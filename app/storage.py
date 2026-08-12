"""Durable PostgreSQL/SQLite repository plus optional Redis conversation cache."""
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.models import Memory


class Base(DeclarativeBase):
    pass


class MemoryRow(Base):
    __tablename__ = "memories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ConversationRow(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    session_id: Mapped[str] = mapped_column(String(128), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class MemoryStore:
    def __init__(self, database_url: str | None, sqlite_path: Path, redis_url: str | None = None):
        url = database_url or f"sqlite:///{sqlite_path.resolve().as_posix()}"
        self.engine = create_engine(url, pool_pre_ping=True)
        Base.metadata.create_all(self.engine)
        self.redis = None
        if redis_url:
            try:
                import redis
                client = redis.Redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=1)
                client.ping()
                self.redis = client
            except Exception:
                self.redis = None

    def add_memory(self, user_id: str, content: str) -> None:
        with Session(self.engine) as session:
            exists = session.scalar(select(MemoryRow).where(MemoryRow.user_id == user_id, MemoryRow.content == content))
            if not exists:
                session.add(MemoryRow(user_id=user_id, content=content))
                session.commit()

    def memories(self, user_id: str, limit: int = 20) -> list[Memory]:
        with Session(self.engine) as session:
            rows = session.scalars(select(MemoryRow).where(MemoryRow.user_id == user_id).order_by(MemoryRow.created_at.desc()).limit(limit)).all()
        return [Memory(content=r.content, created_at=r.created_at) for r in rows]

    def append_message(self, user_id: str, session_id: str, role: str, content: str) -> None:
        key = f"eai:history:{user_id}:{session_id}"
        payload = json.dumps({"role": role, "content": content})
        if self.redis:
            self.redis.rpush(key, payload)
            self.redis.expire(key, 86400)
        with Session(self.engine) as session:
            session.add(ConversationRow(user_id=user_id, session_id=session_id, role=role, content=content))
            session.commit()

    def history(self, user_id: str, session_id: str, limit: int = 12) -> list[dict[str, str]]:
        key = f"eai:history:{user_id}:{session_id}"
        if self.redis:
            return [json.loads(v) for v in self.redis.lrange(key, -limit, -1)]
        with Session(self.engine) as session:
            rows = session.scalars(select(ConversationRow).where(ConversationRow.user_id == user_id, ConversationRow.session_id == session_id).order_by(ConversationRow.id.desc()).limit(limit)).all()
        return [{"role": r.role, "content": r.content} for r in reversed(rows)]
