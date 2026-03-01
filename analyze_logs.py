import argparse
import os
import sys
import re
import requests
from typing import Tuple, Optional
from google import genai

SYSTEM_PROMPT = """
You are an expert Minecraft log analyzer. Please analyze the following log and:
1. Identify the core error or reason for the crash/failure.
2. Provide a clear, step-by-step solution.
3. If it's a mod conflict, specify which mods are involved.
4. If it's a version mismatch (e.g., Fabric vs Forge), explain the fix.
Keep your response concise, helpful, and professional.

This was made by an automated tool that uses AI
"""


SCANNER_PROMPT = """
You are a Minecraft Mod Compatibility Specialist. Scan the following log specifically for:
1. Mod Conflicts: Identify mods that cannot run together (e.g., Sodium + Optifine).
2. Missing Dependencies: List any mods that are missing their required library mods.
3. Version Mismatches: Check for mods built for a different Minecraft version than the one running.
4. Duplicate Mods: Identify if multiple versions of the same mod are present.

Output only a bulleted list of suspected compatibility issues. If none are found, state "No obvious compatibility issues detected."

This was made by an automated tool that uses AI
"""



def get_raw_url(url: str) -> str:
    """Modifies the provided URL to fetch the raw text version."""
    url = url.strip().strip('<>') # Remove whitespace and angle brackets
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

def upload_to_mclogs(log_content: str) -> Optional[str]:
    """Uploads the provided log content to mclo.gs and returns the resulting raw URL."""
    print("Uploading log to mclo.gs...")
    try:
        url = "https://api.mclo.gs/1/log"
        data = {"content": log_content}
        response = requests.post(url, data=data, timeout=15)
        response.raise_for_status()
        result = response.json()
        if result.get("success"):
            log_id = result.get("id")
            return f"https://api.mclo.gs/1/raw/{log_id}"
        else:
            print(f"mclo.gs upload failed: {result.get('error')}", file=sys.stderr)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Failed to upload log to mclo.gs. Error: {e}", file=sys.stderr)
        return None

def analyze_log_gemini(log_content: str, api_key: str, model_name: str, system_prompt: str = SYSTEM_PROMPT) -> Tuple[Optional[str], Optional[str]]:
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"{system_prompt}\n\nHere is the log to analyze:\n```\n{log_content}\n```"
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response.text, None
    except Exception as e:
        return None, f"Gemini Error: {e}"

def analyze_log_openai(log_content: str, api_key: str, base_url: str, model_name: str, system_prompt: str = SYSTEM_PROMPT) -> Tuple[Optional[str], Optional[str]]:
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the log to analyze:\n```\n{log_content}\n```"}
            ]
        }
        response = requests.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'], None
    except Exception as e:
        return None, f"API Error: {e}"

def analyze_log_ollama(log_content: str, base_url: str, model_name: str, system_prompt: str = SYSTEM_PROMPT) -> Tuple[Optional[str], Optional[str]]:
    try:
        # Try /api/chat first (Preferred)
        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the log to analyze:\n```\n{log_content}\n```"}
            ],
            "stream": False
        }
        response = requests.post(f"{base_url.rstrip('/')}/api/chat", json=data, timeout=120)
        
        # If /api/chat fails, try /v1/chat/completions (OpenAI Compatible)
        if response.status_code == 404:
            data_v1 = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is the log to analyze:\n```\n{log_content}\n```"}
                ],
                "stream": False
            }
            response = requests.post(f"{base_url.rstrip('/')}/v1/chat/completions", json=data_v1, timeout=120)

        # If still 404, try /api/generate (Legacy)
        if response.status_code == 404:
            data_legacy = {
                "model": model_name,
                "system": system_prompt,
                "prompt": f"Here is the log to analyze:\n```\n{log_content}\n```",
                "stream": False
            }
            response = requests.post(f"{base_url.rstrip('/')}/api/generate", json=data_legacy, timeout=120)

        # Final check
        if not response.ok:
            return None, f"Ollama Error: {response.status_code} - {response.text}"
            
        result = response.json()
        if 'message' in result: # /api/chat
            return result['message']['content'], None
        elif 'choices' in result: # /v1/chat/completions
            return result['choices'][0]['message']['content'], None
        elif 'response' in result: # /api/generate
            return result['response'], None
        
        return None, f"Ollama Error: Unexpected response format: {result}"

    except Exception as e:
        return None, f"Ollama Error: {e}"



def get_ollama_models(base_url: str) -> list:
    """Fetches the list of available models from the local Ollama instance."""
    try:
        response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()
        return [m['name'] for m in data.get('models', [])]
    except Exception:
        return []

    except Exception:
        return []

def analyze_log_anthropic(log_content: str, api_key: str, model_name: str, system_prompt: str = SYSTEM_PROMPT) -> Tuple[Optional[str], Optional[str]]:



    try:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        data = {
            "model": model_name,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": f"Here is the log to analyze:\n```\n{log_content}\n```"}
            ],
            "max_tokens": 4096
        }
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result['content'][0]['text'], None
    except Exception as e:
        return None, f"Anthropic Error: {e}"

def analyze_log(log_content: str, provider: str = 'gemini', model_name: str = None, system_prompt: str = SYSTEM_PROMPT, **kwargs) -> Tuple[Optional[str], Optional[str]]:
    print(f"Analyzing log with {provider} ({model_name})...")
    
    if provider == 'gemini':
        api_key = kwargs.get('api_key') or os.environ.get("GEMINI_API_KEY")
        return analyze_log_gemini(log_content, api_key, model_name or 'gemini-3.1-pro-preview', system_prompt=system_prompt)
    
    elif provider == 'openai':
        api_key = kwargs.get('api_key') or os.environ.get("OPENAI_API_KEY")
        return analyze_log_openai(log_content, api_key, "https://api.openai.com/v1", model_name or "gpt-4o", system_prompt=system_prompt)

    elif provider == 'anthropic':
        api_key = kwargs.get('api_key') or os.environ.get("ANTHROPIC_API_KEY")
        return analyze_log_anthropic(log_content, api_key, model_name or "claude-3-5-sonnet-20240620", system_prompt=system_prompt)
    
    elif provider == 'ollama':
        base_url = kwargs.get('base_url') or "http://localhost:11434"
        return analyze_log_ollama(log_content, base_url, model_name or "llama3", system_prompt=system_prompt)
        
    elif provider == 'openai_compatible':
        base_url = kwargs.get('base_url')
        api_key = kwargs.get('api_key')
        return analyze_log_openai(log_content, api_key, base_url, model_name, system_prompt=system_prompt)



    return None, f"Unknown provider: {provider}"

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
