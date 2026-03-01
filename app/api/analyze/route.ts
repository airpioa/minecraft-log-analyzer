import { NextRequest, NextResponse } from "next/server";

export const SYSTEM_PROMPT = `
You are an expert Minecraft log analyzer. Please analyze the following log and:
1. Identify the core error or reason for the crash/failure.
2. Provide a clear, step-by-step solution.
3. If it's a mod conflict, specify which mods are involved.
4. If it's a version mismatch (e.g., Fabric vs Forge), explain the fix.
Keep your response concise, helpful, and professional.

This was made by an automated tool that uses AI: https://airpioa.github.io/minecraft-log-analyzer
`;

export async function POST(req: NextRequest) {
    try {
        const { logContent, provider, model, apiKey, customPrompt, baseUrl } = await req.json();

        const systemPrompt = customPrompt || SYSTEM_PROMPT;
        const fullPrompt = `${systemPrompt}\n\nLog:\n${logContent}`;

        if (provider === "gemini") {
            const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model || 'gemini-1.5-pro'}:generateContent?key=${apiKey}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    contents: [{ parts: [{ text: fullPrompt }] }]
                })
            });
            const data = await resp.json();
            if (data.error) throw new Error(data.error.message || "Gemini API error");
            return NextResponse.json({ analysis: data.candidates?.[0]?.content?.parts?.[0]?.text });
        }

        if (provider === "openai" || provider === "openai-compatible") {
            const defaultBaseUrl = "https://api.openai.com/v1";
            const apiBaseUrl = baseUrl?.replace(/\/$/, "") || defaultBaseUrl;

            const resp = await fetch(`${apiBaseUrl}/chat/completions`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: model || "gpt-4o",
                    messages: [{ role: "system", content: systemPrompt }, { role: "user", content: logContent }]
                })
            });
            const data = await resp.json();
            if (data.error) throw new Error(data.error.message || `${provider} API error. Check your key and Base URL.`);
            return NextResponse.json({ analysis: data.choices[0].message.content });
        }

        if (provider === "anthropic") {
            const resp = await fetch("https://api.anthropic.com/v1/messages", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "x-api-key": apiKey,
                    "anthropic-version": "2023-06-01"
                },
                body: JSON.stringify({
                    model: model || "claude-3-5-sonnet-20240620",
                    max_tokens: 4096,
                    system: systemPrompt,
                    messages: [{ role: "user", content: logContent }]
                })
            });
            const data = await resp.json();
            if (data.error) throw new Error(data.error.message || "Anthropic API error");
            return NextResponse.json({ analysis: data.content[0].text });
        }

        if (provider === "ollama") {
            const resp = await fetch(`${baseUrl?.replace(/\/$/, "") || "http://localhost:11434"}/api/generate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    model: model || "llama3",
                    system: systemPrompt,
                    prompt: `Log:\n${logContent}`,
                    stream: false
                })
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.error || "Ollama API error");
            return NextResponse.json({ analysis: data.response });
        }

        return NextResponse.json({ error: "Provider not implemented yet" }, { status: 501 });
    } catch (error: any) {
        console.error("API Error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}

export async function GET(req: NextRequest) {
    const { searchParams } = new URL(req.url);
    const provider = searchParams.get("provider");
    const baseUrl = searchParams.get("baseUrl")?.replace(/\/$/, "");
    const apiKey = searchParams.get("apiKey");

    try {
        if (provider === "ollama" && baseUrl) {
            const resp = await fetch(`${baseUrl}/api/tags`);
            const data = await resp.json();
            return NextResponse.json({ models: data.models?.map((m: any) => m.name) || [] });
        }

        if (provider === "openai" || (provider === "openai-compatible" && baseUrl)) {
            const apiBaseUrl = provider === "openai" ? "https://api.openai.com/v1" : baseUrl;
            const headers: any = { "Content-Type": "application/json" };
            if (apiKey) headers["Authorization"] = `Bearer ${apiKey}`;

            const resp = await fetch(`${apiBaseUrl}/models`, { headers });
            const data = await resp.json();
            
            if (data.error) throw new Error(data.error.message || "API Error");
            
            // Filter to only chat models for OpenAI official to reduce noise
            let models = data.data?.map((m: any) => m.id) || [];
            if (provider === "openai") {
                models = models.filter((id: string) => id.startsWith("gpt-") || id.startsWith("o1-") || id.startsWith("o3-"));
            }
            return NextResponse.json({ models });
        }

        if (provider === "gemini" && apiKey) {
            const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`);
            const data = await resp.json();
            if (data.error) throw new Error(data.error.message || "Gemini API error");
            
            // Filter to only generateContent capable models
            const models = data.models
                ?.filter((m: any) => m.supportedGenerationMethods.includes("generateContent"))
                .map((m: any) => m.name.replace("models/", "")) || [];
            return NextResponse.json({ models });
        }

        if (provider === "anthropic") {
            // Anthropic doesn't have a public stable models list API that's easy to use here,
            // so we provide a curated list of current models.
            return NextResponse.json({
                models: [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-5-sonnet-20240620",
                    "claude-3-5-haiku-20241022",
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307"
                ]
            });
        }

        return NextResponse.json({ models: [] });
    } catch (err: any) {
        console.error("GET Models Error:", err);
        return NextResponse.json({ error: err.message }, { status: 500 });
    }
}
