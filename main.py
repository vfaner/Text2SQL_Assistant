"""
Text2SQL Assistant - Main entry point.
"""
import sys
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox

from app.main_window import MainWindow
from app.styles import APP_STYLE


def excepthook(exc_type, exc_value, exc_tb):
    """Global exception handler so the UI doesn't die silently."""
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    sys.stderr.write(msg)
    try:
        QMessageBox.critical(None, "未捕获的异常", msg)
    except Exception:
        pass


def main():
    sys.excepthook = excepthook
    app = QApplication(sys.argv)
    app.setApplicationName("Text2SQL Assistant")
    app.setStyleSheet(APP_STYLE)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
