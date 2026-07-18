"""Simple SQL syntax highlighter for QPlainTextEdit."""
from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


KEYWORDS = [
    "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "INSERT", "INTO", "VALUES",
    "UPDATE", "SET", "DELETE", "CREATE", "TABLE", "DROP", "ALTER", "ADD", "COLUMN",
    "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "FULL", "ON", "AS", "GROUP", "BY",
    "ORDER", "ASC", "DESC", "HAVING", "LIMIT", "OFFSET", "UNION", "ALL", "DISTINCT",
    "IN", "IS", "NULL", "LIKE", "BETWEEN", "EXISTS", "CASE", "WHEN", "THEN", "ELSE",
    "END", "WITH", "INDEX", "PRIMARY", "KEY", "FOREIGN", "REFERENCES", "DEFAULT",
    "CONSTRAINT", "UNIQUE", "AUTO_INCREMENT", "IDENTITY", "SHOW", "DESCRIBE", "EXPLAIN",
    "TRUNCATE", "GRANT", "REVOKE", "COMMIT", "ROLLBACK", "BEGIN", "TRANSACTION",
    "IF", "COUNT", "SUM", "AVG", "MIN", "MAX", "USING", "OVER", "PARTITION",
]


class SQLHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.keyword_fmt = QTextCharFormat()
        self.keyword_fmt.setForeground(QColor("#2c7be5"))
        self.keyword_fmt.setFontWeight(QFont.Bold)

        self.string_fmt = QTextCharFormat()
        self.string_fmt.setForeground(QColor("#27ae60"))

        self.number_fmt = QTextCharFormat()
        self.number_fmt.setForeground(QColor("#e67e22"))

        self.comment_fmt = QTextCharFormat()
        self.comment_fmt.setForeground(QColor("#95a5a6"))
        self.comment_fmt.setFontItalic(True)

        self._kw_re = re.compile(r"\b(" + "|".join(KEYWORDS) + r")\b", re.IGNORECASE)
        self._str_re = re.compile(r"'[^'\n]*'|\"[^\"\n]*\"")
        self._num_re = re.compile(r"\b\d+(\.\d+)?\b")
        self._cmt_re = re.compile(r"--[^\n]*")

    def highlightBlock(self, text: str) -> None:  # noqa: N802 (Qt naming)
        for m in self._kw_re.finditer(text):
            self.setFormat(m.start(), m.end() - m.start(), self.keyword_fmt)
        for m in self._num_re.finditer(text):
            self.setFormat(m.start(), m.end() - m.start(), self.number_fmt)
        for m in self._str_re.finditer(text):
            self.setFormat(m.start(), m.end() - m.start(), self.string_fmt)
        for m in self._cmt_re.finditer(text):
            self.setFormat(m.start(), m.end() - m.start(), self.comment_fmt)
