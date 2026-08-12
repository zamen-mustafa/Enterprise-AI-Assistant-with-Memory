# Enterprise AI Assistant

Production-style LangGraph/LangChain assistant with isolated durable user memory, Redis short-term conversation cache, PostgreSQL persistence, persistent local hybrid vector retrieval, citations, document ingestion, Gemini generation, and Streamlit UI.

## Run on Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
Copy-Item .env.example .env  # optional, required only for Gemini configuration
# Set GOOGLE_API_KEY in .env for Gemini responses
streamlit run streamlit_app.py
```

For full Redis/PostgreSQL services, start Docker Desktop and run `docker compose up --build`. Then open http://localhost:8501.

## Architecture

- `app/assistant.py`: LangGraph context-to-generation workflow; Gemini or safe no-key fallback.
- `app/storage.py`: SQLAlchemy PostgreSQL production path / SQLite local fallback, Redis cache with SQL fallback.
- `app/rag.py`: JSON-persisted hashed vectors plus lexical scoring (hybrid local search).
- `app/documents.py`: validated text, Markdown, PDF, and DOCX extraction.

Run checks with `pytest` and `ruff check .`.

To load the included example document, run `python scripts/ingest_sample.py` before starting the UI.
