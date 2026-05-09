from voice_role.ui.theme import COLORS, FONTS


def get_stylesheet() -> str:
    c = COLORS
    return f"""
/* Global */
QMainWindow {{
    background-color: {c["bg_primary"]};
}}
QWidget {{
    font-family: "{FONTS["body"]}";
    font-size: {FONTS["size_sm"]}pt;
    color: {c["text_primary"]};
}}

/* Buttons */
QPushButton {{
    border: 2px solid {c["gold_primary"]};
    border-radius: 6px;
    padding: 8px 20px;
    background-color: transparent;
    color: {c["gold_dark"]};
    font-weight: bold;
    font-size: {FONTS["size_sm"]}pt;
}}
QPushButton:hover {{
    background-color: {c["gold_pale"]};
    border-color: {c["gold_dark"]};
}}
QPushButton:pressed {{
    background-color: {c["gold_light"]};
}}
QPushButton:disabled {{
    border-color: {c["border"]};
    color: {c["text_secondary"]};
    background-color: {c["bg_secondary"]};
}}

QPushButton#primaryBtn {{
    background-color: {c["gold_primary"]};
    color: white;
    border: none;
    padding: 10px 28px;
    font-size: {FONTS["size_md"]}pt;
}}
QPushButton#primaryBtn:hover {{
    background-color: {c["gold_dark"]};
}}
QPushButton#primaryBtn:disabled {{
    background-color: {c["border"]};
    color: {c["text_secondary"]};
}}

/* Input */
QLineEdit, QTextEdit, QPlainTextEdit {{
    border: 2px solid {c["border"]};
    border-radius: 4px;
    padding: 6px 10px;
    background-color: white;
    font-size: {FONTS["size_sm"]}pt;
}}
QLineEdit:focus, QTextEdit:focus {{
    border-color: {c["gold_primary"]};
}}

/* ComboBox */
QComboBox {{
    border: 2px solid {c["border"]};
    border-radius: 4px;
    padding: 6px 10px;
    background-color: white;
    font-size: {FONTS["size_sm"]}pt;
}}
QComboBox:hover {{
    border-color: {c["gold_primary"]};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    border: 1px solid {c["border"]};
    background-color: white;
    selection-background-color: {c["gold_pale"]};
    selection-color: {c["text_primary"]};
}}

/* SpinBox */
QSpinBox, QDoubleSpinBox {{
    border: 2px solid {c["border"]};
    border-radius: 4px;
    padding: 6px 10px;
    background-color: white;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {c["gold_primary"]};
}}

/* ProgressBar */
QProgressBar {{
    border: none;
    border-radius: 4px;
    height: 8px;
    background-color: {c["bg_secondary"]};
    text-align: center;
    font-size: {FONTS["size_xs"]}pt;
}}
QProgressBar::chunk {{
    background-color: {c["gold_primary"]};
    border-radius: 4px;
}}

/* Table */
QTableWidget {{
    border: 1px solid {c["border"]};
    gridline-color: {c["border"]};
    background-color: white;
    alternate-background-color: {c["bg_secondary"]};
    selection-background-color: {c["gold_pale"]};
    selection-color: {c["text_primary"]};
}}
QHeaderView::section {{
    background-color: {c["gold_primary"]};
    color: white;
    padding: 6px 10px;
    border: none;
    font-weight: bold;
    font-size: {FONTS["size_sm"]}pt;
}}

/* GroupBox */
QGroupBox {{
    border: 1px solid {c["border"]};
    border-radius: 6px;
    margin-top: 12px;
    padding: 12px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {c["gold_dark"]};
}}

/* TabWidget */
QTabWidget::pane {{
    border: 1px solid {c["border"]};
    background-color: white;
}}
QTabBar::tab {{
    padding: 8px 20px;
    border: 1px solid {c["border"]};
    border-bottom: none;
    background-color: {c["bg_secondary"]};
    font-size: {FONTS["size_sm"]}pt;
}}
QTabBar::tab:selected {{
    background-color: white;
    border-bottom: 2px solid {c["gold_primary"]};
    color: {c["gold_dark"]};
    font-weight: bold;
}}
QTabBar::tab:hover {{
    background-color: {c["gold_pale"]};
}}

/* ScrollBar */
QScrollBar:vertical {{
    border: none;
    background: {c["bg_secondary"]};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {c["gold_primary"]};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* CheckBox */
QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {c["border"]};
    border-radius: 3px;
}}
QCheckBox::indicator:checked {{
    background-color: {c["gold_primary"]};
    border-color: {c["gold_primary"]};
}}

/* Label */
QLabel#titleLabel {{
    font-size: {FONTS["size_lg"]}pt;
    font-weight: bold;
    color: {c["gold_dark"]};
}}
QLabel#subtitleLabel {{
    font-size: {FONTS["size_sm"]}pt;
    color: {c["text_secondary"]};
}}
QLabel#errorLabel {{
    font-size: {FONTS["size_sm"]}pt;
    color: {c["error"]};
    font-weight: bold;
}}

/* Menu bar */
QMenuBar {{
    background-color: {c["bg_primary"]};
    border-bottom: 1px solid {c["border"]};
    padding: 2px;
}}
QMenuBar::item {{
    padding: 4px 12px;
    border-radius: 4px;
}}
QMenuBar::item:selected {{
    background-color: {c["gold_pale"]};
}}
QMenu {{
    background-color: white;
    border: 1px solid {c["border"]};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 30px 6px 16px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {c["gold_pale"]};
}}
QMenu::separator {{
    height: 1px;
    background: {c["border"]};
    margin: 4px 8px;
}}

/* StatusBar */
QStatusBar {{
    background-color: {c["bg_secondary"]};
    border-top: 1px solid {c["border"]};
    padding: 2px 8px;
    font-size: {FONTS["size_xs"]}pt;
}}
"""
