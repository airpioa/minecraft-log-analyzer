"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, LayoutGroup } from "framer-motion";
import {
    Search,
    Terminal,
    Zap,
    AlertCircle,
    Loader2,
    CheckCircle2,
    Copy,
    Plus,
    ArrowRight,
    ChevronDown,
    X,
    FileText,
    Upload,
    Download,
    ShieldCheck,
    SearchCode,
    Globe,
    Github,
    History,
    Info,
    Settings as SettingsIcon
} from "lucide-react";
import { getRawUrl, fetchLog } from "@/lib/logs";
import { openSearchUrl, uploadToMclogs, exportToFile, SCANNER_PROMPT } from "@/lib/utilities";

type Provider = "gemini" | "openai" | "anthropic" | "ollama" | "openai-compatible";
type Mode = "url" | "manual" | "hub";
type Notification = { id: string, message: string, type: 'error' | 'success' };

const SYSTEM_PROMPT = `
You are an expert Minecraft log analyzer. Please analyze the following log and:
1. Identify the core error or reason for the crash/failure.
2. Provide a clear, step-by-step solution.
3. If it's a mod conflict, specify which mods are involved.
4. If it's a version mismatch (e.g., Fabric vs Forge), explain the fix.
Keep your response concise, helpful, and professional.

This was made by an automated tool that uses AI: https://airpioa.github.io/minecraft-log-analyzer
`;

const SELECTION_PROMPT = `
You are an expert Minecraft developer. Please explain the following snippet from a log or code in detail. 
Tell the user what it means, what it is doing, and if it looks like an error, how to fix it.
Keep it technical but easy to understand.

This was made by an automated tool that uses AI: https://airpioa.github.io/minecraft-log-analyzer
`;

const MinecraftLogo = ({ size = 16, className = "" }: { size?: number, className?: string }) => (
    <svg 
        width={size} 
        height={size} 
        viewBox="0 0 24 24" 
        fill="none" 
        stroke="currentColor" 
        strokeWidth="2" 
        strokeLinecap="round" 
        strokeLinejoin="round" 
        className={className}
    >
        <path d="M12 2l-8 4v12l8 4 8-4V6l-8-4z" />
        <path d="M12 22V12" />
        <path d="M20 6l-8 4-8-4" />
        <path d="M4 10l8 4 8-4" />
    </svg>
);

const AnvilLogo = ({ size = 16, className = "" }: { size?: number, className?: string }) => (
    <img 
        src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAKIAAACUCAMAAAAnDwKZAAAAk1BMVEX////b0LQ4NCq8spzGvKWakn6uppTYzbI1MSfJv6cyLiOAem0wLCPT0tGnpqPn5+YtKBytrKm4t7YcFQA9OjBbWFNTUEmUjHoiHArRx6yhn5yIgG+gmIQnIhqXlZNOST1jYFtuaFlWUURFQTl3cWSzqpNlX1Hw8O8fGg/Dw8MQBAAmIRTd3dylopkYFApIRUFqamn03RJoAAAEwklEQVR4nO2ccVuqMBSHr4gJiIIJooChKFDhrfv9P93tiZ2zPbnQcsqs8/4pYm8Htt8Ggz9/COI8qqd7YN+1yydU8+dZw/O0a5dPqNaO0eDfd+3yCaSoAlJUASmqoFrXbkOtmeIeGI9KYIqfVV3rveGtg21DaA6XDcMIPgt0qKcX+tY7Tmb3gGTVfGb5OkShF7JGYomKPjQcbRWjlfaKCSl+jVtVjPRvLskj5IxmiuYQSMtNQ/l3P2Z4OigWNsO0UTayggaru3qKiiawFHpIljP1RAtFW6bIGg4pkiIp3oJiFfosSbbYL9qCIuTM4tqKFWTG+Gm0AdI7wFwCQs6Mr5sz3pyFhpFjkti5xQ6qFfUB3NobuGwX/zr19OYOm7HkOHiwc5hHOwlXxEM+eDTe9zAW8ZUUWcUsmaIlVYSGQ4qkSIo9odPRQ9F33nEzQXHFksRPTIniC9v6cklFIVN2LDXKHYbdMsGcSVKg35ozY+WK3rbprw0n78OQwR72DsHpgCOrZ7oy2ObXSyiy+Mj7ZpsiTvVdqeIjpNAFFa1jijDVl1cRFC9ZxWOKOErUVzEhxV+i2GFzYQNZ92gV4XL8dRQrZB9mjLKPUym8wiS4Rlv4YlIw7swefE1UxN8+S/E+XDN2QqYgNpdFxSXWmMtGJlQez1TDWCNnKU7rZsTg+Pmyd8DQbj3kGIX+CA85nqlv5yrweJ4i/KL7LUXYWaqIrNQoOj9c0SHFmznQGjeX2oJMUdLpiP3iWYo8UyZZlr+TbaSKkpzhgTMIWM+9TQp22axI4EZHEJylOIVMCVMuISlTT5YznD7kX5FkmJ47xDpHcbKAfj+Siclc8ZCL4IwahxZOOQLOVKxhZ1WK0EgsUiRFUuxAkfURyjodmaL/9SFt5THeMiVnmZIKFpJ5iqCItCvmvOsOgfnJitM57MIzZSmTkDrynOkfwgcPwRbyb44lOf12UTyDwg9kDlgbqSKnXRH51iQ1XsDpS4qkSIo/QREyRb1i7XzEP12RZ0oMU40glfzl9nnKUKZYIEm4/kj472TFyStkinBPR1ad9nnKUKKY4P8cV4ecnikPkCl1gssbpFMpoZ6HAwap4shXs2bsARsJVzRVKbKfJkWdFH39FW+gijeg+BsPtDmC2JspUnRHmC4FFkLaieN6giWfQHHZCB/OiRUtZuOKuwGQnlpPrsjZrSCuVC2VVq/owslNiqRIit0p+qoUWaaoe8juoWbLXBVWUfFzgB5GwANcsst5ztzxPy2Z93HFYqM8U2TEMzbVWG0k9SzaFTMXMuWSj3nGrQ3niCIusbzow8ekSIqk+BVFdgf/G4qZA3fwL6k48eHJwpP7xT6vosF2di6p2J4zKc8ZnKf0MVN2T1d+6AZvsPmyevJQxEzx59d+6hRvU7rHFGHZJSmSIinqrHhqp9OZ4hQXdnHFgaDI7qZ0qYg5s48xZ8oBxAy/9FWy86EDRQ4uDnS2EZQzCmCeYmmhiOsuBMWt8RFSJEVS/EzR0l9RqypO4M2PLwbvulHRWsDWbXeKe3x/5nTHEmVTBli7KWx90uK1Z/Bgk4VnohPqIMbxDhuJE3Z3eGWQogpIUQWkqALPeJl94PlVL0XhRc33WmUKcYv8B5NrJtnQX1BIAAAAAElFTkSuQmCC"
        width={size} 
        height={size} 
        className={`${className} object-contain`}
        alt="Forge"
    />
);

