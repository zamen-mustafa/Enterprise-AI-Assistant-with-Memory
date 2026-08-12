from app.rag import PersistentVectorStore


def test_persistent_hybrid_retrieval(tmp_path):
    store = PersistentVectorStore(tmp_path / "vectors.json")
    assert store.add_document("d1", "handbook.md", "Remote work is allowed three days per week with manager approval.") == 1
    hits = store.search("What is the remote work policy?")
    assert hits and hits[0].source == "handbook.md"
    assert PersistentVectorStore(tmp_path / "vectors.json").search("remote work")
