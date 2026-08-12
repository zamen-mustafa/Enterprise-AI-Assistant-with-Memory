import io
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from app.security import safe_filename


def extract_text(filename: str, content: bytes) -> str:
    suffix = Path(safe_filename(filename)).suffix.lower()
    if suffix in {".txt", ".md"}:
        return content.decode("utf-8", errors="replace")
    if suffix == ".pdf":
        return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(content)).pages)
    return "\n".join(paragraph.text for paragraph in Document(io.BytesIO(content)).paragraphs)
