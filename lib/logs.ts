export function getRawUrl(url: string): string {
    url = url.trim().replace(/^<|>$/g, ""); // Remove whitespace and angle brackets
    url = url.replace(/\/$/, ""); // Remove trailing slash

    // Check for mclo.gs
    const mclogsMatch = url.match(/https?:\/\/(?:www\.)?mclo\.gs\/([a-zA-Z0-9]+)/);
    if (mclogsMatch) {
        const logId = mclogsMatch[1];
        return `https://api.mclo.gs/1/raw/${logId}`;
    }

    // Check for gnomebot.dev linking to mclogs
    const gnomebotMclogsMatch = url.match(
        /https?:\/\/(?:www\.)?gnomebot\.dev\/paste\/mclogs\/([a-zA-Z0-9]+)/
    );
    if (gnomebotMclogsMatch) {
        const logId = gnomebotMclogsMatch[1];
        return `https://api.mclo.gs/1/raw/${logId}`;
    }

    // Check for native gnomebot.dev paste
    const gnomebotMatch = url.match(
        /https?:\/\/(?:www\.)?gnomebot\.dev\/(?:raw\/)?([a-zA-Z0-9]+)/
    );
    if (gnomebotMatch) {
        const logId = gnomebotMatch[1];
        return `https://gnomebot.dev/raw/${logId}`;
    }

    const pasteGnomebotMatch = url.match(
        /https?:\/\/(?:www\.)?paste\.gnomebot\.dev\/(?:raw\/)?([a-zA-Z0-9]+)/
    );
    if (pasteGnomebotMatch) {
        const logId = pasteGnomebotMatch[1];
        return `https://paste.gnomebot.dev/raw/${logId}`;
    }

    // Fallback to appending /raw if we don't recognize the host specifically
    if (!url.includes("/raw")) {
        return `${url}/raw`;
    }
    return url;
}

export async function fetchLog(url: string): Promise<string | null> {
    const rawUrl = getRawUrl(url);
    try {
        const response = await fetch(rawUrl);
        if (!response.ok) {
            throw new Error(`Failed to fetch log: ${response.statusText}`);
        }
        return await response.text();
    } catch (error) {
        console.error(`Failed to fetch log from ${url}. Error:`, error);
        return null;
    }
}
