from src.kb_bot import should_escalate


def test_empty_retrieval_is_escalated():
    assert should_escalate({"sources": 0, "answer": "I need a note for that."}) is True
    assert should_escalate({"sources": 2, "answer": "Friday."}) is False
