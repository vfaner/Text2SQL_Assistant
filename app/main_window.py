"""Main application window - hosts the three pages."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QLabel, QMainWindow, QStatusBar, QTabWidget, QWidget, QVBoxLayout,
)

from .config import ConfigManager
from .pages_ai import AIConfigPage
from .pages_about import AboutPage
from .pages_data_source import DataSourcePage
from .pages_text2sql import Text2SQLPage
from .title_bar import TitleBar
from . import toast as toast_mod


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Text-to-SQL 智能查询工具")
        self.resize(1280, 860)

        # Frameless: custom title bar handles minimize/maximize/close and dragging
        self.setWindowFlag(Qt.FramelessWindowHint, True)

        self.cfg = ConfigManager()

        # Toast/notification manager - pages find it via parent chain
        self._notifier = toast_mod.install(self)

        self._build_ui()
        self._wire_signals()

        # Center the window on the primary screen at startup
        self._center_on_screen()

        # Trigger initial refreshes
        self.text2sql_page.refresh_data_sources()
        self._refresh_status()

    def _center_on_screen(self) -> None:
        """Position this window at the center of the screen it's opening on."""
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return
        # availableGeometry() excludes the OS menu bar / dock, which is what we want.
        avail = screen.availableGeometry()
        geo = self.frameGeometry()
        geo.moveCenter(avail.center())
        self.move(geo.topLeft())

    def _build_ui(self) -> None:
        # Container that holds title bar + content
        container = QWidget()
        container.setObjectName("windowContainer")
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Custom title bar
        self.title_bar = TitleBar(self, self.windowTitle())
        self.title_bar.minimize_requested.connect(self.showMinimized)
        self.title_bar.maximize_toggle_requested.connect(self._toggle_max_restore)
        self.title_bar.close_requested.connect(self.close)
        outer.addWidget(self.title_bar)

        # Central: tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.North)

        self.text2sql_page = Text2SQLPage(self.cfg)
        self.data_source_page = DataSourcePage(self.cfg)
        self.ai_page = AIConfigPage(self.cfg)
        self.about_page = AboutPage()

        self.tabs.addTab(self.text2sql_page, "  Text2SQL  ")
        self.tabs.addTab(self.data_source_page, "  数据源配置  ")
        self.tabs.addTab(self.ai_page, "  AI 配置  ")
        self.tabs.addTab(self.about_page, "  软件说明  ")

        outer.addWidget(self.tabs, 1)

        self.setCentralWidget(container)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status_ds_label = QLabel("数据源: -")
        self.status_ai_label = QLabel("AI: -")
        self.status_msg_label = QLabel("就绪")
        self.status.addWidget(self.status_msg_label, 1)
        self.status.addPermanentWidget(self.status_ds_label)
        self.status.addPermanentWidget(QLabel("  |  "))
        self.status.addPermanentWidget(self.status_ai_label)

    def _wire_signals(self) -> None:
        self.data_source_page.data_sources_changed.connect(self._on_data_sources_changed)
        self.ai_page.ai_changed.connect(self._refresh_status)
        self.text2sql_page.status_message.connect(self._set_status)

    # ----- window controls -----
    def _toggle_max_restore(self) -> None:
        if self.isMaximized():
            self.showNormal()
            self.title_bar.set_maximized(False)
        else:
            self.showMaximized()
            self.title_bar.set_maximized(True)

    def changeEvent(self, event):
        # Keep the max/restore icon in sync when the OS changes window state.
        if event.type() == event.Type.WindowStateChange:
            self.title_bar.set_maximized(self.isMaximized())
        super().changeEvent(event)

    # ----- helpers -----
    def _on_data_sources_changed(self) -> None:
        self.text2sql_page.refresh_data_sources()
        self._refresh_status()

    def _refresh_status(self) -> None:
        ds_name = self.cfg.get_current_data_source() or "(未选择)"
        ai_cfg = self.cfg.get_ai_config()
        ai_desc = ai_cfg.get("model") or "(未配置)"
        provider = ai_cfg.get("provider") or "?"
        self.status_ds_label.setText(f"数据源: {ds_name}")
        self.status_ai_label.setText(f"AI: {provider}/{ai_desc}")

    def _set_status(self, msg: str) -> None:
        self.status_msg_label.setText(msg)
        self._refresh_status()
