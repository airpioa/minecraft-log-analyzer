# Minecraft Log Analyzer

A desktop GUI tool that fetches Minecraft crash logs from **mclo.gs** and **gnomebot.dev**, then uses the **Gemini AI API** to analyze them and explain exactly what's wrong and how to fix it.

## Installation

```bash
pip install -r requirements.txt
python3 gui.py
```

> **Note**: On some systems you may need to set up a virtual environment first:
>
> ```bash
> python3 -m venv venv && source venv/bin/activate
> pip install -r requirements.txt
> python3 gui.py
> ```

## How to Use the GUI

### 1. Enter Log URLs

At the top of the window, paste one or more log URLs — one per line:

```
https://mclo.gs/XXXXXXX
https://gnomebot.dev/paste/mclogs/YYYYYYY
```

---

### 2. Manual Mode (Default)

Use this if you don't have a Gemini API key, or want to use [Gemini on the web](https://gemini.google.com).

1. Click **"Fetch Log & Generate Prompt"**
2. The logs are saved to your disk — their file paths appear in the **"Saved Log Paths"** box
3. Click **"Copy Prompt to Clipboard"**
4. Go to [gemini.google.com](https://gemini.google.com), **upload the saved log files**, then paste the prompt

---

### 3. API Mode

Use this if you have a [Gemini API key](https://aistudio.google.com).

1. Enter your API key in the **"Gemini API Key"** field
2. Choose a model from the **AI Model** dropdown (Gemini 3.1 Pro Preview is recommended)
3. Click **"Analyze Logs with AI"**
4. Results appear in the output box below

Your API key, preferred model, and save directory are all automatically saved in `config.json` for next time.

---

### 4. Settings

- **Default Save Directory**: Choose where downloaded log files are saved
- **Automatically save fetched logs to disk**: Toggle log saving on/off

## Getting a Free API Key

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account
3. Click **"Get API key"**
4. Paste it into the API Mode tab

## CLI Usage

You can also run the analyzer from the command line:

```bash
export GEMINI_API_KEY="your_key_here"
python3 analyze_logs.py https://mclo.gs/XXXXXXX --save
```

Use `--save` to download the log file to disk alongside the analysis.
