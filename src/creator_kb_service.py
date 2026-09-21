from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .kb_bot import Document, InfraiError, KnowledgeBot, should_escalate


class NoteRequest(BaseModel):
    id: str
    title: str
    text: str


class IndexRequest(BaseModel):
    documents: List[NoteRequest]


class QuestionRequest(BaseModel):
    question: str


app = FastAPI(title="Creator Team Knowledge Bot")


def bot() -> KnowledgeBot:
    return KnowledgeBot()


@app.post("/documents")
def index_documents(request: IndexRequest):
    try:
        notes: List[Document] = [note.model_dump() for note in request.documents]
        bot().add_documents(notes)
        return {"indexed": len(notes)}
    except InfraiError as exc:
        raise HTTPException(status_code=exc.status if exc.status < 500 else 502, detail=exc.detail) from exc


@app.post("/ask")
def ask(request: QuestionRequest):
    try:
        result = bot().answer(request.question)
        return {**result, "escalate": should_escalate(result)}
    except InfraiError as exc:
        raise HTTPException(status_code=exc.status if exc.status < 500 else 502, detail=exc.detail) from exc
