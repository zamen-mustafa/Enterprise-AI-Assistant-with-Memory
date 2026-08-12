import re
import uuid
from pathlib import Path

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def new_id() -> str:
    return str(uuid.uuid4())


def safe_filename(name: str) -> str:
    candidate = Path(name).name
    candidate = re.sub(r"[^A-Za-z0-9._ -]", "_", candidate)
    if not candidate or Path(candidate).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Only .txt, .md, .pdf, and .docx files are allowed")
    return candidate


def validate_identifier(value: str, label: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value):
        raise ValueError(f"Invalid {label}")
    return value


def redact_secret(text: str) -> str:
    return re.sub(r"(?i)(api[_ -]?key|password|token)\s*[:=]\s*\S+", r"\1=[REDACTED]", text)
