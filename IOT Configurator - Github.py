import sys
import json
import serial
import serial.tools.list_ports
import base64
import urllib.request
import tempfile
import zipfile
import os
import shutil
from packaging import version
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QComboBox, QLineEdit,
    QTabWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTextEdit, QMessageBox,
    QFileDialog, QGroupBox, QTableWidget, QHeaderView, QMenuBar, QMenu, QSizePolicy
)
from PyQt5.QtCore import QTimer, Qt, QRegExp
from PyQt5.QtGui import QColor, QIntValidator, QRegExpValidator

# Try to import cryptography for encryption
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

MB_COUNT = 128

# Encryption key for config files (must be 32 bytes)
ENCRYPTION_KEY = b'Dq0J8JhG2XeZ4Y7q1v3z0p0v3X3R5e8v2'  # 32 bytes

class UpdateChecker:
    GITHUB_REPO = "MohitPatel94/iot-configurator"  # Replace with your GitHub repo
    CURRENT_VERSION = "1.0.0"  # Update this with each release
    
    @staticmethod
    def get_latest_release_info():
        try:
            url = f"https://api.github.com/repos/{UpdateChecker.GITHUB_REPO}/releases/latest"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                return {
                    'version': data['tag_name'],
                    'url': data['html_url'],
                    'download_url': data['assets'][0]['browser_download_url'] if data['assets'] else None,
                    'body': data['body']
                }
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return None
    
    @staticmethod
    def is_update_available():
        latest = UpdateChecker.get_latest_release_info()
        if not latest:
            return False
        return version.parse(latest['version']) > version.parse(UpdateChecker.CURRENT_VERSION)
    
    @staticmethod
    def download_and_update(parent_widget):
        latest = UpdateChecker.get_latest_release_info()
        if not latest or not latest['download_url']:
            QMessageBox.warning(parent_widget, "Update Error", "Could not find download URL for the update.")
            return
        
        try:
            # Ask user for confirmation
            reply = QMessageBox.question(
                parent_widget, 
                "Update Available",
                f"Version {latest['version']} is available (you have {UpdateChecker.CURRENT_VERSION}).\n\n"
                f"Release notes:\n{latest['body']}\n\n"
                "Would you like to download and install this update?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "update.zip")
            
            # Download the update
            parent_widget.status_label.setText("Downloading update...")
            QApplication.processEvents()  # Force UI update
            urllib.request.urlretrieve(latest['download_url'], zip_path)
            
            # Extract the update
            parent_widget.status_label.setText("Extracting update...")
            QApplication.processEvents()  # Force UI update
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find the executable/script in the extracted files
            extracted_files = os.listdir(temp_dir)
            new_version_file = None
            for file in extracted_files:
                if file.endswith(".py") or file.endswith(".exe"):
                    new_version_file = os.path.join(temp_dir, file)
                    break
            
            if not new_version_file:
                raise Exception("Could not find application file in the update package")
            
            # Determine current application path
            current_path = os.path.abspath(sys.argv[0])
            backup_path = current_path + ".bak"
            
            # Create backup
            shutil.copy2(current_path, backup_path)
            
            # Replace with new version
            shutil.copy2(new_version_file, current_path)
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            QMessageBox.information(
                parent_widget,
                "Update Complete",
                f"Successfully updated to version {latest['version']}.\n"
                "The application will now restart."
            )
            
            # Restart the application
            os.execl(sys.executable, sys.executable, *sys.argv)
            
        except Exception as e:
            QMessageBox.critical(
                parent_widget,
                "Update Failed",
                f"An error occurred during update:\n{str(e)}"
            )
            parent_widget.status_label.setText("○ DISCONNECTED")

# Theme definitions (removed min-width constraints)
LIGHT_THEME = """
    QWidget {
        background-color: #f4faff;
        font-family: 'Segoe UI';
        font-size: 11pt;
    }
    QPushButton {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #00b4db, stop:1 #0083b0);
        color: white;
        border-radius: 6px;
        padding: 6px 14px;
    }
    QPushButton:hover {
        background-color: #005f7f;
    }
    QPushButton:disabled {
        background-color: #cccccc;
    }
    QLabel {
        font-weight: bold;
    }
    QLineEdit, QComboBox {
        background-color: white;
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 5px;
    }
    QLineEdit:disabled, QComboBox:disabled {
        background-color: #eeeeee;
    }
    QGroupBox {
        border: 2px solid #a0c4ff;
        border-radius: 8px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 8px;
        color: #007BFF;
        font-weight: bold;
    }
    QTableWidget {
        selection-background-color: #a0c4ff;
    }
    QLineEdit:focus, QComboBox:focus {
        border: 2px solid #0083b0;
        background-color: #f4faff;
    }
    QTableWidget QLineEdit:focus {
        border: 2px solid #0083b0;
        background-color: white;
    }
"""

DARK_THEME = """
    QWidget {
        background-color: #2d2d2d;
        color: #e0e0e0;
        font-family: 'Segoe UI';
        font-size: 11pt;
    }
    QPushButton {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #00688B, stop:1 #00465e);
        color: white;
        border-radius: 6px;
        padding: 6px 14px;
    }
    QPushButton:hover {
        background-color: #003f5c;
    }
    QPushButton:disabled {
        background-color: #555555;
    }
    QLabel {
        font-weight: bold;
        color: #e0e0e0;
    }
    QLineEdit, QComboBox {
        background-color: #3d3d3d;
        color: #e0e0e0;
        border: 1px solid #555;
        border-radius: 5px;
        padding: 5px;
    }
    QLineEdit:disabled, QComboBox:disabled {
        background-color: #333333;
    }
    QGroupBox {
        border: 2px solid #4a6580;
        border-radius: 8px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 8px;
        color: #5d9bff;
        font-weight: bold;
    }
    QTableWidget {
        background-color: #3d3d3d;
        color: #e0e0e0;
        selection-background-color: #4a6580;
        gridline-color: #555;
    }
    QHeaderView::section {
        background-color: #3a3a3a;
        color: #e0e0e0;
        padding: 4px;
        border: 1px solid #555;
    }
    QLineEdit:focus, QComboBox:focus {
        border: 2px solid #5d9bff;
        background-color: #333333;
    }
    QTableWidget QLineEdit:focus {
        border: 2px solid #5d9bff;
        background-color: #3d3d3d;
    }
"""

BLUE_THEME = """
    QWidget {
        background-color: #e6f2ff;
        font-family: 'Segoe UI';
        font-size: 11pt;
    }
    QPushButton {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #1e90ff, stop:1 #0066cc);
        color: white;
        border-radius: 6px;
        padding: 6px 14px;
    }
    QPushButton:hover {
        background-color: #0059b3;
    }
    QPushButton:disabled {
        background-color: #a3c6ff;
    }
    QLabel {
        font-weight: bold;
        color: #003366;
    }
    QLineEdit, QComboBox {
        background-color: white;
        border: 1px solid #99c2ff;
        border-radius: 5px;
        padding: 5px;
    }
    QLineEdit:disabled, QComboBox:disabled {
        background-color: #e6f0ff;
    }
    QGroupBox {
        border: 2px solid #4d94ff;
        border-radius: 8px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 8px;
        color: #0066cc;
        font-weight: bold;
    }
    QTableWidget {
        background-color: #f0f7ff;
        selection-background-color: #99c2ff;
    }
    QLineEdit:focus, QComboBox:focus {
        border: 2px solid #0066cc;
        background-color: #e6f2ff;
    }
    QTableWidget QLineEdit:focus {
        border: 2px solid #0066cc;
        background-color: white;
    }
"""

class NameValidator(QRegExpValidator):
    def __init__(self, max_bytes, parent=None):
        super().__init__(QRegExp(".*"), parent)
        self.max_bytes = max_bytes

    def validate(self, text, pos):
        state, text, pos = super().validate(text, pos)
        if len(text.encode('utf-8')) > self.max_bytes:
            return (QRegExpValidator.Invalid, text, pos)
        return (state, text, pos)

class USBConfigTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"IOT Configurator v{UpdateChecker.CURRENT_VERSION}")
        self.setMinimumSize(1100, 700)
        self.serial = None
        self.fields = {}
        self.mb_table = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_from_serial)
        self.port_refresh = QTimer()
        self.port_refresh.timeout.connect(self.refresh_ports)
        self.port_refresh.start(2000)
        self.init_ui()
        self.setStyleSheet(LIGHT_THEME)

    def init_ui(self):
        # Create menu bar
        menubar = QMenuBar()
        theme_menu = menubar.addMenu("Theme")
        theme_menu.addAction("Light", lambda: self.set_theme("light"))
        theme_menu.addAction("Dark", lambda: self.set_theme("dark"))
        theme_menu.addAction("Blue", lambda: self.set_theme("blue"))
        
        # Help menu with update check
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("Check for Updates", self.check_for_updates)
        help_menu.addAction("About", self.show_about)
        
        # Top controls
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(5, 5, 5, 5)
        top_layout.setSpacing(10)
        
        # Add menu bar to main layout
        main_layout = QVBoxLayout()
        main_layout.setMenuBar(menubar)
        
        # Status label
        self.status_label = QLabel("○ DISCONNECTED")
        self.status_label.setStyleSheet("font-weight: bold; color: red")
        self.status_label.setFixedSize(160, 30)
        top_layout.addWidget(self.status_label)
        
        # Port combo - strictly enforce 120px width
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(140)
        self.port_combo.setMaximumWidth(140)
        self.port_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_layout.addWidget(self.port_combo)
        
        # Connect button - strictly enforce 160px width
        self.connect_btn = QPushButton("CONNECT")
        self.connect_btn.setMinimumWidth(140)
        self.connect_btn.setMaximumWidth(140)
        self.connect_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_layout.addWidget(self.connect_btn)
        
        # Other buttons with fixed 80px width
        btn_width = 100
        self.read_btn = QPushButton("READ")
        self.read_btn.setFixedWidth(btn_width)
        self.read_btn.setVisible(False)
        top_layout.addWidget(self.read_btn)
        
        self.write_btn = QPushButton("WRITE")
        self.write_btn.setFixedWidth(btn_width)
        self.write_btn.setVisible(False)
        self.write_btn.setEnabled(False)
        top_layout.addWidget(self.write_btn)
        
        self.reset_btn = QPushButton("CLEAR")
        self.reset_btn.setFixedWidth(btn_width)
        self.reset_btn.setVisible(False)
        top_layout.addWidget(self.reset_btn)
        
        self.save_btn = QPushButton("SAVE")
        self.save_btn.setFixedWidth(btn_width)
        self.save_btn.setVisible(False)
        self.save_btn.setEnabled(False)
        top_layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton("LOAD")
        self.load_btn.setFixedWidth(btn_width)
        self.load_btn.setVisible(False)
        top_layout.addWidget(self.load_btn)
        
        # Add stretch to push buttons to the left
        top_layout.addStretch()
        
        # Tabs
        self.tabs = QTabWidget()
        self.set_inactive_tab_style()
        self.init_tabs()
        self.tabs.setEnabled(False)
        self.tabs.currentChanged.connect(self.check_fields_for_data)

        # Main layout
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

        # Connections
        self.connect_btn.clicked.connect(self.toggle_serial)
        self.read_btn.clicked.connect(self.read_current_tab)
        self.write_btn.clicked.connect(self.write_current_tab)
        self.reset_btn.clicked.connect(self.clear_gui_fields)
        self.save_btn.clicked.connect(self.save_config)
        self.load_btn.clicked.connect(self.load_config)

        self.refresh_ports()

    def check_for_updates(self):
        if UpdateChecker.is_update_available():
            UpdateChecker.download_and_update(self)
        else:
            QMessageBox.information(
                self,
                "No Updates",
                f"You are running the latest version ({UpdateChecker.CURRENT_VERSION})."
            )

    def show_about(self):
        QMessageBox.about(
            self,
            "About IOT Configurator",
            f"IOT Configurator v{UpdateChecker.CURRENT_VERSION}\n\n"
            "A tool for configuring IoT devices via USB serial connection.\n\n"
            "GitHub Repository:\n"
            f"https://github.com/{UpdateChecker.GITHUB_REPO}"
        )

    def set_theme(self, theme_name):
        if theme_name == "dark":
            self.setStyleSheet(DARK_THEME)
        elif theme_name == "blue":
            self.setStyleSheet(BLUE_THEME)
        else:
            self.setStyleSheet(LIGHT_THEME)

    def set_active_tab_style(self):
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #a0c4ff;
                border-radius: 5px;
                margin-top: 5px;
            }
            QTabBar::tab {
                background: #e0e0e0;
                color: #555;
                padding: 8px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: #0083b0;
                color: white;
                border-bottom: 2px solid #005f7f;
            }
            QTabBar::tab:hover {
                background: #a0c4ff;
            }
        """)

    def set_inactive_tab_style(self):
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #a0c4ff;
                border-radius: 5px;
                margin-top: 5px;
            }
            QTabBar::tab {
                background: #e0e0e0;
                color: #999;
                padding: 8px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: #e0e0e0;
                color: #999;
                border-bottom: 2px solid #ccc;
            }
            QTabBar::tab:hover {
                background: #f0f0f0;
            }
        """)

    def init_tabs(self):
        # Device Config Tab
        self.config_tab = QWidget()
        hbox = QHBoxLayout()

        # Device Group
        dev_group = QGroupBox("DEVICE")
        dev_form = QFormLayout()
        
        self.fields["SSID"] = QLineEdit()
        self.fields["SSID"].setMaxLength(32)
        self.fields["SSID"].textChanged.connect(self.check_fields_for_data)
        dev_form.addRow("WiFi Name:", self.fields["SSID"])
        
        self.fields["PASS"] = QLineEdit()
        self.fields["PASS"].setMaxLength(32)
        self.fields["PASS"].textChanged.connect(self.check_fields_for_data)
        dev_form.addRow("WiFi Password:", self.fields["PASS"])
        
        self.fields["SiteName"] = QLineEdit()
        self.fields["SiteName"].setMaxLength(16)
        self.fields["SiteName"].textChanged.connect(self.check_fields_for_data)
        dev_form.addRow("Site Name:", self.fields["SiteName"])
        
        self.fields["PanelName"] = QLineEdit()
        self.fields["PanelName"].setMaxLength(16)
        self.fields["PanelName"].textChanged.connect(self.check_fields_for_data)
        dev_form.addRow("Panel Name:", self.fields["PanelName"])
        
        self.fields["Interval"] = QLineEdit()
        self.fields["Interval"].setValidator(QIntValidator(1, 86400))
        self.fields["Interval"].textChanged.connect(self.check_fields_for_data)
        dev_form.addRow("Transmit Time (s):", self.fields["Interval"])
        
        dev_group.setLayout(dev_form)

        # Modbus Group
        modbus_group = QGroupBox("MODBUS")
        mod_form = QFormLayout()
        
        self.fields["BaudRate"] = QComboBox()
        self.fields["BaudRate"].addItems(["9600", "19200", "38400", "57600", "115200"])
        self.fields["BaudRate"].currentIndexChanged.connect(self.check_fields_for_data)
        mod_form.addRow("Baud Rate:", self.fields["BaudRate"])
        
        self.fields["StopBit"] = QComboBox()
        self.fields["StopBit"].addItems(["1", "2"])
        self.fields["StopBit"].currentIndexChanged.connect(self.check_fields_for_data)
        mod_form.addRow("Stop Bit:", self.fields["StopBit"])
        
        self.fields["Parity"] = QComboBox()
        self.fields["Parity"].addItems(["None", "Odd", "Even"])
        self.fields["Parity"].currentIndexChanged.connect(self.check_fields_for_data)
        mod_form.addRow("Parity:", self.fields["Parity"])
        
        modbus_group.setLayout(mod_form)

        # MQTT Group (without Client ID)
        mqtt_group = QGroupBox("MQTT")
        mqtt_form = QFormLayout()
        
        self.fields["IP"] = QLineEdit()
        self.fields["IP"].setMaxLength(32)
        self.fields["IP"].textChanged.connect(self.check_fields_for_data)
        mqtt_form.addRow("IP Address:", self.fields["IP"])
        
        self.fields["Port"] = QLineEdit()
        self.fields["Port"].setValidator(QIntValidator(0, 65535))
        self.fields["Port"].textChanged.connect(self.check_fields_for_data)
        mqtt_form.addRow("Port:", self.fields["Port"])
        
        self.fields["mqttUser"] = QLineEdit()
        self.fields["mqttUser"].setMaxLength(32)
        self.fields["mqttUser"].textChanged.connect(self.check_fields_for_data)
        mqtt_form.addRow("Username:", self.fields["mqttUser"])
        
        self.fields["mqttPass"] = QLineEdit()
        self.fields["mqttPass"].setMaxLength(32)
        self.fields["mqttPass"].textChanged.connect(self.check_fields_for_data)
        mqtt_form.addRow("Password:", self.fields["mqttPass"])
        
        self.fields["PubTopic"] = QLineEdit()
        self.fields["PubTopic"].setMaxLength(32)
        self.fields["PubTopic"].textChanged.connect(self.check_fields_for_data)
        mqtt_form.addRow("Publish Topic:", self.fields["PubTopic"])
        
        self.fields["SubTopic"] = QLineEdit()
        self.fields["SubTopic"].setMaxLength(32)
        self.fields["SubTopic"].textChanged.connect(self.check_fields_for_data)
        mqtt_form.addRow("Subscribe Topic:", self.fields["SubTopic"])
        
        mqtt_group.setLayout(mqtt_form)

        hbox.addWidget(dev_group)
        hbox.addWidget(modbus_group)
        hbox.addWidget(mqtt_group)
        self.config_tab.setLayout(hbox)
        self.tabs.addTab(self.config_tab, "DEVICE CONFIGURATION")

        # Modbus Registers Tab
        self.mb_tab = QWidget()
        vbox = QVBoxLayout()
        self.mb_table = QTableWidget(MB_COUNT, 5)
        self.mb_table.setHorizontalHeaderLabels(["Slave ID", "JSON Name", "Read Address", "Function", "Bytes"])
        self.mb_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Create validators
        slave_validator = QIntValidator(0, 247, self)
        address_validator = QIntValidator(0, 65535, self)
        name_validator = NameValidator(11, self)

        for row in range(MB_COUNT):
            # SlaveID (0-247)
            slave_edit = QLineEdit()
            slave_edit.setValidator(slave_validator)
            slave_edit.setText("0")
            self.mb_table.setCellWidget(row, 0, slave_edit)

            # Name (max 11 bytes)
            name_edit = QLineEdit()
            name_edit.setValidator(name_validator)
            name_edit.textChanged.connect(self.check_fields_for_data)
            self.mb_table.setCellWidget(row, 1, name_edit)

            # Address (0-65535)
            addr_edit = QLineEdit()
            addr_edit.setValidator(address_validator)
            addr_edit.textChanged.connect(self.check_fields_for_data)
            self.mb_table.setCellWidget(row, 2, addr_edit)

            # Function and Bytes (dropdowns)
            func_combo = self.function_dropdown()
            func_combo.currentIndexChanged.connect(self.check_fields_for_data)
            self.mb_table.setCellWidget(row, 3, func_combo)
            
            bytes_combo = self.bytes_dropdown()
            bytes_combo.currentIndexChanged.connect(self.check_fields_for_data)
            self.mb_table.setCellWidget(row, 4, bytes_combo)

        vbox.addWidget(self.mb_table)
        self.mb_tab.setLayout(vbox)
        self.tabs.addTab(self.mb_tab, "MODBUS REGISTERS")

    def function_dropdown(self):
        combo = QComboBox()
        combo.addItems(["Coils", "Discrete Inputs", "Holding Registers", "Input Registers"])
        return combo

    def bytes_dropdown(self):
        combo = QComboBox()
        combo.addItems(["1", "2", "3", "4"])  # Now supports 1-4 bytes
        return combo

    def refresh_ports(self):
        current = self.port_combo.currentText()
        self.port_combo.blockSignals(True)
        self.port_combo.clear()
        
        ports = serial.tools.list_ports.comports()
        
        for p in ports:
            # Check using multiple criteria to identify STM32 CDC ports
            is_stm32_cdc = (
                # Check VID/PID pairs (hex or decimal)
                (hasattr(p, 'vid') and hasattr(p, 'pid') and 
                 ((p.vid, p.pid) in [(0x0483, 0x5740), (0x0483, 0xDF11), (0x0483, 0x3748)] or
                  (hex(p.vid)[2:].lower(), hex(p.pid)[2:].lower()) in [('483', '5740'), ('483', 'df11'), ('483', '3748')])) or
                # Check description
                (p.description and 
                 ("STM32" in p.description.upper() and "CDC" in p.description.upper())) or
                # Check manufacturer
                (hasattr(p, 'manufacturer') and p.manufacturer and 
                 "STMicroelectronics" in p.manufacturer)
            )
            
            if is_stm32_cdc:
                self.port_combo.addItem(p.device, userData=p)  # Store port info in userData
        
        if current in [self.port_combo.itemText(i) for i in range(self.port_combo.count())]:
            self.port_combo.setCurrentText(current)
        self.port_combo.blockSignals(False)

    def toggle_serial(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.serial = None
            self.timer.stop()
            self.status_label.setText("○ DISCONNECTED")
            self.status_label.setStyleSheet("color: red; font-weight: bold")
            self.connect_btn.setText("CONNECT")
            self.tabs.setEnabled(False)
            self.set_inactive_tab_style()
            
            # Hide action buttons when disconnected
            self.read_btn.setVisible(False)
            self.write_btn.setVisible(False)
            self.reset_btn.setVisible(False)
            self.save_btn.setVisible(False)
            self.load_btn.setVisible(False)
        else:
            try:
                self.serial = serial.Serial(self.port_combo.currentText(), 115200, timeout=0.1)
                self.timer.start(100)
                self.status_label.setText("● CONNECTED")
                self.status_label.setStyleSheet("color: green; font-weight: bold")
                self.connect_btn.setText("DISCONNECT")
                self.tabs.setEnabled(True)
                self.set_active_tab_style()
                
                # Show action buttons when connected
                self.read_btn.setVisible(True)
                self.write_btn.setVisible(True)
                self.reset_btn.setVisible(True)
                self.save_btn.setVisible(True)
                self.load_btn.setVisible(True)
                
                # Check initial state
                self.check_fields_for_data()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                self.tabs.setEnabled(False)

    def check_fields_for_data(self):
        """Enable write/save buttons only if there's data in any field"""
        current_tab = self.tabs.currentIndex()
        has_data = False
        
        if current_tab == 0:  # Device Config tab
            for widget in self.fields.values():
                if isinstance(widget, QLineEdit) and widget.text().strip():
                    has_data = True
                    break
                elif isinstance(widget, QComboBox) and widget.currentIndex() > 0:
                    has_data = True
                    break
        else:  # Modbus tab
            for row in range(MB_COUNT):
                if (self.mb_table.cellWidget(row, 1).text().strip() or  # Name
                    self.mb_table.cellWidget(row, 2).text().strip()):   # Address
                    has_data = True
                    break
        
        self.write_btn.setEnabled(has_data)
        self.save_btn.setEnabled(has_data)

    def read_current_tab(self):
        if not self.serial or not self.serial.is_open:
            return
        tab = self.tabs.currentIndex()
        cmd = {"DataType": 1} if tab == 0 else {"DataType": 3}
        self.serial.write((json.dumps(cmd) + "\n").encode())

    def write_current_tab(self):
        if not self.serial or not self.serial.is_open:
            return
        if self.tabs.currentIndex() == 0:
            self.send_config_json()
        else:
            self.send_modbus_json()

    def read_from_serial(self):
        if self.serial and self.serial.in_waiting:
            try:
                line = self.serial.readline().decode(errors='ignore').strip()
                if not line: 
                    return
                    
                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)
                        if data.get("DataType") == 3:
                            self.load_modbus_table(data)
                        else:
                            self.update_fields(data)
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                pass

    def update_fields(self, data):
        for key, widget in self.fields.items():
            if key not in data:
                continue
            val = data[key]
            if isinstance(widget, QLineEdit):
                widget.setText(str(val))
            elif isinstance(widget, QComboBox):
                if key == "StopBit":
                    val = "1" if int(val) == 0 else "2"
                elif key == "Parity":
                    val = {0: "None", 1536: "Odd", 1024: "Even"}.get(int(val), "None")
                idx = widget.findText(str(val))
                if idx >= 0:
                    widget.setCurrentIndex(idx)
        
        # After updating fields, check if we should enable write/save
        self.check_fields_for_data()

    def clear_gui_fields(self):
        current_tab = self.tabs.currentIndex()
        
        if current_tab == 0:
            for w in self.fields.values():
                if isinstance(w, QLineEdit):
                    w.clear()
                elif isinstance(w, QComboBox):
                    w.setCurrentIndex(0)
        elif current_tab == 1:
            for row in range(MB_COUNT):
                self.mb_table.cellWidget(row, 0).setText("0")
                self.mb_table.cellWidget(row, 1).setText("")
                self.mb_table.cellWidget(row, 2).setText("")
                self.mb_table.cellWidget(row, 3).setCurrentIndex(0)
                self.mb_table.cellWidget(row, 4).setCurrentIndex(0)
        
        # After clearing, disable write/save buttons
        self.write_btn.setEnabled(False)
        self.save_btn.setEnabled(False)

    def load_modbus_table(self, data):
        for row in range(MB_COUNT):
            self.mb_table.cellWidget(row, 0).setText("0")
            self.mb_table.cellWidget(row, 1).setText("")
            self.mb_table.cellWidget(row, 2).setText("")
            self.mb_table.cellWidget(row, 3).setCurrentIndex(0)
            self.mb_table.cellWidget(row, 4).setCurrentIndex(0)
        
        count = min(len(data.get("Name", [])), MB_COUNT)
        for i in range(count):
            self.mb_table.cellWidget(i, 0).setText(str(data["SlaveID"][i]))
            self.mb_table.cellWidget(i, 1).setText(data["Name"][i][:11])
            self.mb_table.cellWidget(i, 2).setText(str(data["Address"][i]))
            self.mb_table.cellWidget(i, 3).setCurrentIndex(int(data["Function"][i])-1)
            
            # Handle byte selection (1-4)
            bytes_val = data["Bytes"][i] if i < len(data.get("Bytes", [])) else 1
            byte_index = max(0, min(3, bytes_val - 1))  # Ensure it's between 0-3 (for 1-4 bytes)
            self.mb_table.cellWidget(i, 4).setCurrentIndex(byte_index)
        
        # After loading data, check if we should enable write/save
        self.check_fields_for_data()

    def send_config_json(self):
        config = {"DataType": 2}
        for key, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                config[key] = widget.text()
            elif isinstance(widget, QComboBox):
                if key == "StopBit":
                    config[key] = 0 if widget.currentText() == "1" else 8192
                elif key == "Parity":
                    config[key] = {"None": 0, "Odd": 1536, "Even": 1024}.get(widget.currentText(), 0)
                else:
                    config[key] = int(widget.currentText())
        try:
            config["Interval"] = int(self.fields["Interval"].text())
        except:
            QMessageBox.critical(self, "Error", "Invalid Interval value")
            return
        json_str = json.dumps(config)
        for i in range(0, len(json_str), 64):
            self.serial.write(json_str[i:i+64].encode())
        self.serial.write(b"\n")

    def send_modbus_json(self):
        data = {"DataType": 4, "Name": [], "Address": [], "Function": [], "SlaveID": [], "Bytes": []}
        for row in range(MB_COUNT):
            slave_edit = self.mb_table.cellWidget(row, 0)
            name_edit = self.mb_table.cellWidget(row, 1)
            addr_edit = self.mb_table.cellWidget(row, 2)
            
            name = name_edit.text().strip()
            if not name:
                continue

            try:
                data["SlaveID"].append(int(slave_edit.text()))
                data["Name"].append(name)
                data["Address"].append(int(addr_edit.text()))
                data["Function"].append(
                    ["Coils", "Discrete Inputs", "Holding Registers", "Input Registers"].index(
                        self.mb_table.cellWidget(row, 3).currentText()
                    ) + 1
                )
                # Handle 1-4 bytes selection
                byte_selection = int(self.mb_table.cellWidget(row, 4).currentText())
                if byte_selection < 1 or byte_selection > 4:
                    raise ValueError("Bytes must be between 1 and 4")
                data["Bytes"].append(byte_selection)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Row {row+1}: {str(e)}")
                return

        json_str = json.dumps(data)
        for i in range(0, len(json_str), 64):
            self.serial.write(json_str[i:i+64].encode())
        self.serial.write(b"\n")

    def save_config(self):
        tab = self.tabs.currentIndex()
        data = {}
        if tab == 0:
            for key, widget in self.fields.items():
                if isinstance(widget, QLineEdit):
                    data[key] = widget.text()
                elif isinstance(widget, QComboBox):
                    if key == "StopBit":
                        data[key] = 0 if widget.currentText() == "1" else 8192
                    elif key == "Parity":
                        data[key] = {"None": 0, "Odd": 1536, "Even": 1024}.get(widget.currentText(), 0)
                    else:
                        data[key] = int(widget.currentText())
            try:
                data["Interval"] = int(self.fields["Interval"].text())
            except:
                QMessageBox.critical(self, "Error", "Invalid Interval value")
                return
            
            fname, _ = QFileDialog.getSaveFileName(
                self, "Save Device Configuration", "", 
                "Device Config Files (*.cfg)"
            )
        else:
            data = {"Name": [], "Address": [], "Function": [], "SlaveID": [], "Bytes": []}
            for row in range(MB_COUNT):
                name_edit = self.mb_table.cellWidget(row, 1)
                name = name_edit.text().strip()
                if not name:
                    continue
                try:
                    data["Name"].append(name)
                    data["Address"].append(int(self.mb_table.cellWidget(row, 2).text()))
                    data["SlaveID"].append(int(self.mb_table.cellWidget(row, 0).text()))
                    data["Function"].append(
                        ["Coils", "Discrete Inputs", "Holding Registers", "Input Registers"].index(
                            self.mb_table.cellWidget(row, 3).currentText()
                        ) + 1
                    )
                    # Save the byte selection (1-4)
                    byte_selection = int(self.mb_table.cellWidget(row, 4).currentText())
                    if byte_selection < 1 or byte_selection > 4:
                        raise ValueError("Bytes must be between 1 and 4")
                    data["Bytes"].append(byte_selection)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Invalid data in row {row+1}: {str(e)}")
                    return
            
            fname, _ = QFileDialog.getSaveFileName(
                self, "Save Modbus Settings", "", 
                "Modbus Setting Files (*.mb)"
            )

        if not fname:
            return
            
        if tab == 0 and not fname.endswith('.cfg'):
            fname += '.cfg'
        elif tab == 1 and not fname.endswith('.mb'):
            fname += '.mb'
            
        try:
            json_data = json.dumps(data).encode()
            
            if CRYPTO_AVAILABLE:
                try:
                    fernet = Fernet(ENCRYPTION_KEY)
                    encrypted = fernet.encrypt(json_data)
                    encoded = base64.b64encode(encrypted).decode()
                except:
                    encoded = base64.b64encode(json_data).decode()
            else:
                encoded = base64.b64encode(json_data).decode()
                
            with open(fname, "w") as f:
                f.write(encoded)
            QMessageBox.information(self, "Success", f"Configuration saved to {fname}")
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save configuration:\n{str(e)}")

    def load_config(self):
        tab = self.tabs.currentIndex()
        if tab == 0:
            filter = "Device Config Files (*.cfg)"
        else:
            filter = "Modbus Setting Files (*.mb)"
            
        fname, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "", 
            f"{filter};;All Files (*)"
        )
        
        if not fname:
            return
            
        try:
            with open(fname, "r") as f:
                encoded = f.read().strip()
                
            try:
                decoded = base64.b64decode(encoded)
            except:
                with open(fname, "r") as f:
                    config = json.load(f)
                if tab == 0:
                    self.update_fields(config)
                else:
                    self.load_modbus_table(config)
                return
                
            if CRYPTO_AVAILABLE:
                try:
                    fernet = Fernet(ENCRYPTION_KEY)
                    decrypted = fernet.decrypt(decoded)
                    config = json.loads(decrypted.decode())
                except:
                    config = json.loads(decoded.decode())
            else:
                config = json.loads(decoded.decode())
                
            if tab == 0:
                self.update_fields(config)
            else:
                self.load_modbus_table(config)
                
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load configuration:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = USBConfigTool()
    win.show()
    sys.exit(app.exec_())