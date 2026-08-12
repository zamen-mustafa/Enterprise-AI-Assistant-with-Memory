from app.assistant import EnterpriseAssistant
from app.config import Settings


def test_memory_is_user_isolated(tmp_path):
    service = EnterpriseAssistant(Settings(data_dir=tmp_path))
    service.ask("alice", "s1", "Remember that I prefer concise answers")
    assert any("concise" in memory.content for memory in service.memory.memories("alice"))
    assert not service.memory.memories("bob")


def test_document_answer_has_citation(tmp_path):
    service = EnterpriseAssistant(Settings(data_dir=tmp_path))
    service.vectors.add_document("policy", "policy.md", "Expense reports must be filed within thirty days.")
    response = service.ask("alice", "s1", "What does the policy say about expense reports?")
    assert response.citations
