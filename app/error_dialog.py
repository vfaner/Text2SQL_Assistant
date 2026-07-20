"""Error dialog - clean, scrollable, resizable, with a Close button.

Used for showing SQL execution errors (which can be quite long and noisy
from SQLAlchemy) without letting them overrun the result panel.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
    QVBoxLayout, QWidget,
)


class ErrorDialog(QDialog):
    """Modal dialog for showing a long error message with a Close button."""

    def __init__(
        self,
        parent: QWidget | None = None,
        title: str = "执行失败",
        summary: str = "",
        detail: str = "",
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(640)
        self.setMinimumHeight(280)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 14)
        root.setSpacing(10)

        # Headline - one-line summary
        head = QLabel(f"❌  {summary}" if summary else "❌  执行失败")
        head.setWordWrap(True)
        head.setStyleSheet(
            "font-size:15px; font-weight:600; color:#c0392b;"
        )
        root.addWidget(head)

        # Optional detail - long form, scrollable, monospace
        if detail:
            detail_view = QPlainTextEdit()
            detail_view.setReadOnly(True)
            detail_view.setPlainText(detail)
            detail_view.setStyleSheet(
                "QPlainTextEdit { "
                "background:#fdf6f6; border:1px solid #f2c7c1; "
                "border-radius:6px; padding:8px; "
                "font-family:'Menlo','Consolas',monospace; font-size:12px; "
                "color:#7f2f24; }"
            )
            root.addWidget(detail_view, 1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        btn_close.setDefault(True)
        btn_row.addWidget(btn_close)
        root.addLayout(btn_row)


def show_error(parent: QWidget | None, summary: str, detail: str = "", title: str = "执行失败") -> None:
    ErrorDialog(parent, title=title, summary=summary, detail=detail).exec()
