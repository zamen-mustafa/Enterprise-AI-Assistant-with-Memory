"""Index the bundled handbook for a first local RAG query."""
from pathlib import Path

from app.assistant import EnterpriseAssistant
from app.config import get_settings
from app.security import new_id


def main() -> None:
    assistant = EnterpriseAssistant(get_settings())
    source = Path("samples/employee-handbook.md")
    chunks = assistant.vectors.add_document(new_id(), source.name, source.read_text(encoding="utf-8"))
    print(f"Indexed {chunks} chunks from {source}")


if __name__ == "__main__":
    main()
