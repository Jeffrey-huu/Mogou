from PySide6.QtGui import QTextDocument


def markdown_to_html(markdown: str) -> str:
    document = QTextDocument()
    document.setMarkdown(markdown)
    return document.toHtml()


def text_to_html(text: str) -> str:
    document = QTextDocument()
    document.setPlainText(text)
    return document.toHtml()


def html_to_markdown(html: str) -> str:
    document = QTextDocument()
    document.setHtml(html)
    return document.toMarkdown().rstrip() + "\n"


def html_to_text(html: str) -> str:
    document = QTextDocument()
    document.setHtml(html)
    return document.toPlainText()
