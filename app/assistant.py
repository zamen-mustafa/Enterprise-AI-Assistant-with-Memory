import re
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.config import Settings
from app.models import AssistantResponse, Citation
from app.rag import PersistentVectorStore
from app.security import redact_secret, validate_identifier
from app.storage import MemoryStore


class State(TypedDict, total=False):
    query: str
    user_id: str
    session_id: str
    route: str
    memories: list[str]
    citations: list[Citation]
    answer: str


class EnterpriseAssistant:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.memory = MemoryStore(settings.database_url, settings.sqlite_path, settings.redis_url)
        self.vectors = PersistentVectorStore(settings.vector_path)
        self.graph = self._build_graph()

    @staticmethod
    def _route(state: State) -> dict:
        query = state["query"].lower()
        knowledge_terms = ("document", "policy", "according to", "knowledge base", "handbook", "project")
        memory_terms = ("remember", "my ", "previous", "preference", "what do you know")
        route = "hybrid" if any(term in query for term in knowledge_terms) and any(term in query for term in memory_terms) else "knowledge" if any(term in query for term in knowledge_terms) else "memory" if any(term in query for term in memory_terms) else "conversation"
        return {"route": route}

    def _load_context(self, state: State) -> dict:
        route = state["route"]
        memories = [m.content for m in self.memory.memories(state["user_id"])] if route in {"memory", "hybrid"} else []
        citations = self.vectors.search(state["query"]) if route in {"knowledge", "hybrid"} else []
        return {"memories": memories, "citations": citations}

    def _generate(self, state: State) -> dict:
        history = self.memory.history(state["user_id"], state["session_id"])
        sources = "\n".join(f"- {c.excerpt}" for c in state.get("citations", []))
        memories = "\n".join(f"- {m}" for m in state.get("memories", [])[:8])
        if self.settings.google_api_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            model = ChatGoogleGenerativeAI(model=self.settings.gemini_model, google_api_key=self.settings.google_api_key, temperature=0.2)
            prompt = f"""You are an enterprise assistant. Answer accurately, state uncertainty, and never reveal secrets.
User memories (only this user):\n{memories or 'None'}
Knowledge excerpts:\n{sources or 'None'}
Conversation:\n{history}
Question: {state['query']}"""
            answer = str(model.invoke(prompt).content)
        elif sources:
            answer = "I found relevant knowledge:\n\n" + "\n\n".join(c.excerpt for c in state["citations"]) + "\n\nConfigure GOOGLE_API_KEY for a synthesized Gemini answer."
        elif state.get("memories"):
            answer = "I remember: " + "; ".join(state["memories"][:3]) + ". Configure GOOGLE_API_KEY for a fuller response."
        else:
            answer = "I’m ready to help. Upload documents or configure GOOGLE_API_KEY for Gemini-powered answers."
        return {"answer": redact_secret(answer)}

    def _build_graph(self):
        graph = StateGraph(State)
        graph.add_node("route", self._route)
        graph.add_node("context", self._load_context)
        graph.add_node("generate", self._generate)
        graph.add_edge(START, "route")
        graph.add_edge("route", "context")
        graph.add_edge("context", "generate")
        graph.add_edge("generate", END)
        return graph.compile()

    @staticmethod
    def _extract_memories(query: str) -> list[str]:
        patterns = [r"(?i)remember (?:that )?(.+)", r"(?i)my (?:name|role|preference|team) is (.+)", r"(?i)i (?:prefer|work|am) (.+)"]
        return [match.group(1).strip().rstrip(".") for pattern in patterns if (match := re.search(pattern, query))]

    def ask(self, user_id: str, session_id: str, query: str) -> AssistantResponse:
        validate_identifier(user_id, "user id")
        validate_identifier(session_id, "session id")
        clean = redact_secret(query.strip())
        if not clean:
            raise ValueError("Please enter a message")
        self.memory.append_message(user_id, session_id, "user", clean)
        for item in self._extract_memories(clean):
            self.memory.add_memory(user_id, item)
        state = self.graph.invoke({"query": clean, "user_id": user_id, "session_id": session_id})
        self.memory.append_message(user_id, session_id, "assistant", state["answer"])
        return AssistantResponse(answer=state["answer"], route=state["route"], citations=state.get("citations", []), memories_used=state.get("memories", []))

    def stream(self, user_id: str, session_id: str, query: str):
        result = self.ask(user_id, session_id, query)
        yield from re.findall(r"\S+\s*", result.answer)
