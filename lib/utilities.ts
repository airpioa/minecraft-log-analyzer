export const SCANNER_PROMPT = `
You are a Minecraft Mod Compatibility Specialist. Scan the following log specifically for:
1. Mod Conflicts: Identify mods that cannot run together (e.g., Sodium + Optifine).
2. Missing Dependencies: List any mods that are missing their required library mods.
3. Version Mismatches: Check for mods built for a different Minecraft version than the one running.
4. Duplicate Mods: Identify if multiple versions of the same mod are present.

Output only a bulleted list of suspected compatibility issues. If none are found, state "No obvious compatibility issues detected."

This was made by an automated tool that uses AI: https://airpioa.github.io/minecraft-log-analyzer
`;

export function openSearchUrl(text: string, platform: string) {
    const query = text.trim().slice(0, 200);
    const encodedQuery = encodeURIComponent(query);
    let url = "";

    switch (platform) {
        case "forge":
            url = `https://github.com/search?q=org%3Aneoforged+${encodedQuery}&type=code`;
            break;
        case "fabric":
            url = `https://github.com/search?q=repo%3AFabricMC%2Ffabric+OR+repo%3AFabricMC%2Ffabric-loader+${encodedQuery}&type=code`;
            break;
        case "mc":
            url = `https://git.merded.zip/merded/minecraft-src/search?q=${encodedQuery}`;
            break;
        default:
            url = `https://www.google.com/search?q=minecraft+${encodedQuery}`;
    }

    window.open(url, "_blank");
}

export async function uploadToMclogs(content: string): Promise<string | null> {
    try {
        const response = await fetch("https://api.mclo.gs/1/log", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ content })
        });
        const result = await response.json();
        if (result.success) {
            return `https://mclo.gs/${result.id}`;
        }
        return null;
    } catch (error) {
        console.error("mclo.gs upload error:", error);
        return null;
    }
}

export function exportToFile(content: string, filename: string) {
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}
