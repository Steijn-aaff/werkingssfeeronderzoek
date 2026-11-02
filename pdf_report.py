import re
from io import BytesIO

import markdown
from xhtml2pdf import pisa

CSS = """
@page { size: a4 portrait; margin: 2cm; }
body { font-family: Helvetica; font-size: 10.5pt; line-height: 1.4; color: #000000; }
h1, h2, h3 { color: #4e2680; }
h1 { font-size: 20pt; }
h2 { font-size: 14pt; margin-top: 16pt; }
h3 { font-size: 11.5pt; }
a { color: #4e2680; }
td, th { border: 1px solid #d9d0e5; padding: 4pt 6pt; }
th { background-color: #efeaf5; color: #4e2680; }
"""

LIST_ITEM = re.compile(r"\s*([-*+]|\d+[.)])\s")

def blank_line_before_lists(text):
    # CommonMark (the browser) starts a list right after a paragraph line, Python-Markdown does not
    # and then renders "- item" as plain text, so add the blank line it needs
    lines = []
    for line in text.split("\n"):
        if lines and LIST_ITEM.match(line) and lines[-1].strip() and not LIST_ITEM.match(lines[-1]):
            lines.append("")
        lines.append(line)
    return "\n".join(lines)

def markdown_to_pdf(text):
    # The text comes from the model: drop images (xhtml2pdf would fetch the URL) and escape raw HTML
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text).replace("<", "&lt;")
    text = blank_line_before_lists(text)
    body = markdown.markdown(text, extensions=["tables", "sane_lists"])
    html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"

    out = BytesIO()
    result = pisa.CreatePDF(html, dest=out, encoding="utf-8")
    if result.err:
        raise RuntimeError("PDF kon niet worden gemaakt")
    return out.getvalue()
