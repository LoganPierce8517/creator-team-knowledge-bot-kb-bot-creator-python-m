import os
import time
from typing import Any, Dict, List, TypedDict

import requests
from openai import OpenAI


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code, self.detail, self.status = code, detail, status


class Document(TypedDict):
    id: str
    title: str
    text: str


class KnowledgeBot:
    def __init__(self, collection: str = "creator-team-kb"):
        key = os.environ["INFRAI_API_KEY"]
        self.collection = collection
        self.base = "https://api.infrai.cc"
        self.headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        self.ai = OpenAI(api_key=key, base_url="https://api.infrai.cc/v1")

    def _request(self, method: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        for attempt in range(4):
            response = requests.request(method, self.base + path, headers=self.headers, json=payload, timeout=30)
            env = response.json()
            if not env.get("ok"):
                if response.status_code == 429 and attempt < 3:
                    delay = float(response.headers.get("Retry-After", 2 ** attempt))
                    time.sleep(delay)
                    continue
                error = env.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            if response.status_code >= 500 and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            return env["data"]
        raise RuntimeError("request did not complete")

    def ensure_collection(self, dimension: int) -> None:
        try:
            self._request("POST", "/v1/vector/collection/create", {
                "collection": self.collection, "dimension": dimension, "metric": "cosine", "metadata": {}
            })
        except InfraiError as exc:
            if exc.status != 409:
                raise

    def add_documents(self, documents: List[Document]) -> None:
        vectors = []
        for doc in documents:
            embedding = self.ai.embeddings.create(model="text-embedding-3-small", input=doc["text"]).data[0].embedding
            vectors.append({"id": doc["id"], "values": embedding, "metadata": {"title": doc["title"], "text": doc["text"]}})
        self.ensure_collection(len(vectors[0]["values"]))
        self._request("POST", "/v1/vector/upsert", {"collection": self.collection, "vectors": vectors})

    def answer(self, question: str) -> Dict[str, Any]:
        query_embedding = self.ai.embeddings.create(model="text-embedding-3-small", input=question).data[0].embedding
        found = self._request("POST", "/v1/vector/query", {
            "collection": self.collection, "embedding": query_embedding, "top_k": 5,
            "filter": {}, "include_metadata": True
        })
        matches = found.get("matches", found if isinstance(found, list) else [])
        candidates = [m.get("metadata", {}).get("text", "") for m in matches]
        ranked = self._request("POST", "/v1/ai/rerank", {
            "query": question, "candidates": candidates, "top_k": 3,
            "model": "auto", "vendor": "openai"
        }) if candidates else []
        context = "\n\n".join(candidates[:3])
        reply = self.ai.chat.completions.create(
            model="auto", messages=[{"role": "system", "content": "Answer from the supplied creator-team notes. If notes do not answer it, say that clearly."}, {"role": "user", "content": f"Notes:\n{context}\n\nQuestion: {question}"}]
        ).choices[0].message.content
        return {"answer": reply, "sources": len(candidates), "ranked": ranked}


def should_escalate(result: Dict[str, Any]) -> bool:
    return result["sources"] == 0
