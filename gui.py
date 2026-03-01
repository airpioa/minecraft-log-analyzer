import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTabWidget, QTextEdit, 
    QFileDialog, QMessageBox, QCheckBox, QProgressBar, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import analyze_logs

CONFIG_FILE = "config.json"

class ApiWorker(QThread):
    finished = pyqtSignal(str, str) # result, error
    progress = pyqtSignal(str)
    
    def __init__(self, urls, api_key, model_name, save_dir, save_logs):
        super().__init__()
        self.urls = urls
        self.api_key = api_key
        self.model_name = model_name
        self.save_dir = save_dir
        self.save_logs = save_logs
        
    def run(self):
        try:
            all_results = []
            
            for url in self.urls:
                self.progress.emit(f"Fetching log from {url}...")
                log_content = analyze_logs.fetch_log(url)
                
                if not log_content:
                    all_results.append(f"--- Analysis for {url} ---\nFailed to fetch log.\n")
                    continue
                    
                if self.save_logs:
                    url_part = url.rstrip('/').split('/')[-1]
                    safe_name = analyze_logs.re.sub(r'[^a-zA-Z0-9_-]', '_', url_part)
                    filename = f"log_{safe_name}.txt"
                    save_path = os.path.join(self.save_dir, filename)
                    try:
                        with open(save_path, "w", encoding="utf-8") as f:
                            f.write(log_content)
                    except Exception as e:
                        print(f"Thread save error: {e}")
                        
                self.progress.emit(f"Analyzing log from {url}...")
                analysis, error = analyze_logs.analyze_log(log_content, api_key=self.api_key, model_name=self.model_name)
                if analysis:
                    all_results.append(f"--- Analysis for {url} ---\n{analysis}\n")
                elif error:
                    all_results.append(f"--- Analysis for {url} ---\n{error}\n")
                else:
                    all_results.append(f"--- Analysis for {url} ---\nFailed to generate analysis.\n")
                    
            self.finished.emit("\n".join(all_results), "")
        except Exception as e:
            self.finished.emit("", str(e))


class LogAnalyzerGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Minecraft Log Analyzer")
        self.resize(800, 600)
        
        self.config_data = {
            "api_key": "",
            "model_name": "gemini-3.1-pro-preview",
            "save_dir": os.getcwd(),
            "default_mode": "manual",
            "save_logs": True
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
        
        self.tabs.addTab(manual_tab, "Manual Mode (Default)")

        # -- API Mode Tab --
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)
        
        # API Key Row
        api_controls = QHBoxLayout()
        api_controls.addWidget(QLabel("Gemini API Key:"))
        self.api_key_input = QLineEdit(self.config_data.get("api_key", ""))
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.textChanged.connect(self.on_config_change)
        api_controls.addWidget(self.api_key_input)
        
        analyze_btn = QPushButton("Analyze Logs with AI")
        analyze_btn.clicked.connect(self.analyze_with_api)
        api_controls.addWidget(analyze_btn)
        api_controls.addStretch()
        api_layout.addLayout(api_controls)
        
        # Model Selection Row
        model_controls = QHBoxLayout()
        model_controls.addWidget(QLabel("AI Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItem("Gemini 3.1 Pro Preview (Recommended)", "gemini-3.1-pro-preview")
        self.model_combo.addItem("Gemini 3 Pro Preview", "gemini-3-pro-preview")
        self.model_combo.addItem("Gemini 2.5 Pro", "gemini-2.5-pro")
        self.model_combo.addItem("Gemini 2.5 Flash", "gemini-2.5-flash")
        self.model_combo.addItem("Gemini 2.0 Flash", "gemini-2.0-flash")
        
        # Set saved or default selection
        saved_model = self.config_data.get("model_name", "gemini-3.1-pro-preview")
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == saved_model:
                self.model_combo.setCurrentIndex(i)
                break
                
        self.model_combo.currentIndexChanged.connect(self.on_config_change)
        model_controls.addWidget(self.model_combo)
        model_controls.addStretch()
        api_layout.addLayout(model_controls)
        
        self.api_progress = QProgressBar()
        self.api_progress.setRange(0, 0) # Indeterminate mode
        self.api_progress.hide()
        api_layout.addWidget(self.api_progress)
        
        self.api_text = QTextEdit()
        self.api_text.setPlainText("Results from Gemini API will appear here.")
        api_layout.addWidget(self.api_text)
        
        self.tabs.addTab(api_tab, "API Mode")
        
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
        
        settings_layout.addWidget(QLabel("(API Key is managed in the API Mode tab)"))
        settings_layout.addStretch()
        
        self.tabs.addTab(settings_tab, "Settings")
        
        # Set default tab
        if self.config_data.get("default_mode") == "api":
            self.tabs.setCurrentIndex(1)
        else:
            self.tabs.setCurrentIndex(0)
            
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        if index == 0:
            self.config_data["default_mode"] = "manual"
        elif index == 1:
            self.config_data["default_mode"] = "api"
        self.save_config()

    def on_config_change(self):
        self.config_data["api_key"] = self.api_key_input.text()
        self.config_data["model_name"] = self.model_combo.currentData()
        self.config_data["save_dir"] = self.save_dir_input.text()
        self.config_data["save_logs"] = self.save_logs_checkbox.isChecked()
        self.save_config()

    def browse_save_dir(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select Save Directory", self.save_dir_input.text())
        if dir_name:
            self.save_dir_input.setText(dir_name)

    def fetch_and_save_logs(self):
        urls = [u.strip() for u in self.url_input.toPlainText().split('\n') if u.strip()]
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
            prompt = f"{analyze_logs.SYSTEM_PROMPT}\n\nI have attached the required log files. Please analyze them based on the strict format specified above."
            self.manual_text.setPlainText(prompt)
            QMessageBox.information(self, "Success", f"{len(saved_paths)} log(s) fetched, saved, and prompt generated!\n\n1. Upload the files listed in 'Saved Log Paths' to Gemini.\n2. Click 'Copy Prompt' and paste the instructions.")


    def copy_prompt(self):
        prompt = self.manual_text.toPlainText().strip()
        if prompt and prompt != "Enter a URL and click 'Fetch Log & Generate Prompt' to get started.":
             QApplication.clipboard().setText(prompt)
             QMessageBox.information(self, "Copied", "Prompt copied to clipboard!")
        else:
             QMessageBox.warning(self, "Warning", "Nothing to copy. Please fetch a log first.")

    def analyze_with_api(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.critical(self, "Error", "Please enter your Gemini API Key in the field above.")
            return
            
        urls = [u.strip() for u in self.url_input.toPlainText().split('\n') if u.strip()]
        if not urls:
            QMessageBox.critical(self, "Error", "Please enter at least one URL.")
            return

        self.api_progress.show()
        self.api_text.setPlainText(f"Fetching and analyzing {len(urls)} logs... Please wait.\n")
        
        selected_model = self.model_combo.currentData()
        self.worker = ApiWorker(urls, api_key, selected_model, self.save_dir_input.text(), self.save_logs_checkbox.isChecked())
        self.worker.progress.connect(self.on_api_progress)
        self.worker.finished.connect(self.on_api_finished)
        self.worker.start()

    def on_api_progress(self, message):
        self.api_text.append(message)

    def on_api_finished(self, result, error):
        self.api_progress.hide()
        if error:
            self.api_text.setPlainText(f"Error: {error}")
        elif result:
            self.api_text.setPlainText(result)
        else:
            self.api_text.setPlainText("An unknown error occurred during analysis.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LogAnalyzerGUI()
    window.show()
    sys.exit(app.exec())
