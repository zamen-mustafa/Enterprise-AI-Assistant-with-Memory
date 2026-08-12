"""Persistent local hybrid vector retrieval without a hosted vector database."""
import hashlib
import json
import math
import re
from pathlib import Path

from app.models import Citation

TOKEN = re.compile(r"[A-Za-z0-9_]{2,}")


def tokens(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def embed(text: str, dimensions: int = 384) -> list[float]:
    result = [0.0] * dimensions
    for token in tokens(text):
        result[int(hashlib.sha256(token.encode()).hexdigest(), 16) % dimensions] += 1.0
    norm = math.sqrt(sum(v * v for v in result)) or 1.0
    return [v / norm for v in result]


class PersistentVectorStore:
    def __init__(self, path: Path):
        self.path, self.records = path, []
        if path.exists():
            self.records = json.loads(path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.records), encoding="utf-8")

    def add_document(self, document_id: str, source: str, text: str, chunk_size: int = 900, overlap: int = 150) -> int:
        self.records = [r for r in self.records if r["document_id"] != document_id]
        start = index = 0
        while start < len(text):
            chunk = text[start:start + chunk_size].strip()
            if chunk:
                self.records.append({"document_id": document_id, "source": source, "chunk_index": index, "text": chunk, "vector": embed(chunk)})
                index += 1
            start += chunk_size - overlap
        self._save()
        return index

    def search(self, query: str, k: int = 4) -> list[Citation]:
        qv, qtokens, scored = embed(query), set(tokens(query)), []
        for record in self.records:
            lexical = len(qtokens & set(tokens(record["text"]))) / max(1, len(qtokens))
            score = 0.72 * sum(x * y for x, y in zip(qv, record["vector"])) + 0.28 * lexical
            if score > 0.08:
                scored.append((score, record))
        return [Citation(document_id=r["document_id"], source=r["source"], chunk_index=r["chunk_index"], excerpt=r["text"][:360], score=round(s, 3)) for s, r in sorted(scored, reverse=True, key=lambda item: item[0])[:k]]
