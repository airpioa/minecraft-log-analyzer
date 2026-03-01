# Changelog

All notable changes to the Minecraft Log Analyzer will be documented in this file.

## [0.2.0] - 2026-03-01

### Added
- **Client-Side AI Architecture**:
  - Migrated all AI logic from server-side to the browser for full static portability.
  - Enabled direct communication with local **Ollama** instances (`localhost:11434`) via the browser.
- **Manual Prompting Overhaul**:
  - Consolidated "Manual Paste" and "Prompt Maker" into a single, high-power tab.
  - Added **Import from Cloud** functionality to pull raw logs from URLs directly into the workspace.
  - **Dual-Source Prompting**: Separate buttons for generating prompts using **Raw Text** vs. **Cloud URLs**.
- **Compatibility Hub**:
  - A dedicated workspace for mod compatibility scans and quick search tools.
  - Integrated a **Scan Source** portal for managing log links directly within the hub.
- **Selection Intelligence**:
  - Added **AI Selection Explain**: Highlight any part of a log and click the brain icon for an instant technical explanation.
  - **Selection Search**: Floating toolbar to instantly look up highlighted text on Forge, Fabric, Minecraft Source, or Google.
- **Visual Branding**:
  - Integrated official **Forge (Anvil)** and **Fabric Loader** logos.
  - Added custom **Minecraft Logo** SVG for source lookups.
- **Automated CI/CD**:
  - Added GitHub Actions workflow for automatic deployment to GitHub Pages.
  - Implemented build caching (`actions/cache@v4`) for faster deployment runs.

### Changed
- **Navigation**: Redesigned the main menu into three focused tabs: Cloud Logs, Manual Prompting, and Comp. Hub.
- **Model Selection**: Standardized auto-fetching and dropdown menus across all providers (Gemini, OpenAI, Anthropic, Ollama).
- **UI Design**: Modernized the layout with a glass-morphism aesthetic and refined spacing.
- **Prompts**: Updated all AI instructions to include a mandatory signature and project URL.

### Fixed
- **Parsing Errors**: Resolved several build-time errors related to JSX structure and template literals.
- **Static Export**: Removed server-side API routes that were incompatible with `output: 'export'`.
- **CORS Support**: Implemented client-side fetching to better handle local AI instances.

## [0.1.0] - 2026-03-01

### Added
- **AI Compatibility Scanning**:
  - New "Scan for Conflicts (AI)" button in the Paste Log tab.
  - Manual scan prompt generation for web-based AI.
- **Initial GUI Implementation**: REDESIGNED from Python desktop tool to Next.js web application.
- **Progress Visualization**: Added loading states and processing indicators.
- **Custom AI Support**: Added API Key support for "Custom OpenAI-Compatible" providers.
