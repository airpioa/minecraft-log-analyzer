import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTabWidget, QTextEdit, 
    QFileDialog, QMessageBox, QCheckBox, QProgressBar, QComboBox,
    QGridLayout, QInputDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import analyze_logs
import webbrowser
import urllib.parse
import re

CONFIG_FILE = "config.json"

class ApiWorker(QThread):
    finished = pyqtSignal(str, str) # result, error
    progress = pyqtSignal(str)
    progress_val = pyqtSignal(int)

    
    def __init__(self, urls=None, api_key=None, model_name=None, save_dir=None, save_logs=False, content=None, provider='gemini', base_url=None, system_prompt=None):
        super().__init__()
        self.urls = urls or []
        self.api_key = api_key
        self.model_name = model_name
        self.save_dir = save_dir
        self.save_logs = save_logs
        self.content = content
        self.provider = provider
        self.base_url = base_url
        self.system_prompt = system_prompt or analyze_logs.SYSTEM_PROMPT
        
    def run(self):
        try:
            all_results = []
            
            if self.content:
                # Direct content analysis
                self.progress_val.emit(10)
                self.progress.emit("Analyzing pasted log...")
                analysis, error = analyze_logs.analyze_log(self.content, provider=self.provider, model_name=self.model_name, 
                                                        api_key=self.api_key, base_url=self.base_url, system_prompt=self.system_prompt)
                self.progress_val.emit(90)
                if analysis:
                    all_results.append(f"--- Analysis for Pasted Log ---\n{analysis}\n")
                elif error:
                    all_results.append(f"--- Analysis for Pasted Log ---\n{error}\n")
                else:
                    all_results.append("--- Analysis for Pasted Log ---\nFailed to generate analysis.\n")
                self.progress_val.emit(100)
            else:
                # URL fetching and analysis
                total = len(self.urls)
                for i, url in enumerate(self.urls):
                    base_progress = (i / total) * 100
                    self.progress_val.emit(int(base_progress + 5))
                    self.progress.emit(f"[{i+1}/{total}] Fetching log from {url}...")

                    log_content = analyze_logs.fetch_log(url)
                    
                    if not log_content:
                        all_results.append(f"--- Analysis for {url} ---\nFailed to fetch log.\n")
                        self.progress_val.emit(int(base_progress + (1/total)*100))
                        continue
                        
                    self.progress_val.emit(int(base_progress + 20/total))
                    if self.save_logs:
                        # ... (save logic remains same)
                        url_part = url.rstrip('/').split('/')[-1]
                        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', url_part)
                        filename = f"log_{safe_name}.txt"
                        save_path = os.path.join(self.save_dir, filename)
                        try:
                            with open(save_path, "w", encoding="utf-8") as f:
                                f.write(log_content)
                        except Exception as e:
                            print(f"Thread save error: {e}")
                            
                    self.progress.emit(f"[{i+1}/{total}] Analyzing log from {url}...")
                    self.progress_val.emit(int(base_progress + 40/total))
                    
                    analysis, error = analyze_logs.analyze_log(log_content, provider=self.provider, model_name=self.model_name, 
                                                        api_key=self.api_key, base_url=self.base_url, system_prompt=self.system_prompt)
                    if analysis:
                        all_results.append(f"--- Analysis for {url} ---\n{analysis}\n")
                    elif error:
                        all_results.append(f"--- Analysis for {url} ---\n{error}\n")
                    else:
                        all_results.append(f"--- Analysis for {url} ---\nFailed to generate analysis.\n")
                    self.progress_val.emit(int(base_progress + (1/total)*100))
                    
            self.finished.emit("\n".join(all_results), "")

        except Exception as e:
            self.finished.emit("", str(e))


class LogAnalyzerGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Minecraft Log Analyzer")
        self.resize(800, 600)
        
        self.config_data = {
            "gemini_api_key": "",
            "openrouter_api_key": "",
            "openai_api_key": "",
            "anthropic_api_key": "",
            "custom_openai_url": "https://api.example.com/v1",
            "ollama_url": "http://localhost:11434",
            "provider": "gemini",
            "model_name": "gemini-3.1-pro-preview",
            "search_platform": "forge",
            "save_dir": os.getcwd(),
            "default_mode": "manual",
            "save_logs": True,
            "system_prompt": analyze_logs.SYSTEM_PROMPT
        }
        self.load_config()
        self.init_ui()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.config_data.update(data)
            except Exception as e:
                print(f"Error loading config: {e}")
                
    def save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config_data, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def init_ui(self):
        # Central Widget & Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Top Frame (URL Input)
        top_layout = QVBoxLayout()
        top_layout.addWidget(QLabel("Log URLs (mclo.gs or gnomebot.dev) - One per line:"))
        self.url_input = QTextEdit()
        self.url_input.setFixedHeight(80)
        self.url_input.setPlaceholderText("https://mclo.gs/XXXXX\nhttps://gnomebot.dev/YYYYY")
        top_layout.addWidget(self.url_input)
        main_layout.addLayout(top_layout)
        
        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # -- Manual Mode Tab --
        manual_tab = QWidget()
        manual_layout = QVBoxLayout(manual_tab)
        
        manual_controls = QHBoxLayout()
        fetch_btn = QPushButton("Fetch Log & Generate Prompt")
        fetch_btn.clicked.connect(self.generate_manual_prompt)
        manual_controls.addWidget(fetch_btn)
        
        copy_btn = QPushButton("Copy Prompt to Clipboard")
        copy_btn.clicked.connect(self.copy_prompt)
        manual_controls.addWidget(copy_btn)
        manual_controls.addStretch()
        
        manual_layout.addLayout(manual_controls)
        
        manual_layout.addWidget(QLabel("Saved Log Paths (Upload these files to Gemini):"))
        self.paths_text = QTextEdit()
        self.paths_text.setReadOnly(True)
        self.paths_text.setFixedHeight(60)
        manual_layout.addWidget(self.paths_text)

        manual_layout.addWidget(QLabel("Instructions Prompt (Copy and paste this into Gemini):"))
        self.manual_text = QTextEdit()
        self.manual_text.setPlainText("Enter URL(s) and click 'Fetch Log & Generate Prompt' to get started.")
        manual_layout.addWidget(self.manual_text)
        
        # Manual Compatibility Check
        manual_layout.addWidget(QLabel("Manual Compatibility Check (for mclo.gs or gnomebot.dev URLs):"))
        self.manual_url_input = QLineEdit()
        self.manual_url_input.setPlaceholderText("https://mclo.gs/XXXXX")
        manual_layout.addWidget(self.manual_url_input)

        manual_btn_layout = QHBoxLayout()
        self.manual_scan_btn = QPushButton("Scan for Compatibility (Manual)")
        self.manual_scan_btn.clicked.connect(self.manual_scan_compatibility)
        manual_btn_layout.addWidget(self.manual_scan_btn)
        manual_layout.addLayout(manual_btn_layout)

        self.tabs.addTab(manual_tab, "Manual Mode (Default)")
        
        # Search Buttons for Manual Mode
        self.manual_search_layout = QHBoxLayout()
        self.manual_search_layout.addWidget(QLabel("Search Highlighted Text:"))
        
        forge_btn = QPushButton("Forge/Neo (Codesearch)")
        forge_btn.clicked.connect(lambda: self.search_source("forge"))
        self.manual_search_layout.addWidget(forge_btn)
        
        fabric_btn = QPushButton("Fabric/Quilt (GitHub)")
        fabric_btn.clicked.connect(lambda: self.search_source("fabric"))
        self.manual_search_layout.addWidget(fabric_btn)
        
        google_btn = QPushButton("Google Search")
        google_btn.clicked.connect(lambda: self.search_source("google"))
        self.manual_search_layout.addWidget(google_btn)
        self.manual_search_layout.addStretch()
        manual_layout.addLayout(self.manual_search_layout)

        # -- API Mode Tab --
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)

        # 1. Create Widgets
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("AI Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItem("Google Gemini", "gemini")
        self.provider_combo.addItem("OpenAI (ChatGPT)", "openai")
        self.provider_combo.addItem("Anthropic (Claude)", "anthropic")
        self.provider_combo.addItem("Ollama (Local)", "ollama")
        self.provider_combo.addItem("Custom OpenAI-Compatible", "openai_compatible")
        provider_layout.addWidget(self.provider_combo)

        analyze_btn = QPushButton("Analyze Logs with AI")
        provider_layout.addWidget(analyze_btn)
        provider_layout.addStretch()
        api_layout.addLayout(provider_layout)

        model_controls = QHBoxLayout()
        model_controls.addWidget(QLabel("AI Model:"))
        self.model_combo = QComboBox()
        model_controls.addWidget(self.model_combo)
        self.refresh_api_models_btn = QPushButton("Refresh")
        model_controls.addWidget(self.refresh_api_models_btn)
        model_controls.addStretch()
        api_layout.addLayout(model_controls)

        # 2. Connect Signals and Sync (Now safe because widgets exist)
        self.provider_combo.currentIndexChanged.connect(self.on_provider_changed)
        self.model_combo.currentIndexChanged.connect(self.on_model_changed_api)
        self.refresh_api_models_btn.clicked.connect(self.update_model_list)

        analyze_btn.clicked.connect(self.analyze_with_api)

        # Initial Sync from Config
        saved_provider = self.config_data.get("provider", "gemini")
        for i in range(self.provider_combo.count()):
            if self.provider_combo.itemData(i) == saved_provider:
                self.provider_combo.blockSignals(True)
                self.provider_combo.setCurrentIndex(i)
                self.provider_combo.blockSignals(False)
                break




        self.api_progress = QProgressBar()
        self.api_progress.setRange(0, 0) # Indeterminate mode
        self.api_progress.hide()
        api_layout.addWidget(self.api_progress)

        self.api_text = QTextEdit()
        self.api_text.setPlainText("AI Analysis results will appear here.")

        api_layout.addWidget(self.api_text)

        self.tabs.addTab(api_tab, "API Mode")

        # -- Paste Log Tab (Manual Input) --
        paste_tab = QWidget()
        paste_layout = QVBoxLayout(paste_tab)

        paste_layout.addWidget(QLabel("Paste full log content here:"))

        # Search Bar for Paste Tab
        search_bar_layout = QHBoxLayout()
        self.log_search_input = QLineEdit()
        self.log_search_input.setPlaceholderText("Search in log...")
        self.log_search_input.returnPressed.connect(self.find_text_next)
        search_bar_layout.addWidget(self.log_search_input)

        find_next_btn = QPushButton("Find Next")
        find_next_btn.clicked.connect(self.find_text_next)
        search_bar_layout.addWidget(find_next_btn)

        find_prev_btn = QPushButton("Find Prev")
        find_prev_btn.clicked.connect(self.find_text_prev)
        search_bar_layout.addWidget(find_prev_btn)

        self.search_count_label = QLabel("Matches: 0")
        search_bar_layout.addWidget(self.search_count_label)
        search_bar_layout.addStretch()
        paste_layout.addLayout(search_bar_layout)

        self.pasted_log_text = QTextEdit()
        self.pasted_log_text.setAcceptRichText(False)
        self.pasted_log_text.setPlaceholderText("Paste your Minecraft log here...")
        self.pasted_log_text.textChanged.connect(self.on_pasted_text_changed)
        paste_layout.addWidget(self.pasted_log_text)

        paste_controls = QHBoxLayout()
        upload_log_btn = QPushButton("Upload Local Log (mclo.gs)")
        upload_log_btn.clicked.connect(self.import_local_log)
        paste_controls.addWidget(upload_log_btn)

        analyze_pasted_btn = QPushButton("Analyze Pasted Log with AI")
        analyze_pasted_btn.clicked.connect(self.analyze_pasted_log)
        paste_controls.addWidget(analyze_pasted_btn)

        scan_compatibility_btn = QPushButton("Scan for Conflicts (AI)")
        scan_compatibility_btn.clicked.connect(self.scan_compatibility)
        paste_controls.addWidget(scan_compatibility_btn)


        import_url_btn = QPushButton("Import from URL")
        import_url_btn.clicked.connect(self.import_log_from_url)
        paste_controls.addWidget(import_url_btn)
        
        export_log_btn = QPushButton("Export Log")
        export_log_btn.clicked.connect(self.export_pasted_log)
        paste_controls.addWidget(export_log_btn)
        
        clear_pasted_btn = QPushButton("Clear")
        clear_pasted_btn.clicked.connect(lambda: self.pasted_log_text.clear())
        paste_controls.addWidget(clear_pasted_btn)

        paste_controls.addStretch()
        paste_layout.addLayout(paste_controls)

        # Search Buttons for Paste Tab
        self.paste_search_layout = QHBoxLayout()
        self.paste_search_layout.addWidget(QLabel("Search Highlighted Text:"))

        forge_paste_btn = QPushButton("Forge/Neo (Codesearch)")
        forge_paste_btn.clicked.connect(lambda: self.search_source("forge"))
        self.paste_search_layout.addWidget(forge_paste_btn)

        fabric_paste_btn = QPushButton("Fabric/Quilt (GitHub)")
        fabric_paste_btn.clicked.connect(lambda: self.search_source("fabric"))
        self.paste_search_layout.addWidget(fabric_paste_btn)

        google_paste_btn = QPushButton("Google Search")
        google_paste_btn.clicked.connect(lambda: self.search_source("google"))
        self.paste_search_layout.addWidget(google_paste_btn)
        
        mc_source_paste_btn = QPushButton("Minecraft Source (GitHub)")
        mc_source_paste_btn.clicked.connect(lambda: self.search_source("mc"))
        self.paste_search_layout.addWidget(mc_source_paste_btn)

        self.paste_search_layout.addStretch()
        paste_layout.addLayout(self.paste_search_layout)

        self.tabs.addTab(paste_tab, "Paste Log")

        # -- Code Search Tab --
        search_tab = QWidget()
        search_tab_layout = QVBoxLayout(search_tab)

        search_tab_layout.addWidget(QLabel("Enter class name, error, or mod name to search:"))
        self.manual_search_input = QLineEdit()
        self.manual_search_input.setPlaceholderText("e.g. net.minecraft.class_123 or ModName")
        self.manual_search_input.returnPressed.connect(self.run_manual_search)
        search_tab_layout.addWidget(self.manual_search_input)

        search_tab_controls = QHBoxLayout()
        search_tab_controls.addWidget(QLabel("Search Platform:"))
        self.search_tab_combo = QComboBox()
        self.search_tab_combo.addItem("Forge/Neo (Codesearch)", "forge")
        self.search_tab_combo.addItem("Fabric/Quilt (GitHub)", "fabric")
        self.search_tab_combo.addItem("Google Search", "google")
        self.search_tab_combo.addItem("Minecraft Source (GitHub)", "mc")


        # Sync with config
        saved_platform = self.config_data.get("search_platform", "forge")
        for i in range(self.search_tab_combo.count()):
            if self.search_tab_combo.itemData(i) == saved_platform:
                self.search_tab_combo.setCurrentIndex(i)
                break

        self.search_tab_combo.currentIndexChanged.connect(self.on_search_platform_changed_tab)
        search_tab_controls.addWidget(self.search_tab_combo)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.run_manual_search)
        search_tab_controls.addWidget(search_btn)
        search_tab_controls.addStretch()
        search_tab_layout.addLayout(search_tab_controls)

        search_tab_layout.addWidget(QLabel("Note: This is useful for looking up errors found in Gemini Web or other logs."))
        search_tab_layout.addStretch()

        self.tabs.addTab(search_tab, "Code Search")

        # Search Buttons for API Mode
        self.api_search_layout = QHBoxLayout()
        self.api_search_layout.addWidget(QLabel("Search Highlighted Text:"))

        forge_api_btn = QPushButton("Forge/Neo (Codesearch)")
        forge_api_btn.clicked.connect(lambda: self.search_source("forge"))
        self.api_search_layout.addWidget(forge_api_btn)

        fabric_api_btn = QPushButton("Fabric/Quilt (GitHub)")
        fabric_api_btn.clicked.connect(lambda: self.search_source("fabric"))
        self.api_search_layout.addWidget(fabric_api_btn)

        google_api_btn = QPushButton("Google Search")
        google_api_btn.clicked.connect(lambda: self.search_source("google"))
        self.api_search_layout.addWidget(google_api_btn)
        
        mc_source_api_btn = QPushButton("Minecraft Source (GitHub)")
        mc_source_api_btn.clicked.connect(lambda: self.search_source("mc"))
        self.api_search_layout.addWidget(mc_source_api_btn)

        self.api_search_layout.addStretch()

        api_layout.addLayout(self.api_search_layout)

        # -- Settings Tab --
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)

        save_dir_layout = QHBoxLayout()
        save_dir_layout.addWidget(QLabel("Default Save Directory:"))
        self.save_dir_input = QLineEdit(self.config_data.get("save_dir", os.getcwd()))
        self.save_dir_input.textChanged.connect(self.on_config_change)
        save_dir_layout.addWidget(self.save_dir_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_save_dir)
        save_dir_layout.addWidget(browse_btn)
        settings_layout.addLayout(save_dir_layout)

        self.save_logs_checkbox = QCheckBox("Automatically save fetched logs to disk")
        self.save_logs_checkbox.setChecked(self.config_data.get("save_logs", True))
        self.save_logs_checkbox.stateChanged.connect(self.on_config_change)
        settings_layout.addWidget(self.save_logs_checkbox)

        search_pref_layout = QHBoxLayout()
        search_pref_layout.addWidget(QLabel("Preferred Search Platform:"))
        self.settings_search_combo = QComboBox()
        self.settings_search_combo.addItem("Forge/Neo (Codesearch)", "forge")
        self.settings_search_combo.addItem("Fabric/Quilt (GitHub)", "fabric")
        self.settings_search_combo.addItem("Google Search", "google")
        self.settings_search_combo.addItem("Minecraft Source (GitHub)", "mc")


        # Sync with config
        for i in range(self.settings_search_combo.count()):
            if self.settings_search_combo.itemData(i) == saved_platform:
                self.settings_search_combo.setCurrentIndex(i)
                break

        self.settings_search_combo.currentIndexChanged.connect(self.on_search_platform_changed_settings)
        search_pref_layout.addWidget(self.settings_search_combo)
        search_pref_layout.addStretch()
        settings_layout.addLayout(search_pref_layout)

        # AI Defaults Row
        ai_defaults_layout = QHBoxLayout()
        ai_defaults_layout.addWidget(QLabel("Default AI Provider:"))
        self.default_provider_combo = QComboBox()
        self.default_provider_combo.addItem("Google Gemini", "gemini")
        self.default_provider_combo.addItem("OpenAI (ChatGPT)", "openai")
        self.default_provider_combo.addItem("Anthropic (Claude)", "anthropic")
        self.default_provider_combo.addItem("Ollama (Local)", "ollama")
        self.default_provider_combo.addItem("Custom OpenAI-Compatible", "openai_compatible")

        
        # Sync with config
        saved_provider = self.config_data.get("provider", "gemini")
        for i in range(self.default_provider_combo.count()):
            if self.default_provider_combo.itemData(i) == saved_provider:
                self.default_provider_combo.setCurrentIndex(i)
                break
        
        ai_defaults_layout.addWidget(self.default_provider_combo)
        ai_defaults_layout.addSpacing(20)
        
        ai_defaults_layout.addWidget(QLabel("Default AI Model:"))
        self.default_model_combo = QComboBox()
        # Initialize default model list (will be updated when provider changes)
        ai_defaults_layout.addWidget(self.default_model_combo)

        self.refresh_default_models_btn = QPushButton("Refresh")
        self.refresh_default_models_btn.clicked.connect(self.update_default_model_list)
        ai_defaults_layout.addWidget(self.refresh_default_models_btn)

        ai_defaults_layout.addStretch()
        settings_layout.addLayout(ai_defaults_layout)


        self.default_provider_combo.currentIndexChanged.connect(self.on_default_provider_changed)
        self.default_model_combo.currentIndexChanged.connect(self.on_model_changed_settings)
        



        # API Key Management
        settings_layout.addWidget(QLabel("API Settings:"))

        api_keys_grid = QGridLayout()

        api_keys_grid.addWidget(QLabel("Gemini API Key:"), 0, 0)
        self.gemini_key_input = QLineEdit()
        self.gemini_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_key_input.setText(self.config_data.get("gemini_api_key", ""))
        self.gemini_key_input.textChanged.connect(self.on_config_change)
        api_keys_grid.addWidget(self.gemini_key_input, 0, 1)

        api_keys_grid.addWidget(QLabel("OpenAI Key:"), 1, 0)
        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key_input.setText(self.config_data.get("openai_api_key", ""))
        self.openai_key_input.textChanged.connect(self.on_config_change)
        api_keys_grid.addWidget(self.openai_key_input, 1, 1)

        api_keys_grid.addWidget(QLabel("Anthropic Key:"), 2, 0)
        self.anthropic_key_input = QLineEdit()
        self.anthropic_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.anthropic_key_input.setText(self.config_data.get("anthropic_api_key", ""))
        self.anthropic_key_input.textChanged.connect(self.on_config_change)
        api_keys_grid.addWidget(self.anthropic_key_input, 2, 1)

        api_keys_grid.addWidget(QLabel("Custom API Key:"), 3, 0)
        self.custom_key_input = QLineEdit()
        self.custom_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.custom_key_input.setText(self.config_data.get("custom_api_key", ""))
        self.custom_key_input.textChanged.connect(self.on_config_change)
        api_keys_grid.addWidget(self.custom_key_input, 3, 1)

        api_keys_grid.addWidget(QLabel("Ollama URL:"), 4, 0)
        self.ollama_url_input = QLineEdit()
        self.ollama_url_input.setText(self.config_data.get("ollama_url", "http://localhost:11434"))
        self.ollama_url_input.textChanged.connect(self.on_config_change)
        self.ollama_url_input.editingFinished.connect(self.update_model_list)
        self.ollama_url_input.returnPressed.connect(self.update_model_list)
        self.ollama_url_input.editingFinished.connect(self.update_default_model_list)
        api_keys_grid.addWidget(self.ollama_url_input, 4, 1)


        api_keys_grid.addWidget(QLabel("Custom API URL:"), 5, 0)
        self.custom_url_input = QLineEdit()
        self.custom_url_input.setText(self.config_data.get("custom_openai_url", "https://api.example.com/v1"))
        self.custom_url_input.textChanged.connect(self.on_config_change)
        api_keys_grid.addWidget(self.custom_url_input, 5, 1)


        settings_layout.addLayout(api_keys_grid)

        settings_layout.addWidget(QLabel("(These keys are saved locally in config.json)"))

        # Advanced Section
        settings_layout.addWidget(QLabel("\nAdvanced Settings:"))
        self.advanced_container = QWidget()
        advanced_layout = QVBoxLayout(self.advanced_container)

        advanced_layout.addWidget(QLabel("Custom AI System Prompt:"))
        self.prompt_editor = QTextEdit()
        self.prompt_editor.setPlainText(self.config_data.get("system_prompt", analyze_logs.SYSTEM_PROMPT))
        self.prompt_editor.textChanged.connect(self.on_config_change)
        advanced_layout.addWidget(self.prompt_editor)

        reset_prompt_btn = QPushButton("Reset Prompt to Default")
        reset_prompt_btn.clicked.connect(self.reset_system_prompt)
        advanced_layout.addWidget(reset_prompt_btn)

        settings_layout.addWidget(self.advanced_container)
        settings_layout.addStretch()

        self.tabs.addTab(settings_tab, "Settings")

        # Set default tab
        if self.config_data.get("default_mode") == "api":
            self.tabs.setCurrentIndex(1)
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # Final initialization of dynamic content
        self.update_model_list()
        self.update_default_model_list()

    def on_default_provider_changed(self, index):
        provider = self.default_provider_combo.itemData(index)
        self.config_data["provider"] = provider
        
        # Sync the API mode provider combo
        for i in range(self.provider_combo.count()):
            if self.provider_combo.itemData(i) == provider:
                self.provider_combo.blockSignals(True)
                self.provider_combo.setCurrentIndex(i)
                self.provider_combo.blockSignals(False)
                break
        
        self.update_default_model_list()
        self.update_model_list() # Sync API tab model list
        self.on_config_change()

    def update_default_model_list(self):
        self.default_model_combo.blockSignals(True)
        self.default_model_combo.clear()
        provider = self.default_provider_combo.currentData()
        models = self.get_models_for_provider(provider)

        for model in models:
            self.default_model_combo.addItem(model, model)

        saved_model = self.config_data.get("model_name")
        if saved_model:
            index = self.default_model_combo.findData(saved_model)
            if index != -1:
                self.default_model_combo.setCurrentIndex(index)
            else:
                # If switching provider, don't carry over incompatible models as custom
                if saved_model in ["gemini-3.1-pro-preview", "gemini-1.5-pro-latest", "gemini-1.0-pro"] and provider != "gemini":
                    self.default_model_combo.setCurrentIndex(0)
                elif saved_model == "__custom__":
                    self.default_model_combo.addItem(saved_model, saved_model)
                    self.default_model_combo.setCurrentIndex(self.default_model_combo.count() - 1)
                else:
                    # Only add as custom if it doesn't look like a standard model name from another provider
                    self.default_model_combo.addItem(f"Custom: {saved_model}", saved_model)
                    self.default_model_combo.setCurrentIndex(self.default_model_combo.count() - 1)
        
        if self.default_model_combo.currentIndex() == -1 and self.default_model_combo.count() > 0:
            self.default_model_combo.setCurrentIndex(0)
            
        self.default_model_combo.blockSignals(False)

    def get_models_for_provider(self, provider):
        if provider == "gemini":
            return ["gemini-3.1-pro-preview", "gemini-1.5-pro-latest", "gemini-1.0-pro"]
        elif provider == "openai":
            return ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "__custom__"]
        elif provider == "anthropic":
            return ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229", "__custom__"]
        elif provider == "ollama":
            base_url = self.ollama_url_input.text().strip() or "http://localhost:11434"
            models = analyze_logs.get_ollama_models(base_url)
            if not models: models = ["llama3", "mistral", "gemma2"]
            return models + ["__custom__"]

        elif provider == "openai_compatible":
            return ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "__custom__"]
        return []



    def update_model_list(self):
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        provider = self.provider_combo.currentData()
        models = self.get_models_for_provider(provider)

        for model in models:
            self.model_combo.addItem(model, model)

        # Try to set the previously saved model
        saved_model = self.config_data.get("model_name")
        if saved_model:
            index = self.model_combo.findData(saved_model)
            if index != -1:
                self.model_combo.setCurrentIndex(index)
            else:
                # If switching provider, don't carry over incompatible models as custom
                if saved_model in ["gemini-3.1-pro-preview", "gemini-1.5-pro-latest", "gemini-1.0-pro"] and provider != "gemini":
                    self.model_combo.setCurrentIndex(0)
                elif saved_model == "__custom__":
                    self.model_combo.addItem(saved_model, saved_model)
                    self.model_combo.setCurrentIndex(self.model_combo.count() - 1)
                else:
                    # Only add as custom if it doesn't look like a standard model name from another provider
                    self.model_combo.addItem(f"Custom: {saved_model}", saved_model)
                    self.model_combo.setCurrentIndex(self.model_combo.count() - 1)
        
        if self.model_combo.currentIndex() == -1 and self.model_combo.count() > 0:
            self.model_combo.setCurrentIndex(0)
            
        self.model_combo.blockSignals(False)

    def on_model_changed_api(self, index):
        model = self.model_combo.currentData()
        if not model: return
        self.config_data["model_name"] = model
        
        # Sync Settings tab model combo
        self.default_model_combo.blockSignals(True)
        idx = self.default_model_combo.findData(model)
        if idx != -1:
            self.default_model_combo.setCurrentIndex(idx)
        else:
            # If not found, it might be a custom model added to the API combo
            # Check if it's already a "Custom: X" entry before adding
            if not any(self.default_model_combo.itemData(i) == model for i in range(self.default_model_combo.count())):
                self.default_model_combo.addItem(f"Custom: {model}", model)
            self.default_model_combo.setCurrentIndex(self.default_model_combo.count() - 1)
        self.default_model_combo.blockSignals(False)
        
        self.on_config_change()

    def on_model_changed_settings(self, index):
        model = self.default_model_combo.currentData()
        if not model: return
        self.config_data["model_name"] = model
        
        # Sync API tab model combo
        self.model_combo.blockSignals(True)
        idx = self.model_combo.findData(model)
        if idx != -1:
            self.model_combo.setCurrentIndex(idx)
        else:
            # Check if it's already a "Custom: X" entry before adding
            if not any(self.model_combo.itemData(i) == model for i in range(self.model_combo.count())):
                self.model_combo.addItem(f"Custom: {model}", model)
            self.model_combo.setCurrentIndex(self.model_combo.count() - 1)
        self.model_combo.blockSignals(False)
        
        self.on_config_change()

    def on_provider_changed(self, index):
        provider = self.provider_combo.currentData()
        self.config_data["provider"] = provider
        
        # Sync Settings tab
        self.default_provider_combo.blockSignals(True)
        idx = self.default_provider_combo.findData(provider)
        if idx != -1:
            self.default_provider_combo.setCurrentIndex(idx)
        self.default_provider_combo.blockSignals(False)
        
        self.update_model_list()
        self.update_default_model_list() # Sync settings model list
        self.on_config_change()

    def on_config_change(self):
        self.config_data["gemini_api_key"] = self.gemini_key_input.text().strip()
        self.config_data["openai_api_key"] = self.openai_key_input.text().strip()
        self.config_data["anthropic_api_key"] = self.anthropic_key_input.text().strip()
        self.config_data["custom_api_key"] = self.custom_key_input.text().strip()
        self.config_data["ollama_url"] = self.ollama_url_input.text().strip()

        self.config_data["custom_openai_url"] = self.custom_url_input.text().strip()
        self.config_data["model_name"] = self.model_combo.currentData()
        self.config_data["save_dir"] = self.save_dir_input.text()


        self.config_data["save_logs"] = self.save_logs_checkbox.isChecked()
        self.config_data["search_platform"] = self.settings_search_combo.currentData()
        self.config_data["system_prompt"] = self.prompt_editor.toPlainText()
        self.save_config()

    def reset_system_prompt(self):
        reply = QMessageBox.question(self, "Reset Prompt", "Are you sure you want to reset the system prompt to default?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.prompt_editor.setPlainText(analyze_logs.SYSTEM_PROMPT)
            self.on_config_change()

    def on_search_platform_changed_tab(self, index):
        platform = self.search_tab_combo.currentData()
        self.config_data["search_platform"] = platform
        # Sync the settings tab combo
        for i in range(self.settings_search_combo.count()):
            if self.settings_search_combo.itemData(i) == platform:
                self.settings_search_combo.blockSignals(True)
                self.settings_search_combo.setCurrentIndex(i)
                self.settings_search_combo.blockSignals(False)
                break
        self.save_config()

    def on_search_platform_changed_settings(self, index):
        platform = self.settings_search_combo.currentData()
        self.config_data["search_platform"] = platform
        # Sync the search tab combo
        for i in range(self.search_tab_combo.count()):
            if self.search_tab_combo.itemData(i) == platform:
                self.search_tab_combo.blockSignals(True)
                self.search_tab_combo.setCurrentIndex(i)
                self.search_tab_combo.blockSignals(False)
                break
        self.save_config()

    def browse_save_dir(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select Save Directory", self.save_dir_input.text())
        if dir_name:
            self.save_dir_input.setText(dir_name)

    def fetch_and_save_logs(self):
        urls = [u.strip().strip('<>') for u in self.url_input.toPlainText().split('\n') if u.strip()]


        if not urls:
            QMessageBox.critical(self, "Error", "Please enter at least one URL.")
            return []
            
        saved_paths = []
        for url in urls:
            log_content = analyze_logs.fetch_log(url)
            if not log_content:
                QMessageBox.warning(self, "Warning", f"Failed to fetch log from: {url}")
                continue
                
            if self.save_logs_checkbox.isChecked():
                url_part = url.rstrip('/').split('/')[-1]
                safe_name = analyze_logs.re.sub(r'[^a-zA-Z0-9_-]', '_', url_part)
                filename = f"log_{safe_name}.txt"
                save_path = os.path.join(self.save_dir_input.text(), filename)
                try:
                    with open(save_path, "w", encoding="utf-8") as f:
                        f.write(log_content)
                    print(f"Saved log to {save_path}")
                    saved_paths.append(save_path)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save log to disk: {e}")
                    
        return saved_paths

    def generate_manual_prompt(self):
        # Force save_logs to be True for manual mode since we need the file
        original_save_state = self.save_logs_checkbox.isChecked()
        self.save_logs_checkbox.setChecked(True)
        
        saved_paths = self.fetch_and_save_logs()
        
        # Restore original state
        self.save_logs_checkbox.setChecked(original_save_state)
        
        if saved_paths:
            self.paths_text.setPlainText("\n".join(saved_paths))
            prompt = f"{analyze_logs.SYSTEM_PROMPT}\n\nI have attached the required log files. Please analyze them based on the strict format specified above.\n\nThis was made by an automated tool that uses AI"

            self.manual_text.setPlainText(prompt)
            QMessageBox.information(self, "Success", f"{len(saved_paths)} log(s) fetched, saved, and prompt generated!\n\n1. Upload the files listed in 'Saved Log Paths' to Gemini.\n2. Click 'Copy Prompt' and paste the instructions.")


    def copy_prompt(self):
        prompt = self.manual_text.toPlainText().strip()
        if prompt and prompt != "Enter URL(s) and click 'Fetch Log & Generate Prompt' to get started.":
             QApplication.clipboard().setText(prompt)
             QMessageBox.information(self, "Copied", "Prompt copied to clipboard!")
        else:
             QMessageBox.warning(self, "Warning", "Nothing to copy. Please fetch a log first.")

    def analyze_with_api(self):
        provider = self.provider_combo.currentData()
        model_name = self.model_combo.currentData()
        
        # Get correct credentials based on provider
        kwargs = {}
        if provider == 'gemini':
            kwargs['api_key'] = self.gemini_key_input.text().strip()
            if not kwargs['api_key']:
                 QMessageBox.critical(self, "Error", "Please enter your Gemini API Key in Settings.")
                 self.tabs.setCurrentIndex(4) # Settings
                 return
        elif provider == 'openai':
            kwargs['api_key'] = self.openai_key_input.text().strip()
            if not kwargs['api_key']:
                 QMessageBox.critical(self, "Error", "Please enter your OpenAI API Key in Settings.")
                 self.tabs.setCurrentIndex(4) # Settings
                 return
        elif provider == 'anthropic':
            kwargs['api_key'] = self.anthropic_key_input.text().strip()
            if not kwargs['api_key']:
                 QMessageBox.critical(self, "Error", "Please enter your Anthropic API Key in Settings.")
                 self.tabs.setCurrentIndex(4) # Settings
                 return
        elif provider == 'openai_compatible':
            kwargs['api_key'] = self.custom_key_input.text().strip()
            kwargs['base_url'] = self.custom_url_input.text().strip()
            if not kwargs['base_url']:

                 QMessageBox.critical(self, "Error", "Please enter your Custom API URL in Settings.")
                 self.tabs.setCurrentIndex(4) # Settings
                 return
        elif provider == 'ollama':
            kwargs['base_url'] = self.ollama_url_input.text().strip()
            if model_name == "__custom__":
                model_name, ok = QInputDialog.getText(self, "Custom Model", "Enter the exact name of your Ollama model:")
                if not ok or not model_name: return

        
        urls = [u.strip().strip('<>') for u in self.url_input.toPlainText().split('\n') if u.strip()]


        if not urls:
            QMessageBox.critical(self, "Error", "Please enter at least one URL.")
            return

        self.api_progress.show()
        self.api_text.setPlainText(f"Fetching and analyzing {len(urls)} logs with {provider}... Please wait.\n")
        
        self.worker = ApiWorker(urls=urls, api_key=kwargs.get('api_key'), model_name=model_name, 
                              save_dir=self.save_dir_input.text(), save_logs=self.save_logs_checkbox.isChecked(),
                              provider=provider, base_url=kwargs.get('base_url'),
                              system_prompt=self.prompt_editor.toPlainText())
        self.worker.progress.connect(self.on_api_progress)
        self.worker.progress_val.connect(self.api_progress.setValue)
        self.worker.finished.connect(self.on_api_finished)
        self.worker.start()

    def on_api_progress(self, message):
        self.api_text.append(message)

    def on_api_finished(self, result, error):
        self.api_progress.hide()
        self.api_progress.setValue(0)
        if error:
            self.api_text.append(f"\nError: {error}")
        elif result:
            footer = "\n\nThis was made by an automated tool that uses AI"
            if not result.strip().endswith(footer.strip()):
                result += footer
            # Instead of replacing, we append a separator and then the result
            # Or we set the whole thing but start with the log that was already there
            current_log = self.api_text.toPlainText()
            self.api_text.setPlainText(f"{current_log}\n{'='*40}\n\n{result}")
            # Scroll to end
            self.api_text.moveCursor(self.api_text.textCursor().MoveOperation.End)



    def run_manual_search(self):
        text = self.manual_search_input.text().strip()
        if not text:
             QMessageBox.warning(self, "Warning", "Please enter a class name or error to search.")
             return
        platform = self.search_tab_combo.currentData()
        self.open_search_url(text, platform)

    def open_search_url(self, text, platform):
        # Limit search string length
        query = text[:200]
        encoded_query = urllib.parse.quote(query)

        if platform == "forge":
            url = f"https://codesearch.neoforged.net/search?q={encoded_query}"
        elif platform == "fabric":
            url = f"https://github.com/search?q=repo%3AFabricMC%2Ffabric+OR+repo%3AFabricMC%2Ffabric-loader+{encoded_query}&type=code"
        elif platform == "mc":
            # Direct link to the specific Minecraft Source provided by the user
            url = f"https://git.merded.zip/merded/minecraft-src/search?q={encoded_query}"


        else: # google
            url = f"https://www.google.com/search?q=minecraft+{encoded_query}"



        webbrowser.open(url)

    def search_source(self, platform):
        # Get selected text from the active tab's text edit
        current_tab = self.tabs.currentIndex()
        if current_tab == 0:
            text = self.manual_text.textCursor().selectedText().strip()
            if not text:
                 text = self.manual_text.toPlainText().strip()
        elif current_tab == 2: # Paste Log
            text = self.pasted_log_text.textCursor().selectedText().strip()
            if not text:
                 text = self.pasted_log_text.toPlainText().strip()
        else:
            text = self.api_text.textCursor().selectedText().strip()
            if not text:
                 text = self.api_text.toPlainText().strip()


        if not text or len(text) < 3:
             QMessageBox.warning(self, "Warning", "Please highlight some text (a class name or error) to search.")
             return

        # Limit search string length
        query = text[:200]
        encoded_query = urllib.parse.quote(query)

        if platform == "forge":
            url = f"https://codesearch.neoforged.net/search?q={encoded_query}"
        elif platform == "fabric":
            url = f"https://github.com/search?q=repo%3AFabricMC%2Ffabric+OR+repo%3AFabricMC%2Ffabric-loader+{encoded_query}&type=code"
        elif platform == "mc":
            # Direct link to the specific Minecraft Source provided by the user
            url = f"https://git.merded.zip/merded/minecraft-src/search?q={encoded_query}"


        else: # google
            url = f"https://www.google.com/search?q=minecraft+{encoded_query}"




        webbrowser.open(url)

    def on_pasted_text_changed(self):
        # Update search count if search is active
        query = self.log_search_input.text()
        if query:
            self.update_search_count(query)

    def update_search_count(self, query):
        text = self.pasted_log_text.toPlainText()
        count = text.count(query)
        self.search_count_label.setText(f"Matches: {count}")

    def find_text_next(self):
        query = self.log_search_input.text()
        if not query:
            return
        
        res = self.pasted_log_text.find(query)
        if not res:
            # Wrap around to start
            self.pasted_log_text.moveCursor(self.pasted_log_text.textCursor().MoveOperation.Start)
            self.pasted_log_text.find(query)
        self.update_search_count(query)

    def find_text_prev(self):
        query = self.log_search_input.text()
        if not query:
            return
        
        res = self.pasted_log_text.find(query, self.pasted_log_text.FindFlag.FindBackward)
        if not res:
            # Wrap around to end
            self.pasted_log_text.moveCursor(self.pasted_log_text.textCursor().MoveOperation.End)
            self.pasted_log_text.find(query, self.pasted_log_text.FindFlag.FindBackward)
        self.update_search_count(query)

    def import_local_log(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Log File", "", "Log Files (*.log *.txt);;All Files (*)")
        if not file_path:
            return
            
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
            if len(content) < 10:
                QMessageBox.warning(self, "Warning", "The selected file is empty or too short.")
                return

            # Ask user if they want to upload to mclo.gs or just paste directly
            reply = QMessageBox.question(self, "Import Method", 
                                        "Would you like to upload this log to mclo.gs and analyze via URL (recommended for large logs) or just paste it directly?",
                                        QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel,
                                        QMessageBox.StandardButton.Open)
            
            # Open = Upload to mclo.gs, Save = Paste Directly
            if reply == QMessageBox.StandardButton.Cancel:
                return
            
            if reply == QMessageBox.StandardButton.Open: # Upload
                self.pasted_log_text.setPlainText(f"Uploading {os.path.basename(file_path)} to mclo.gs... Please wait.")
                QApplication.processEvents()
                
                raw_url = analyze_logs.upload_to_mclogs(content)
                if raw_url:
                    self.pasted_log_text.setPlainText(content)
                    self.url_input.setPlainText(raw_url)
                    QMessageBox.information(self, "Success", f"Log uploaded successfully!\n\nThe URL has been added to the top input. You can now analyze it in 'API Mode' or keep it here in 'Paste Log'.")
                else:
                    QMessageBox.critical(self, "Error", "Failed to upload log to mclo.gs. Pasting directly instead.")
                    self.pasted_log_text.setPlainText(content)
            else: # Just paste
                self.pasted_log_text.setPlainText(content)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read file: {e}")

    def import_log_from_url(self):
        url, ok = QInputDialog.getText(self, "Import from URL", "Enter mclo.gs or gnomebot.dev URL:")
        if not ok or not url:
            return
            
        self.pasted_log_text.setPlainText(f"Fetching log from {url}... Please wait.")
        QApplication.processEvents()
        
        content = analyze_logs.fetch_log(url)
        if content:
            self.pasted_log_text.setPlainText(content)
            # Also update URL input in API tab for convenience
            self.url_input.setPlainText(url)
            QMessageBox.information(self, "Success", "Log imported successfully!")
        else:
            QMessageBox.critical(self, "Error", "Failed to fetch log. Please check the URL and your connection.")
            self.pasted_log_text.clear()

    def export_pasted_log(self):
        content = self.pasted_log_text.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Warning", "Nothing to export!")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Log As", "exported_log.txt", "Text Files (*.txt);;Log Files (*.log);;All Files (*)")
        if not file_path:
            return
            
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Success", f"Log exported to {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {e}")


    def analyze_pasted_log(self):
        self._run_pasted_analysis(self.prompt_editor.toPlainText())

    def manual_scan_compatibility(self):
        url = self.manual_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Warning", "Please enter a URL first.")
            return
        
        prompt = f"{analyze_logs.SCANNER_PROMPT}\n\nHere is the log URL to scan:\n{url}\n\nThis was made by an automated tool that uses AI"

        QApplication.clipboard().setText(prompt)
        QMessageBox.information(self, "Copied", "Manual compatibility scan prompt copied to clipboard! Paste this into Gemini and provide the URL.")

    def scan_compatibility(self):
        log_content = self.pasted_log_text.toPlainText().strip()
        if not log_content:
            QMessageBox.warning(self, "Warning", "Please paste a log first.")
            return

        provider = self.provider_combo.currentData()
        model_name = self.model_combo.currentData()
        kwargs = {}

        # Get API Key / URL based on provider (similar to analyze_pasted_log)
        if provider == 'gemini':
            kwargs['api_key'] = self.gemini_key_input.text().strip()
            if not kwargs['api_key']:
                 QMessageBox.critical(self, "Error", "Please enter your Gemini API Key in Settings.")
                 self.tabs.setCurrentIndex(4)
                 return
        elif provider == 'openai':
            kwargs['api_key'] = self.openai_key_input.text().strip()
        elif provider == 'anthropic':
            kwargs['api_key'] = self.anthropic_key_input.text().strip()
        elif provider == 'ollama':
            kwargs['base_url'] = self.ollama_url_input.text().strip()
        elif provider == 'openai_compatible':
            kwargs['base_url'] = self.custom_url_input.text().strip()
            kwargs['api_key'] = self.custom_key_input.text().strip()

        if model_name == "__custom__":
             model_name, ok = QInputDialog.getText(self, "Custom Model", "Enter Model ID:")
             if not ok or not model_name: return

        self.api_progress.show()
        self.api_text.setPlainText("Scanning for compatibility issues... Please wait.\n")
        
        # We reuse ApiWorker but with the scanner prompt
        system_prompt = f"{analyze_logs.SCANNER_PROMPT}\n\nThis was made by an automated tool that uses AI"
        self.worker = ApiWorker(content=log_content, api_key=kwargs.get('api_key'), 
                               model_name=model_name, provider=provider, 
                               base_url=kwargs.get('base_url'),
                               system_prompt=system_prompt)

        self.worker.progress.connect(self.on_api_progress)
        self.worker.progress_val.connect(self.api_progress.setValue)
        self.worker.finished.connect(self.on_api_finished)

        self.worker.start()
        self.tabs.setCurrentIndex(1) # Switch to analysis tab

    def _run_pasted_analysis(self, system_prompt, title="Analyzing pasted log"):
        content = self.pasted_log_text.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Warning", "Please paste a log before analyzing.")
            return

        provider = self.provider_combo.currentData()
        model_name = self.model_combo.itemData(self.model_combo.currentIndex())
        if model_name == "__custom__":
            model_name = self.custom_model_input.text().strip() or "gemini-3.1-pro-preview"
            
        kwargs = {}
        if provider == 'gemini':
            kwargs['api_key'] = self.gemini_key_input.text().strip()
        elif provider == 'openai':
            kwargs['api_key'] = self.openai_key_input.text().strip()
        elif provider == 'anthropic':
            kwargs['api_key'] = self.anthropic_key_input.text().strip()
        elif provider == 'openai_compatible':
            kwargs['api_key'] = self.custom_key_input.text().strip()
            kwargs['base_url'] = self.custom_url_input.text().strip()
        elif provider == 'ollama':
            kwargs['base_url'] = self.ollama_url_input.text().strip()



        # Check for API key/base_url if required by provider
        required_key_providers = ['gemini', 'openai', 'anthropic', 'openai_compatible']
        if provider in required_key_providers and not kwargs.get('api_key'):

            QMessageBox.critical(self, "Error", f"Please enter your {provider.capitalize()} API Key in Settings.")
            self.tabs.setCurrentIndex(4) # Settings
            return
        
        if provider in ['ollama', 'openai_compatible'] and not kwargs.get('base_url'):
            QMessageBox.critical(self, "Error", f"Please enter your {provider.capitalize()} Base URL in Settings.")
            self.tabs.setCurrentIndex(4) # Settings
            return


        self.api_progress.show()
        self.api_text.setPlainText(f"{title} with {provider} - {model_name}... Please wait.\n")
        
        self.worker = ApiWorker(api_key=kwargs.get('api_key'), model_name=model_name, content=content,
                               provider=provider, base_url=kwargs.get('base_url'),
                               system_prompt=system_prompt)
        self.worker.progress.connect(self.on_api_progress)
        self.worker.finished.connect(self.on_api_finished)
        self.worker.start()
        self.tabs.setCurrentIndex(1) # Switch to analysis tab


    def on_provider_changed(self, index):
        provider = self.provider_combo.currentData()
        self.config_data["provider"] = provider
        self.update_model_list()
        self.save_config()

    def update_model_list(self):
        provider = self.provider_combo.currentData()
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        
        models = self.get_models_for_provider(provider)
        for model in models:
            # Add human readable labels for some
            label = model
            if model == "__custom__": label = "Custom/Other (Enter Name)"
            elif provider == "ollama": label = f"{model} (Ollama)"
            
            self.model_combo.addItem(label, model)

        # Try to restore saved model if it exists in the new list
        saved_model = self.config_data.get("model_name")
        found = False
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == saved_model:
                self.model_combo.setCurrentIndex(i)
                found = True
                break
        if not found and self.model_combo.count() > 0:
            self.model_combo.setCurrentIndex(0)
            self.config_data["model_name"] = self.model_combo.currentData()
            
        self.model_combo.blockSignals(False)


    def on_tab_changed(self, index):
        # Already handled by index but let's be safe
        tabs = ["manual", "api", "paste", "search", "settings"]
        if index < len(tabs):
             self.config_data["default_mode"] = tabs[index]
             self.save_config()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LogAnalyzerGUI()
    window.show()
    sys.exit(app.exec())
