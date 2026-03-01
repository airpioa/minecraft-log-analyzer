# Changelog

All notable changes to **minecraft-log-analyzer** will be documented in this file.

## [0.3.0] - 2026-03-01

### Added
- **Web-Native LLM Engine**:
  - Replaced Ollama with **WebLLM**, enabling high-performance model execution (Llama 3.1, Mistral, Gemma) directly in the browser via WebGPU.
  - Added a real-time download progress bar for model caching.
- **Enhanced Security**:
  - Migrated API key storage from `localStorage` to **Secure Cookies** with a 30-day expiration and `Strict` SameSite policy.
- **CORS Bypass System**:
  - Integrated an intelligent CORS proxy toggle in settings to handle browser blocks for local/custom providers.
  - Added automated "CORS Error" detection that prompts users to enable the proxy when a block is detected.
- **Experimental Chrome AI**:
  - Added support for Chrome's built-in **Gemini Nano** (Window AI API).
  - Included a "How to Enable" guide for experimental browser flags in the sidebar.

### Changed
- **Branding**: Updated the application name to **minecraft-log-analyzer** and standardized logos using official brand assets for Forge and Fabric.
- **Dependency Management**: Integrated `@mlc-ai/web-llm` and `js-cookie` for core functionality.

### Fixed
- **Build & Scope**: Resolved critical JSX nesting issues and unclosed try/catch blocks that caused build failures.
- **API Clean-up**: Removed obsolete server-side routes to ensure 100% compatibility with static GitHub Pages hosting.

## [0.2.0] - 2026-03-01

### Added
- **Client-Side AI Architecture**:
  - Migrated all AI logic from server-side to the browser for full static portability.
- **Manual Prompting Overhaul**:
  - Consolidated "Manual Paste" and "Prompt Maker" into a single, high-power tab.
  - Added **Import from Cloud** functionality to pull raw logs from URLs directly into the workspace.
- **Compatibility Hub**:
  - A dedicated workspace for mod compatibility scans and quick search tools.
- **Selection Intelligence**:
  - Added **AI Selection Explain**: Highlight any part of a log for an instant technical explanation.
  - **Selection Search**: Floating toolbar to look up highlighted text on modding platforms.

## [0.1.0] - 2026-03-01

### Added
- **Initial GUI Implementation**: REDESIGNED from Python desktop tool to Next.js web application.
- **AI Compatibility Scanning**: Automated mod conflict detection.
- **Progress Visualization**: Added loading states and processing indicators.