const FabricLogo = ({ size = 16, className = "" }: { size?: number, className?: string }) => (
    <img 
        src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDE2IDE2Ij48cGF0aCBmaWxsPSIjMzgzNDJhIiBkPSJNOSAxaDF2MWgxdjFoMXYxaDF2MWgxdjFoMXYyaC0xdjFoLTJ2MWgtMXYxaC0xdjFIOXYyaC04djFIOXYtMUg1di0xSDR2LTFIM3YtMUgyVjlIM3YtMUg0di0xSDV2LTFINnYtMUg3di0xSDh2LTFIOXYtMXoiLz48cGF0aCBmaWxsPSIjZGJkMGI0IiBkPSJNNCA5VjhIMXY3SDFWNmgxbDEtMVY0aDFsLjUxNS0uNDg3TDkgM1YyaDF2MWgxdjFoMXYxaDF2MWgxdjFsLTEuMzYuNjM3TDEwIDEwbC0xLjQ1LjU1TDggMTJsLTEuNjI1LjcwNC0yLjgzMi0zLjA1M1oiLz48cGF0aCBmaWxsPSIjYmNiMjljIiBkPSJNOSAzSDF2MWgxdjFoMXYxaDF2MWgxdjFoLTFMOSA0ek0xMiA3bC0uNTA5LS40NEwxMSA3bC0xIDF2MmgxVjloMXpNMTAgMTBIOUwtLjQ0My0uNTk1TDggMTB2Mmgxdi0xaDF6TTggMTJIM0wtLjQ3Ny41NDZMNyAxM2gxek05IDNoMXYxaDF2MWgxdjFoMXYxaDF2MWgtMUw5IDR6Ii8+PC9zdmc+"
        width={size} 
        height={size} 
        className={`${className} object-contain`}
        alt="Fabric"
    />
);

