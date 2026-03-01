# minecraft-log-analyzer

A modern, high-performance web application designed to diagnose Minecraft crash logs using AI. Built with Next.js and Tailwind CSS, it offers a seamless experience for both automated API-driven analysis and manual AI prompting.

**Live Demo**: [https://airpioa.github.io/minecraft-log-analyzer/](https://airpioa.github.io/minecraft-log-analyzer/)

## Key Features

### 🧠 Direct Browser AI
- **Static Portability**: All AI logic has been moved to the client side. The app runs entirely in your browser, making it compatible with static hosting like GitHub Pages.
- **Local Ollama Support**: Communicate directly with a local Ollama instance (`localhost:11434`) without needing an SSH tunnel or server proxy.
- **Multi-Provider**: Native support for **Google Gemini**, **OpenAI**, **Anthropic Claude**, and any **OpenAI-Compatible** API (like Groq or Together).

### 🛠️ Workspaces
- **Cloud Logs**: Enter `mclo.gs` or other raw log URLs for rapid automated analysis.
- **Manual Prompting**: Consolidate raw text and cloud URLs into powerful prompts for external AI windows.
- **Compatibility Hub**: A dedicated space for scanning mod conflicts, missing libraries, and version mismatches.

### 🔍 Precision Tools
- **Selection Search**: Highlight any part of a log to instantly look it up on Forge/Neo, Fabric, Minecraft Source, or Google.
- **AI Selection Explain**: Highlight a cryptic error or stack trace and click the brain icon for an instant AI-powered technical explanation.
- **Auto-Fetching Models**: Automatically populates model dropdowns for all providers once your API key or Base URL is entered.

## Development

This is a Next.js project using Turbopack.

### Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Static Export

To build the project for static hosting:

```bash
npm run build
```

The output will be in the `out/` directory.

## Deployment

The application is automatically deployed to GitHub Pages via GitHub Actions whenever changes are pushed to the `master` branch.

---
*This was made by an automated tool that uses AI: https://airpioa.github.io/minecraft-log-analyzer*
