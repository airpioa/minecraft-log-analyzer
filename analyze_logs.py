import argparse
import os
import sys
import re
import requests
from typing import Tuple, Optional
from google import genai

SYSTEM_PROMPT = """You are a Minecraft server log analysis expert. Your job is to analyze server logs, identify the core issues causing crashes or errors, and present a clear, structured solution.

CRITICAL: You MUST format your response EXACTLY like the example below. Do NOT deviate from this format. Use numbered headings for the issues, provide a brief description, and use a "Recommended Steps:" section with indented bullet points.

EXAMPLE FORMAT:
1. [Issue Name Here]

[Brief description of the issue here]

Recommended Steps:
    [Step 1 here]
    [Step 2 here]
    
2. [Second Issue Name Here]

[Brief description of the second issue here]

Recommended Steps:
    [Step 1 here]
    [Step 2 here]
"""

def get_raw_url(url: str) -> str:
    """Modifies the provided URL to fetch the raw text version."""
    url = url.rstrip('/') # Remove trailing slash
    
    # Check for mclo.gs
    mclogs_match = re.match(r'https?://(?:www\.)?mclo\.gs/([a-zA-Z0-9]+)', url)
    if mclogs_match:
        log_id = mclogs_match.group(1)
        return f"https://api.mclo.gs/1/raw/{log_id}"
    
    # Check for gnomebot.dev linking to mclogs (gnomebot.dev/paste/mclogs/ID -> mclo.gs)
    gnomebot_mclogs_match = re.match(r'https?://(?:www\.)?gnomebot\.dev/paste/mclogs/([a-zA-Z0-9]+)', url)
    if gnomebot_mclogs_match:
        log_id = gnomebot_mclogs_match.group(1)
        return f"https://api.mclo.gs/1/raw/{log_id}"

    # Check for native gnomebot.dev paste (gnomebot.dev/ID or gnomebot.dev/raw/ID)
    gnomebot_match = re.match(r'https?://(?:www\.)?gnomebot\.dev/(?:raw/)?([a-zA-Z0-9]+)', url)
    if gnomebot_match:
        log_id = gnomebot_match.group(1)
        return f"https://gnomebot.dev/raw/{log_id}"
        
    paste_gnomebot_match = re.match(r'https?://(?:www\.)?paste\.gnomebot\.dev/(?:raw/)?([a-zA-Z0-9]+)', url)
    if paste_gnomebot_match:
        log_id = paste_gnomebot_match.group(1)
        return f"https://paste.gnomebot.dev/raw/{log_id}"
    
    # Fallback to appending /raw if we don't recognize the host specifically
    if "/raw" not in url:
        return f"{url}/raw"
    return url

def fetch_log(url: str) -> str:
    raw_url = get_raw_url(url)
    print(f"Fetching log from: {raw_url}")
    try:
        response = requests.get(raw_url, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch log from {url}. Error: {e}", file=sys.stderr)
        return None

def analyze_log(log_content: str, api_key: str = None, model_name: str = 'gemini-3.1-pro-preview') -> Tuple[Optional[str], Optional[str]]:
    print("Analyzing log with Gemini AI...")
    try:
        if api_key:
            client = genai.Client(api_key=api_key)
        else:
            client = genai.Client()
            
        prompt = f"{SYSTEM_PROMPT}\n\nHere is the log to analyze:\n```\n{log_content}\n```"
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response.text, None
        
    except Exception as e:
        error_msg = f"Failed to analyze log. Error: {e}"
        print(error_msg, file=sys.stderr)
        return None, error_msg

def main():
    parser = argparse.ArgumentParser(description="Analyze Minecraft crash logs using Gemini AI.")
    parser.add_argument("urls", nargs='+', help="One or more URLs to the logs (mclo.gs or gnomebot.dev).")
    parser.add_argument("--save", action="store_true", help="Save the downloaded logs to disk.")
    
    args = parser.parse_args()
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.", file=sys.stderr)
        print("Please set it using: export GEMINI_API_KEY='your_api_key'", file=sys.stderr)
        sys.exit(1)

    
    for url in args.urls:
        print(f"\n--- Processing: {url} ---")
        log_content = fetch_log(url)
        
        if not log_content:
            continue
            
        if args.save:
            # Generate a filename based on the URL or a timestamp
            url_part = url.rstrip('/').split('/')[-1]
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', url_part)
            filename = f"log_{safe_name}.txt"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(log_content)
            print(f"Saved log to {filename}")
            
        analysis, error = analyze_log(log_content, api_key=api_key)
        
        if analysis:
            print("\n" + "="*50)
            print("GEMINI ANALYSIS:")
            print("="*50)
            print(analysis)
            print("="*50 + "\n")
        elif error:
            print("\n" + "="*50)
            print("ERROR:")
            print("="*50)
            print(error)
            print("="*50 + "\n")

if __name__ == "__main__":
    main()
