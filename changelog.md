# Changelog

All notable changes to the Minecraft Log Analyzer will be documented in this file.

## [Unreleased] - 2026-03-01

### Added

- **AI Compatibility Scanning**:
  - New "Scan for Conflicts (AI)" button in the Paste Log tab for automated mod conflict detection.
  - New "Scan for Compatibility (Manual)" button in the Manual Mode tab to generate specialized prompts for web-based AI.
- **Progress Visualization**:
  - Added a functioning progress bar (0-100%) in the API tab.
  - Persistent execution log in the API text area (shows fetch/analysis steps before results).
- **Custom AI Support**:
  - Added API Key support for "Custom OpenAI-Compatible" providers in Settings.
  - Added "Custom AI System Prompt" editor in Settings with a reset feature.
- **AI Attribution**:
  - All AI-generated content now includes a mandatory footer ("This was made by an automated tool that uses AI") for transparency.

### Changed

- **Ollama Integration**:
  - Implemented a robust triple-fallback system for API calls (`/api/chat` -> `/v1/chat/completions` -> `/api/generate`).
  - Improved model detection to automatically find locally installed models like **Gemma 3**.
- **Search Platforms**:
  - **Minecraft Source**: Updated to a more reliable community repository at `git.merded.zip`.
  - **Forge/Neo**: Updated to point to the official CodeSearch endpoint.
- **User Interface**:
  - Redesigned model dropdowns to dynamically update based on the selected provider.
  - Synchronized provider and model selections across all tabs in real-time.
  - Added provider-neutral placeholder text in the analysis area.

### Fixed

- **ApiWorker Crash**: Resolved a `TypeError` when initializing the AI scanner.
- **URL Fetching**: Fixed the "No connection adapters" error by automatically stripping angle brackets (`<`, `>`) from log links.
- **Settings Crash**: Fixed an `AttributeError` caused by missing UI element references during configuration sync.
- **Cleaned Up Provider List**: Removed the deprecated OpenRouter provider from the GUI and backend.
- **Ollama 404s**: Corrected endpoint routing to support different Ollama version configurations.
