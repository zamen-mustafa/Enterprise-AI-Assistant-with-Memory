from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Citation:
    document_id: str
    source: str
    chunk_index: int
    excerpt: str
    score: float


@dataclass
class AssistantResponse:
    answer: str
    route: str
    citations: list[Citation] = field(default_factory=list)
    memories_used: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Memory:
    content: str
    created_at: datetime