export default function Home() {
    const [mounted, setMounted] = useState(false);
    const [activeMode, setActiveMode] = useState<Mode>("url");
    const [urls, setUrls] = useState<string>("");
    const [pastedLog, setPastedLog] = useState<string>("");
    const [provider, setProvider] = useState<Provider>("gemini");
    const [apiKey, setApiKey] = useState<string>("");
    const [baseUrl, setBaseUrl] = useState<string>("");
    const [model, setModel] = useState<string>("");
    const [isRunning, setIsRunning] = useState(false);
    const [isScanning, setIsScanning] = useState(false);
    const [results, setResults] = useState<{ title: string, content: string, type: 'analysis' | 'scan' }[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [isPromptCopied, setIsPromptCopied] = useState(false);
    const [availableModels, setAvailableModels] = useState<string[]>([]);
    const [isFetchingModels, setIsFetchingModels] = useState(false);
    const [isManualModel, setIsManualModel] = useState(false);
    const [isCloudModalOpen, setIsCloudModalOpen] = useState(false);

    const resultsEndRef = useRef<HTMLDivElement>(null);
    const pastedLogRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        setMounted(true);
        const savedProvider = localStorage.getItem("mc_provider") as Provider;
        if (savedProvider) setProvider(savedProvider);
    }, []);

    useEffect(() => {
        if (mounted && activeMode === 'url' && !urls.trim()) {
            setIsCloudModalOpen(true);
        }
    }, [activeMode, mounted]);

    const fetchModels = async () => {
        if (!baseUrl && provider === "ollama") return;
        if (!apiKey && (provider === "gemini" || provider === "openai")) return;
        
        setIsFetchingModels(true);
        try {
            // Direct client-side fetch for Ollama
            if (provider === "ollama") {
                const targetUrl = baseUrl?.replace(/\/$/, "") || "http://localhost:11434";
                const resp = await fetch(`${targetUrl}/api/tags`);
                const data = await resp.json();
                const models = data.models?.map((m: any) => m.name) || [];
                setAvailableModels(models);
                if (models.length > 0 && (!model || !models.includes(model))) {
                    setModel(models[0]);
                }
                notify(`Found ${models.length} local models`, "success");
                setIsFetchingModels(false);
                return;
            }

            // Direct client-side for OpenAI
            if (provider === "openai" || (provider === "openai-compatible" && baseUrl)) {
                const apiBaseUrl = provider === "openai" ? "https://api.openai.com/v1" : baseUrl?.replace(/\/$/, "");
                const headers: any = { "Content-Type": "application/json" };
                if (apiKey) headers["Authorization"] = `Bearer ${apiKey}`;

                const resp = await fetch(`${apiBaseUrl}/models`, { headers });
                const data = await resp.json();
                if (data.error) throw new Error(data.error.message || "API Error");
                let models = data.data?.map((m: any) => m.id) || [];
                if (provider === "openai") {
                    models = models.filter((id: string) => id.startsWith("gpt-") || id.startsWith("o1-") || id.startsWith("o3-"));
                }
                setAvailableModels(models);
                if (models.length > 0 && (!model || !models.includes(model))) setModel(models[0]);
                notify(`Found ${models.length} models`, "success");
                setIsFetchingModels(false);
                return;
            }

            // Direct client-side for Gemini
            if (provider === "gemini" && apiKey) {
                const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`);
                const data = await resp.json();
                if (data.error) throw new Error(data.error.message || "Gemini API error");
                const models = data.models
                    ?.filter((m: any) => m.supportedGenerationMethods.includes("generateContent"))
                    .map((m: any) => m.name.replace("models/", "")) || [];
                setAvailableModels(models);
                if (models.length > 0 && (!model || !models.includes(model))) setModel(models[0]);
                notify(`Found ${models.length} models`, "success");
                setIsFetchingModels(false);
                return;
            }

            // Anthropic curated list
            if (provider === "anthropic") {
                const models = [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-5-sonnet-20240620",
                    "claude-3-5-haiku-20241022",
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307"
                ];
                setAvailableModels(models);
                if (!model || !models.includes(model)) setModel(models[0]);
                setIsFetchingModels(false);
                return;
            }
        } catch (err: any) {
            notify(err.message || "Failed to fetch models");
        } finally {
            setIsFetchingModels(false);
        }
    };

    const callAiClient = async (content: string, customPrompt?: string, taskType?: 'analysis' | 'scan') => {
        const systemPrompt = customPrompt || (taskType === 'scan' ? SCANNER_PROMPT : SYSTEM_PROMPT);
        const fullPrompt = `${systemPrompt}\n\nLog:\n${content}`;

        if (provider === "ollama") {
            const targetUrl = baseUrl?.replace(/\/$/, "") || "http://localhost:11434";
            const resp = await fetch(`${targetUrl}/api/generate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    model: model || "llama3",
                    system: systemPrompt,
                    prompt: content,
                    stream: false
                })
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.error || "Ollama error");
            return data.response;
        }

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
            return data.candidates?.[0]?.content?.parts?.[0]?.text;
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
                    messages: [{ role: "system", content: systemPrompt }, { role: "user", content: content }]
                })
            });
            const data = await resp.json();
            if (data.error) throw new Error(data.error.message || `${provider} API error. Check your key and Base URL.`);
            return data.choices[0].message.content;
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
                    messages: [{ role: "user", content: content }]
                })
            });
            const data = await resp.json();
            if (data.error) throw new Error(data.error.message || "Anthropic API error");
            return data.content[0].text;
        }

        throw new Error("Provider not supported client-side");
    };

    useEffect(() => {
        if (!mounted) return;
        const savedKey = localStorage.getItem(`${provider}_api_key`);
        setApiKey(savedKey || "");

        const savedUrl = localStorage.getItem(`${provider}_base_url`);
        const defaultUrl = provider === "ollama" ? "http://localhost:11434" : "";
        const currentBaseUrl = savedUrl || defaultUrl;
        setBaseUrl(currentBaseUrl);

        const savedModel = localStorage.getItem(`${provider}_model`);
        const defaultModel = provider === "gemini" ? "gemini-1.5-pro" :
            provider === "openai" ? "gpt-4o" :
                provider === "anthropic" ? "claude-3-5-sonnet-20240620" :
                    provider === "ollama" ? "llama3" : "";
        setModel(savedModel || defaultModel);

        localStorage.setItem("mc_provider", provider);

        setAvailableModels([]);
        setIsManualModel(false);
        // Small delay to allow state to settle
        setTimeout(() => {
            fetchModels();
        }, 100);
    }, [provider, mounted]);

    useEffect(() => {
        if (mounted) {
             const timer = setTimeout(() => {
                 fetchModels();
             }, 1000);
             return () => clearTimeout(timer);
        }
    }, [baseUrl, apiKey]);

    const notify = (message: string, type: 'error' | 'success' = 'error') => {
        const id = Math.random().toString(36).substring(2, 9);
        setNotifications(prev => [...prev, { id, message, type }]);
        setTimeout(() => {
            setNotifications(prev => prev.filter(n => n.id !== id));
        }, 5000);
    };

    const handleRunTask = async (taskType: 'analysis' | 'scan') => {
        setIsRunning(true);
        if (taskType === 'scan') setIsScanning(true);
        setError(null);

        try {
            const logsToAnalyze: { title: string, content: string }[] = [];

            if (activeMode === "manual") {
                if (!pastedLog.trim()) throw new Error("Please paste a log first");
                logsToAnalyze.push({ title: "Pasted Log", content: pastedLog });
            } else {
                const urlList = urls.split("\n").filter(u => u.trim());
                if (urlList.length === 0) throw new Error("Please enter at least one URL");

                for (const url of urlList) {
                    const content = await fetchLog(url);
                    if (content) {
                        logsToAnalyze.push({ title: url, content });
                    } else {
                        notify(`Failed to fetch log from ${url}`);
                    }
                }
            }

            if (logsToAnalyze.length === 0) return;

            for (const log of logsToAnalyze) {
                const analysis = await callAiClient(log.content, undefined, taskType);
                setResults(prev => [{ title: log.title, content: analysis, type: taskType }, ...prev]);

                localStorage.setItem(`${provider}_api_key`, apiKey);
                localStorage.setItem(`${provider}_base_url`, baseUrl);
                localStorage.setItem(`${provider}_model`, model);
            }
        } catch (err: any) {
            notify(err.message, 'error');
        } finally {
            setIsRunning(false);
            setIsScanning(false);
        }
    };

    const handleManualUrlPrompt = async (taskType: 'analysis' | 'scan') => {
        const urlList = urls.split("\n").filter(u => u.trim());
        if (urlList.length === 0) {
            notify("Please enter URLs first", "error");
            return;
        }
        const systemPrompt = taskType === 'scan' ? SCANNER_PROMPT : SYSTEM_PROMPT;
        const prompt = `${systemPrompt}\n\nLog URLs:\n${urlList.join("\n")}`;

        await navigator.clipboard.writeText(prompt);
        setIsPromptCopied(true);
        notify(`${taskType === 'scan' ? 'Compatibility' : 'Analysis'} prompt copied!`, "success");
        setTimeout(() => setIsPromptCopied(false), 2000);

        setResults([{ 
            title: taskType === 'scan' ? "Scan Instruction Generated" : "Analysis Instruction Generated", 
            content: `The ${taskType === 'scan' ? 'compatibility scan' : 'analysis'} prompt has been copied. Use it in your AI chat with the provided logs.`, 
            type: taskType 
        }, ...results]);
    };

    const handleCopyPastePrompt = async (taskType: 'analysis' | 'scan') => {
        if (!pastedLog.trim()) {
            notify("Please paste a log first");
            return;
        }
        const systemPrompt = taskType === 'scan' ? SCANNER_PROMPT : SYSTEM_PROMPT;
        const prompt = `${systemPrompt}\n\nLog Content:\n${pastedLog}`;
        await navigator.clipboard.writeText(prompt);
        notify(`${taskType === 'scan' ? 'Compatibility' : 'Analysis'} prompt copied!`, "success");
        
        setResults([{ title: "Log Prompt Copied", content: `A ${taskType === 'scan' ? 'compatibility scan' : 'deep analysis'} prompt including your pasted log has been copied to your clipboard.`, type: taskType === 'scan' ? 'scan' : 'analysis' }, ...results]);
    };

    const handleSelectionSearch = (p: string) => {
        const textarea = pastedLogRef.current;
        if (!textarea) return;
        const selection = textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);
        if (!selection || !selection.trim()) {
            notify("Please select some text first", "error");
            return;
        }
        openSearchUrl(selection.trim(), p);
    };

    const handleSelectionAI = async () => {
        const textarea = pastedLogRef.current;
        if (!textarea) return;
        const selection = textarea.value.substring(textarea.selectionStart, textarea.selectionEnd).trim();
        if (!selection) {
            notify("Please select some text first", "error");
            return;
        }

        setIsRunning(true);
        try {
            const analysis = await callAiClient(selection, SELECTION_PROMPT);
            setResults(prev => [{ title: `Selection: ${selection.substring(0, 30)}...`, content: analysis, type: 'analysis' }, ...prev]);
            notify("Selection analyzed!", "success");
        } catch (err: any) {
            notify(err.message, 'error');
        } finally {
            setIsRunning(false);
        }
    };

    const handleImportUrls = async () => {
        const urlList = urls.split("\n").filter(u => u.trim());
        if (urlList.length === 0) {
            notify("Please enter URLs in the 'Cloud Logs' tab or enter them here.", "error");
            return;
        }

        setIsRunning(true);
        let importedContent = pastedLog ? pastedLog + "\n\n" : "";
        let successCount = 0;

        try {
            for (const url of urlList) {
                const content = await fetchLog(url);
                if (content) {
                    importedContent += `--- LOG FROM ${url} ---\n${content}\n\n`;
                    successCount++;
                } else {
                    notify(`Failed to fetch log from ${url}`, "error");
                }
            }
            setPastedLog(importedContent);
            if (successCount > 0) notify(`Imported ${successCount} logs!`, "success");
        } catch (err: any) {
            notify(err.message, "error");
        } finally {
            setIsRunning(false);
        }
    };

    if (!mounted) return null;

    return (
        <div className="min-h-screen bg-[#020617] text-slate-50 font-sans selection:bg-indigo-500/30">
            <LayoutGroup>
                {/* Settings Sidebar */}
                <AnimatePresence>
                    {sidebarOpen && (
                        <>
                            <motion.div
                                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                onClick={() => setSidebarOpen(false)}
                                className="fixed inset-0 bg-black/80 backdrop-blur-md z-40"
                            />
                            <motion.aside
                                initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }}
                                transition={{ type: "spring", damping: 25, stiffness: 120 }}
                                className="fixed right-0 top-0 bottom-0 w-80 glass z-50 p-8 flex flex-col gap-8 shadow-2xl border-l border-white/10"
                            >
                                <div className="flex items-center justify-between">
                                    <h2 className="text-xl font-bold font-outfit flex items-center gap-2">
                                        <SettingsIcon size={22} className="text-indigo-400" />
                                        AI Config
                                    </h2>
                                    <button onClick={() => setSidebarOpen(false)} className="p-2 hover:bg-white/5 rounded-full transition-colors"><X size={20} /></button>
                                </div>

                                <div className="flex flex-col gap-6">
                                    <div className="flex flex-col gap-3">
                                        <label className="text-xs font-black text-slate-500 uppercase tracking-widest">Model Provider</label>
                                        <select
                                            value={provider}
                                            onChange={(e) => setProvider(e.target.value as Provider)}
                                            className="bg-slate-900 border border-white/10 rounded-2xl p-4 text-sm outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all appearance-none"
                                        >
                                            <option value="gemini">Google Gemini</option>
                                            <option value="openai">OpenAI (Official)</option>
                                            <option value="anthropic">Anthropic Claude</option>
                                            <option value="ollama">Ollama (Local)</option>
                                            <option value="openai-compatible">OpenAI Compatible (Groq, Together, etc)</option>
                                        </select>
                                    </div>

                                    <div className="flex flex-col gap-4">
                                        {provider !== "ollama" && (
                                            <div className="flex flex-col gap-3">
                                                <label className="text-xs font-black text-slate-500 uppercase tracking-widest">API Secret Key</label>
                                                <input
                                                    type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
                                                    placeholder="Paste key here..."
                                                    className="w-full bg-slate-900 border border-white/10 rounded-2xl p-4 text-sm outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all font-mono"
                                                />
                                            </div>
                                        )}

                                        {(provider === "ollama" || provider === "openai-compatible") && (
                                            <div className="flex flex-col gap-3">
                                                <label className="text-xs font-black text-slate-500 uppercase tracking-widest">Base API URL</label>
                                                <input
                                                    type="text" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)}
                                                    placeholder={provider === "ollama" ? "http://localhost:11434" : "https://api.groq.com/openai/v1"}
                                                    className="bg-slate-900 border border-white/10 rounded-2xl p-4 text-sm outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all font-mono"
                                                />
                                            </div>
                                        )}

                                        <div className="flex flex-col gap-3">
                                            <div className="flex items-center justify-between">
                                                <label className="text-xs font-black text-slate-500 uppercase tracking-widest">Model Identifier</label>
                                                <button
                                                    onClick={fetchModels} disabled={isFetchingModels}
                                                    className="text-[10px] font-black text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1 uppercase tracking-tighter"
                                                >
                                                    {isFetchingModels ? <Loader2 size={10} className="animate-spin" /> : <Plus size={10} />}
                                                    Refresh List
                                                </button>
                                            </div>
                                            <div className="relative group/model">
                                                {availableModels.length > 0 && !isManualModel ? (
                                                    <div className="relative flex items-center">
                                                        <select
                                                            value={model}
                                                            onChange={(e) => {
                                                                if (e.target.value === "manual") {
                                                                    setIsManualModel(true);
                                                                    setModel("");
                                                                } else {
                                                                    setModel(e.target.value);
                                                                }
                                                            }}
                                                            className="w-full bg-slate-900 border border-white/10 rounded-2xl p-4 pr-10 text-sm outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all font-mono appearance-none cursor-pointer"
                                                        >
                                                            {availableModels.map(m => <option key={m} value={m}>{m}</option>)}
                                                            <option value="manual" className="text-indigo-400 font-bold italic">+ Manual Entry...</option>
                                                        </select>
                                                        <ChevronDown className="absolute right-4 pointer-events-none text-slate-500" size={16} />
                                                    </div>
                                                ) : (
                                                    <div className="relative">
                                                        <input
                                                            type="text" value={model} onChange={(e) => setModel(e.target.value)}
                                                            placeholder="e.g. gpt-4o, llama3..."
                                                            className="w-full bg-slate-900 border border-white/10 rounded-2xl p-4 text-sm outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all font-mono"
                                                        />
                                                        {availableModels.length > 0 && (
                                                            <button 
                                                                onClick={() => setIsManualModel(false)}
                                                                className="absolute right-4 top-1/2 -translate-y-1/2 p-1.5 bg-indigo-500/10 rounded-lg text-indigo-400 hover:bg-indigo-500/20 transition-all"
                                                                title="Switch back to list"
                                                            >
                                                                <Search size={14} />
                                                            </button>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </motion.aside>
                        </>
                    )}
                </AnimatePresence>

                <main className="max-w-7xl mx-auto p-6 md:p-12">
                    {/* Header */}
                    <header className="flex flex-col md:flex-row items-center justify-between gap-6 mb-16">
                        <div className="flex items-center gap-5">
                            <div className="w-14 h-14 bg-gradient-to-tr from-indigo-600 to-purple-600 rounded-[1.25rem] flex items-center justify-center shadow-2xl shadow-indigo-500/40 border border-white/20">
                                <Terminal className="text-white" size={28} />
                            </div>
                            <div className="text-center md:text-left">
                                <h1 className="text-3xl font-black font-outfit tracking-tighter text-white">
                                    ANALYZER<span className="text-indigo-500">.PRO</span>
                                </h1>
                                <p className="text-xs font-bold text-slate-500 uppercase tracking-[0.3em]">AI Crash Diagnostics</p>
                            </div>
                        </div>

                        <nav className="flex items-center gap-2 bg-slate-900/50 p-2 rounded-2xl border border-white/5">
                            {[
                                { id: 'url', label: 'Cloud Logs', icon: Globe },
                                { id: 'manual', label: 'Manual Prompting', icon: FileText },
                                { id: 'hub', label: 'Comp. Hub', icon: ShieldCheck }
                            ].map((mode) => (
                                <button
                                    key={mode.id}
                                    onClick={() => setActiveMode(mode.id as Mode)}
                                    className={`px-6 py-2.5 rounded-xl text-xs font-black flex items-center gap-2 transition-all ${activeMode === mode.id
                                        ? 'bg-indigo-600 text-white shadow-lg'
                                        : 'text-slate-500 hover:text-slate-300'
                                        }`}
                                >
                                    <mode.icon size={14} />
                                    {mode.label}
                                </button>
                            ))}
                        </nav>

                        <button
                            onClick={() => setSidebarOpen(true)}
                            className="p-3 bg-white/5 border border-white/10 rounded-2xl hover:bg-white/10 transition-all flex items-center gap-2"
                        >
                            <SettingsIcon size={20} className="text-slate-400" />
                            <span className="text-xs font-bold text-slate-300">Settings</span>
                        </button>
                    </header>

                    <div className="grid grid-cols-1 xl:grid-cols-12 gap-12">
                        {/* Input Section */}
                        <div className="xl:col-span-5 flex flex-col gap-8">
                            <section className="glass rounded-[2.5rem] p-10 flex flex-col gap-8 border border-white/10 relative shadow-2xl overflow-hidden">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-lg font-bold font-outfit flex items-center gap-3">
                                        <div className="p-2 bg-indigo-500/10 rounded-lg"><Upload size={18} className="text-indigo-400" /></div>
                                        Input Buffer
                                    </h3>
                                    <div className="flex gap-2">
                                        <button onClick={() => exportToFile(pastedLog, "log.txt")} className="p-2 bg-white/5 rounded-xl hover:text-indigo-400 transition-colors"><Download size={16} /></button>
                                    </div>
                                </div>

                                <div className="min-h-[350px] flex flex-col">
                                    <AnimatePresence mode="wait">
                                        {activeMode === 'url' ? (
                                            urls.trim() ? (
                                                <motion.textarea
                                                    key="url" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                                    value={urls} onChange={(e) => setUrls(e.target.value)}
                                                    placeholder="https://mclo.gs/XXXXX..."
                                                    className="flex-1 bg-black/40 border border-white/5 rounded-[2rem] p-8 text-slate-200 outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all font-mono text-sm leading-relaxed resize-none scrollbar-hide"
                                                />
                                            ) : (
                                                <motion.div
                                                    key="url-empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                                    className="flex-1 flex flex-col items-center justify-center text-center gap-6 border-2 border-dashed border-white/5 rounded-[3rem] p-12 bg-slate-900/40 hover:bg-slate-900/60 transition-all group cursor-pointer"
                                                    onClick={() => setIsCloudModalOpen(true)}
                                                >
                                                    <div className="w-20 h-20 bg-indigo-500/10 rounded-[2rem] flex items-center justify-center border border-indigo-500/20 group-hover:rotate-6 transition-transform">
                                                        <Globe className="text-indigo-400" size={32} />
                                                    </div>
                                                    <div className="space-y-3">
                                                        <h3 className="text-xl font-bold font-outfit uppercase tracking-tighter">Cloud Log Buffer Empty</h3>
                                                        <p className="text-xs text-slate-500 max-w-xs mx-auto leading-relaxed font-medium italic">
                                                            "Enter your mclo.gs or other raw log URLs to start the analysis process."
                                                        </p>
                                                    </div>
                                                    <button className="px-10 py-4 bg-indigo-600 rounded-2xl text-[10px] font-black shadow-xl shadow-indigo-600/20 flex items-center gap-3 active:scale-95 transition-all">
                                                        <Plus size={16} />
                                                        ADD LOG URLS
                                                    </button>
                                                </motion.div>
                                            )
                                        ) : activeMode === 'manual' ? (
                                            <motion.div
                                                key="manual" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                                className="flex-1 flex flex-col gap-4"
                                            >
                                                <div className="flex-1 relative group">
                                                    <textarea
                                                        ref={pastedLogRef}
                                                        value={pastedLog} onChange={(e) => setPastedLog(e.target.value)}
                                                        placeholder="Paste raw log content OR import from URLs..."
                                                        className="w-full h-full bg-black/40 border border-white/5 rounded-[2rem] p-8 text-slate-200 outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all font-mono text-sm leading-relaxed resize-none scrollbar-hide"
                                                    />
                                                    <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-900/90 p-2 rounded-2xl border border-white/10 shadow-2xl backdrop-blur-md">
                                                        <button 
                                                            onClick={handleSelectionAI}
                                                            disabled={isRunning}
                                                            className="px-3 py-2 bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-400 rounded-xl text-[10px] font-black flex items-center gap-2 transition-all border border-indigo-500/20 disabled:opacity-50"
                                                            title="Explain with AI"
                                                        >
                                                            {isRunning ? <Loader2 size={12} className="animate-spin" /> : <Zap size={12} fill="currentColor" />}
                                                            AI EXPLAIN
                                                        </button>
                                                        <div className="w-px h-6 bg-white/5 mx-1" />
                                                        <span className="text-[10px] font-black text-slate-500 flex items-center px-1 uppercase tracking-tighter">Search:</span>
                                                        {[
                                                            { l: 'Forge', p: 'forge', i: AnvilLogo },
                                                            { l: 'Fabric', p: 'fabric', i: FabricLogo },
                                                            { l: 'Src', p: 'mc', i: MinecraftLogo },
                                                            { l: 'Global', p: 'google', i: Search }
                                                        ].map(t => (
                                                            <button 
                                                                key={t.p} 
                                                                onClick={() => handleSelectionSearch(t.p)}
                                                                className="p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-indigo-400 transition-all flex items-center gap-2"
                                                                title={`Search ${t.l} for selection`}
                                                            >
                                                                <t.i size={14} />
                                                            </button>
                                                        ))}
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-4 bg-white/5 p-4 rounded-3xl border border-white/5">
                                                    <div className="p-3 bg-indigo-500/10 rounded-2xl"><Globe size={18} className="text-indigo-400" /></div>
                                                    <div className="flex-1">
                                                        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Cloud Sources</p>
                                                        <p className="text-[11px] text-slate-400">Fetch logs from URLs and append them here.</p>
                                                    </div>
                                                    <div className="flex gap-2">
                                                        <button 
                                                            onClick={handleImportUrls}
                                                            disabled={isRunning}
                                                            className="px-4 py-3 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-400 rounded-xl text-[10px] font-black transition-all flex items-center gap-2"
                                                        >
                                                            {isRunning ? <Loader2 size={12} className="animate-spin" /> : <Plus size={12} />}
                                                            FETCH
                                                        </button>
                                                        <button 
                                                            onClick={() => setIsCloudModalOpen(true)}
                                                            className="px-4 py-3 bg-white/5 hover:bg-white/10 text-slate-400 rounded-xl text-[10px] font-black transition-all border border-white/5"
                                                        >
                                                            EDIT URLs
                                                        </button>
                                                    </div>
                                                </div>
                                            </motion.div>
                                        ) : activeMode === 'hub' ? (
                                            <motion.div
                                                key="hub" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                                className="flex-1 flex flex-col gap-6"
                                            >
                                                <div className="flex flex-col gap-4">
                                                    <p className="text-[11px] text-slate-400 font-medium leading-relaxed px-2">
                                                        Quick search tools for identifying mod conflicts, missing libraries, or version mismatches.
                                                    </p>
                                                    <div className="grid grid-cols-2 gap-3">
                                                        {[
                                                            { l: 'Forge/Neo', p: 'forge', i: AnvilLogo },
                                                            { l: 'Fabric/Quilt', p: 'fabric', i: FabricLogo },
                                                            { l: 'MC Src', p: 'mc', i: MinecraftLogo },
                                                            { l: 'Global', p: 'google', i: Search }
                                                        ].map(t => (
                                                            <button key={t.p} onClick={() => openSearchUrl(searchTerm, t.p)} className="p-4 bg-white/5 rounded-2xl hover:bg-white/10 border border-white/5 transition-all flex items-center gap-3 text-xs font-bold text-slate-300 group">
                                                                <t.i size={14} className="group-hover:text-indigo-400 transition-colors" />
                                                                {t.l}
                                                            </button>
                                                        ))}
                                                    </div>
                                                    <div className="relative">
                                                        <input
                                                            type="text" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                                                            placeholder="Search class or error..."
                                                            className="w-full bg-black/40 border border-white/10 rounded-2xl p-4 pl-12 text-sm outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all placeholder:text-slate-700"
                                                        />
                                                        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-600" />
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-4 bg-emerald-500/5 p-4 rounded-3xl border border-emerald-500/10">
                                                    <div className="p-3 bg-emerald-500/10 rounded-2xl"><ShieldCheck size={18} className="text-emerald-400" /></div>
                                                    <div className="flex-1">
                                                        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Scan Source</p>
                                                        <p className="text-[11px] text-slate-400">Log URLs used for compatibility scanning.</p>
                                                    </div>
                                                    <button 
                                                        onClick={() => setIsCloudModalOpen(true)}
                                                        className="px-6 py-3 bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-400 rounded-xl text-[10px] font-black transition-all border border-emerald-500/20"
                                                    >
                                                        EDIT URLs
                                                    </button>
                                                </div>
                                            </motion.div>
                                        ) : null}
                                    </AnimatePresence>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {activeMode === 'url' && (
                                        <button
                                            onClick={() => handleRunTask('analysis')}
                                            disabled={isRunning}
                                            className="col-span-2 group py-5 bg-gradient-to-r from-indigo-600 to-indigo-700 rounded-3xl font-black text-xs flex items-center justify-center gap-3 shadow-2xl shadow-indigo-600/30 hover:scale-[1.02] transition-all disabled:opacity-50"
                                        >
                                            {isRunning && !isScanning ? <Loader2 className="animate-spin" size={20} /> : <Zap size={18} fill="currentColor" />}
                                            FULL ANALYSIS (API)
                                        </button>
                                    )}

                                    {activeMode === 'manual' && (
                                        <>
                                            <div className="col-span-2 grid grid-cols-2 gap-4">
                                                <button
                                                    onClick={() => handleCopyPastePrompt('analysis')}
                                                    className="group py-5 bg-indigo-600 rounded-3xl font-black text-[10px] flex items-center justify-center gap-3 shadow-2xl shadow-indigo-600/20 hover:scale-[1.02] transition-all"
                                                >
                                                    <Copy size={18} className="text-indigo-200" />
                                                    COPY ANALYSIS (RAW TEXT)
                                                </button>
                                                <button
                                                    onClick={() => handleManualUrlPrompt('analysis')}
                                                    className="py-5 bg-slate-900 border border-white/10 rounded-3xl font-black text-[10px] flex items-center justify-center gap-3 hover:bg-slate-800 transition-all"
                                                >
                                                    <Globe size={18} className="text-indigo-400" />
                                                    COPY ANALYSIS (URLs)
                                                </button>
                                            </div>
                                            <div className="col-span-2 grid grid-cols-2 gap-4">
                                                <button
                                                    onClick={() => handleCopyPastePrompt('scan')}
                                                    className="py-5 bg-slate-900 border border-white/10 rounded-3xl font-black text-[10px] flex items-center justify-center gap-3 hover:bg-slate-800 transition-all"
                                                >
                                                    <ShieldCheck size={18} className="text-emerald-500" />
                                                    COPY SCAN (RAW TEXT)
                                                </button>
                                                <button
                                                    onClick={() => handleManualUrlPrompt('scan')}
                                                    className="py-5 bg-slate-900 border border-white/10 rounded-3xl font-black text-[10px] flex items-center justify-center gap-3 hover:bg-slate-800 transition-all"
                                                >
                                                    <Globe size={18} className="text-emerald-500" />
                                                    COPY SCAN (URLs)
                                                </button>
                                            </div>
                                        </>
                                    )}

                                    {activeMode === 'hub' && (
                                        <>
                                            <button
                                                onClick={() => handleRunTask('scan')}
                                                disabled={isRunning}
                                                className="col-span-2 group py-5 bg-gradient-to-r from-emerald-600 to-emerald-700 rounded-3xl font-black text-xs flex items-center justify-center gap-3 hover:scale-[1.02] transition-all disabled:opacity-50 shadow-2xl shadow-emerald-600/20"
                                            >
                                                {isScanning ? <Loader2 className="animate-spin" size={20} /> : <ShieldCheck size={18} fill="currentColor" />}
                                                RUN SCAN (API)
                                            </button>
                                            <button
                                                onClick={() => handleCopyPastePrompt('scan')}
                                                className="py-5 bg-slate-900 border border-white/10 rounded-3xl font-black text-[10px] flex items-center justify-center gap-3 hover:bg-slate-800 transition-all"
                                            >
                                                <ShieldCheck size={18} className="text-emerald-500" />
                                                COPY SCAN (RAW TEXT)
                                            </button>
                                            <button
                                                onClick={() => handleManualUrlPrompt('scan')}
                                                className="py-5 bg-slate-900 border border-white/10 rounded-3xl font-black text-[10px] flex items-center justify-center gap-3 hover:bg-slate-800 transition-all"
                                            >
                                                <Globe size={18} className="text-emerald-500" />
                                                COPY SCAN (URLs)
                                            </button>
                                        </>
                                    )}
                                </div>
                            </section>

                            <div className="p-8 rounded-[2rem] bg-indigo-500/5 border border-indigo-500/10 flex flex-col gap-4">
                                <h4 className="text-[10px] font-black text-indigo-400 uppercase tracking-widest flex items-center gap-2">
                                    <Zap size={14} className="fill-current" />
                                    Pro Tips
                                </h4>
                                <ul className="flex flex-col gap-3">
                                    {[
                                        "Paste multiple URLs to analyze them sequentially.",
                                        "Settings are saved locally to your browser.",
                                        "Use the Search Tools in Comp. Hub for rapid debugging."
                                    ].map((tip, i) => (
                                        <li key={i} className="text-[11px] text-slate-400 flex items-start gap-3">
                                            <div className="w-1 h-1 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                                            {tip}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>

                        {/* Results Section */}
                        <div className="xl:col-span-7 flex flex-col gap-8 h-full">

                            <div className="flex-1 glass rounded-[3rem] border border-white/10 flex flex-col overflow-hidden shadow-2xl relative">
                                <header className="px-10 py-8 border-b border-white/5 bg-white/2 flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="p-3 bg-indigo-500/10 rounded-2xl"><History size={20} className="text-indigo-400" /></div>
                                        <h2 className="text-xl font-bold font-outfit">Feed Output</h2>
                                    </div>
                                    {isRunning && (
                                        <div className="flex items-center gap-3">
                                            <div className="flex gap-1 h-3 items-center">
                                                {[0, 1, 2].map(i => <motion.div key={i} animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1, delay: i * 0.2 }} className="w-1.5 h-1.5 rounded-full bg-indigo-500" />)}
                                            </div>
                                            <span className="text-[10px] font-black uppercase tracking-widest text-indigo-400">Processing...</span>
                                        </div>
                                    )}
                                </header>

                                <div className="flex-1 overflow-y-auto p-10 custom-scrollbar space-y-10">
                                    <AnimatePresence mode="popLayout">
                                        {results.length === 0 && !isRunning && (
                                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center justify-center pt-24 text-center opacity-30">
                                                <Terminal size={64} className="mb-6" />
                                                <p className="text-sm font-bold uppercase tracking-widest">Awaiting Diagnostic Data</p>
                                            </motion.div>
                                        )}

                                        {results.map((res, i) => (
                                            <motion.article
                                                key={i}
                                                initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }}
                                                className="flex flex-col gap-4"
                                            >
                                                <div className="flex items-center gap-4">
                                                    <div className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest border ${res.type === 'scan' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400'
                                                        }`}>
                                                        {res.type === 'scan' ? 'Compatibility Scan' : 'Deep Analysis'}
                                                    </div>
                                                    <div className="h-px flex-1 bg-white/5" />
                                                    <span className="text-[10px] font-bold text-slate-600 truncate max-w-[200px]">{res.title}</span>
                                                </div>

                                                <div className="p-8 rounded-[2.5rem] bg-slate-900/40 border border-white/5 group relative hover:border-white/10 transition-colors">
                                                    <button onClick={() => navigator.clipboard.writeText(res.content)} className="absolute top-6 right-6 p-3 bg-black/20 rounded-xl text-slate-500 hover:text-white transition-all opacity-0 group-hover:opacity-100">
                                                        <Copy size={16} />
                                                    </button>
                                                    <div className="prose prose-invert max-w-none prose-indigo text-slate-300 leading-relaxed font-sans prose-sm whitespace-pre-wrap">
                                                        {res.content}
                                                    </div>
                                                </div>
                                            </motion.article>
                                        ))}
                                    </AnimatePresence>
                                    <div ref={resultsEndRef} />
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            </LayoutGroup>

            {/* Cloud Logs Modal */}
            <AnimatePresence>
                {isCloudModalOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            onClick={() => setIsCloudModalOpen(false)}
                            className="fixed inset-0 bg-black/90 backdrop-blur-sm z-[100]"
                        />
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-xl glass z-[101] p-10 rounded-[3rem] border border-white/10 shadow-2xl flex flex-col gap-8"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="p-3 bg-indigo-500/10 rounded-2xl"><Globe size={24} className="text-indigo-400" /></div>
                                    <div>
                                        <h2 className="text-xl font-bold font-outfit uppercase tracking-tighter">Add Cloud Logs</h2>
                                        <p className="text-xs text-slate-500 font-medium">Enter one URL per line</p>
                                    </div>
                                </div>
                                <button onClick={() => setIsCloudModalOpen(false)} className="p-2 hover:bg-white/5 rounded-full transition-colors"><X size={24} /></button>
                            </div>

                            <textarea
                                autoFocus
                                value={urls}
                                onChange={(e) => setUrls(e.target.value)}
                                placeholder="https://mclo.gs/XXXXX..."
                                className="h-64 bg-black/40 border border-white/5 rounded-[2rem] p-8 text-slate-200 outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all font-mono text-sm leading-relaxed resize-none scrollbar-hide"
                            />

                            <div className="flex gap-4">
                                <button 
                                    onClick={() => setIsCloudModalOpen(false)}
                                    className="flex-1 py-4 bg-indigo-600 rounded-2xl text-[10px] font-black shadow-xl shadow-indigo-600/20 active:scale-95 transition-all"
                                >
                                    SAVE & CLOSE
                                </button>
                                <button 
                                    onClick={() => setUrls("")}
                                    className="px-8 py-4 bg-white/5 rounded-2xl text-[10px] font-black hover:bg-white/10 transition-all border border-white/5"
                                >
                                    CLEAR
                                </button>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            {/* Notifications */}
            <div className="fixed bottom-8 right-8 z-[100] flex flex-col gap-4 max-w-md w-full pointer-events-none">
                <AnimatePresence>
                    {notifications.map((n) => (
                        <motion.div
                            key={n.id}
                            initial={{ opacity: 0, x: 50, scale: 0.9 }}
                            animate={{ opacity: 1, x: 0, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
                            className={`pointer-events-auto p-5 rounded-[2rem] border shadow-2xl backdrop-blur-xl flex items-center gap-4 ${n.type === 'error'
                                ? 'bg-red-500/10 border-red-500/20 text-red-400'
                                : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                                }`}
                        >
                            {n.type === 'error' ? <AlertCircle size={20} className="shrink-0" /> : <CheckCircle2 size={20} className="shrink-0" />}
                            <p className="text-xs font-bold leading-relaxed flex-1">{n.message}</p>
                            <button onClick={() => setNotifications(prev => prev.filter(nn => nn.id !== n.id))} className="p-2 hover:bg-white/5 rounded-xl transition-colors">
                                <X size={16} />
                            </button>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>

            <style jsx global>{`
                .glass {
                    background: rgba(15, 23, 42, 0.7);
                    backdrop-filter: blur(24px);
                    -webkit-backdrop-filter: blur(24px);
                }
                .custom-scrollbar::-webkit-scrollbar {
                    width: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 20px;
                }
                .scrollbar-hide::-webkit-scrollbar {
                    display: none;
                }
            `}</style>
        </div>
    );
}
