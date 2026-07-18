"""QSS stylesheet for the application - a modern rounded look."""

APP_STYLE = """
* {
    font-family: "PingFang SC", "Microsoft YaHei", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: #2c3e50;
}

QMainWindow, QDialog, QWidget {
    background-color: #f5f7fa;
}

/* Custom title bar */
#titleBar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2c7be5, stop:1 #1a68d1);
}
#titleLabel {
    color: #ffffff;
    font-weight: 600;
}
QToolButton#titleIconBtn {
    background: transparent;
    border: none;
    padding: 6px 10px;
    border-radius: 6px;
    color: #ffffff;
    font-size: 13px;
    font-weight: 500;
    /* Gap between icon and text (icon + "项目地址" / icon + "捐赠") */
    spacing: 6px;
}
QToolButton#titleIconBtn:hover {
    background: rgba(255,255,255,0.18);
}
QToolButton#titleWinBtn {
    background: transparent;
    border: none;
    padding: 6px 10px;
    border-radius: 4px;
}
QToolButton#titleWinBtn:hover {
    background: rgba(255,255,255,0.18);
}
QToolButton#titleCloseBtn {
    background: transparent;
    border: none;
    padding: 6px 10px;
    border-radius: 4px;
}
QToolButton#titleCloseBtn:hover {
    background: #e74c3c;
}

/* Tabs */
QTabWidget::pane {
    border: none;
    background: #ffffff;
    border-radius: 10px;
    margin: 6px;
}
QTabBar::tab {
    background: transparent;
    padding: 10px 24px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    color: #6c7a89;
    font-weight: 500;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #2c7be5;
    font-weight: 600;
}
QTabBar::tab:hover:!selected {
    background: rgba(44,123,229,0.08);
    color: #2c7be5;
}

/* Buttons */
QPushButton {
    background-color: #2c7be5;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    font-weight: 500;
}
QPushButton:hover { background-color: #1a68d1; }
QPushButton:pressed { background-color: #145bb8; }
QPushButton:disabled { background-color: #b0bec5; color: #ecf0f1; }

QPushButton[flat="true"] {
    background-color: #eef2f7;
    color: #2c7be5;
}
QPushButton[flat="true"]:hover { background-color: #dee7f2; }

QPushButton[danger="true"] { background-color: #e74c3c; }
QPushButton[danger="true"]:hover { background-color: #c0392b; }

/* Inputs */
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {
    background: #ffffff;
    border: 1px solid #d5dbe0;
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: #2c7be5;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #2c7be5;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    border: 1px solid #d5dbe0;
    border-radius: 6px;
    background: #ffffff;
    padding: 4px;
    selection-background-color: #2c7be5;
    selection-color: white;
}

/* Labels */
QLabel { background: transparent; }
QLabel[title="true"] {
    font-size: 14px;
    font-weight: 600;
    color: #34495e;
}

/* Group boxes */
QGroupBox {
    border: 1px solid #e0e6ed;
    border-radius: 8px;
    margin-top: 14px;
    padding: 10px;
    background: #ffffff;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #34495e;
}

/* Lists */
QListWidget {
    background: #ffffff;
    border: 1px solid #e0e6ed;
    border-radius: 8px;
    padding: 4px;
}
QListWidget::item {
    padding: 8px 10px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background: #2c7be5;
    color: white;
}
QListWidget::item:hover:!selected {
    background: rgba(44,123,229,0.10);
}

/* Table */
QTableView, QTableWidget {
    background: #ffffff;
    border: 1px solid #e0e6ed;
    border-radius: 8px;
    gridline-color: #eef2f7;
    selection-background-color: #d4e4fb;
    selection-color: #2c3e50;
}
QHeaderView::section {
    background-color: #eef2f7;
    color: #34495e;
    padding: 6px;
    border: none;
    border-right: 1px solid #d5dbe0;
    font-weight: 600;
}

/* Status bar */
QStatusBar {
    background: #34495e;
    color: white;
}
QStatusBar QLabel { color: white; }

/* Scroll bars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #b0bec5;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #90a4ae; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 10px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #b0bec5;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #90a4ae; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* Text edit background for SQL */
QPlainTextEdit#sqlEditor {
    font-family: "JetBrains Mono", "Consolas", "Menlo", monospace;
    font-size: 13px;
    background: #fbfcfd;
}
"""
