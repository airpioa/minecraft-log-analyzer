# Minecraft Log Analyzer

A Python command-line tool that takes log URLs from `mclo.gs` and `gnomebot.dev`, downloads the raw logs, and sends them to the Gemini AI for analysis. The AI points out the core issues causing crashes or errors, following a specific structured solution format.

## Prerequisites

1. **Python 3.7+**
2. **Google Gemini API Key**: You need an API key from Google AI Studio.

## Installation

1. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set your Gemini API key as an environment variable (Replace `your_api_key_here` with your actual key):

   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

## Usage

Run the tool with one or more log URLs as arguments.

```bash
python3 analyze_logs.py <url1> [url2 ...]
```

### Options

* `--save`: Add this flag to save the downloaded raw logs to disk as text files (e.g., `log_XXXXXXX.txt`).

### Examples

**Analyze a single log without saving:**

```bash
python3 analyze_logs.py https://mclo.gs/XXXXXXX
```

**Analyze multiple logs and save them to disk:**

```bash
python3 analyze_logs.py https://mclo.gs/XXXXXXX https://paste.gnomebot.dev/YYYYYYY --save
```
