from app.assistant import EnterpriseAssistant
from app.config import Settings


def test_new_session_isolated_but_memory_survives(tmp_path):
    service = EnterpriseAssistant(Settings(data_dir=tmp_path))
    service.ask("alice", "first-chat", "Remember that I prefer concise answers")
    service.ask("alice", "new-chat", "Hello")
    assert service.memory.history("alice", "new-chat")[0]["content"] == "Hello"
    assert any("concise" in item.content for item in service.memory.memories("alice"))
