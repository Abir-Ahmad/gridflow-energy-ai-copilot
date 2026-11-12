"""Local dense embeddings and exact cosine search. No vector server required."""

import hashlib
import json
from pathlib import Path
from threading import Lock

import numpy as np

from .schemas import Source

MODEL = "BAAI/bge-small-en-v1.5"
CORPUS = Path(__file__).parent / "corpus" / "sources.json"


def chunk_documents(documents: list[dict], words=100, overlap=20) -> list[dict]:
    if not 0 <= overlap < words:
        raise ValueError("overlap must be smaller than chunk size")
    chunks = []
    for doc in documents:
        tokens = doc["text"].split()
        for start in range(0, len(tokens), words - overlap):
            text = " ".join(tokens[start : start + words])
            digest = hashlib.sha256(text.encode()).hexdigest()[:12]
            chunks.append({**doc, "id": f"{doc['id']}:{start}:{digest}", "text": text})
            if start + words >= len(tokens):
                break
    return chunks


class Retriever:
    def __init__(self, embedder=None, documents=None, threshold=0.60):
        if embedder is None:
            from fastembed import TextEmbedding

            embedder = TextEmbedding(model_name=MODEL, threads=2)
        self.embedder = embedder
        self.threshold = threshold  # heuristic, not a calibrated confidence probability
        self.lock = Lock()
        self.chunks = chunk_documents(documents if documents is not None else json.loads(CORPUS.read_text()))
        self.vectors = self._normalise(list(self.embedder.embed([x["text"] for x in self.chunks])))

    @staticmethod
    def _normalise(vectors):
        matrix = np.asarray(vectors, dtype=np.float32)
        return matrix / np.maximum(np.linalg.norm(matrix, axis=-1, keepdims=True), 1e-12)

    def search(self, query: str, limit=3) -> list[Source]:
        with self.lock:
            vector = self._normalise(list(self.embedder.query_embed(query)))[0]
        scores = self.vectors @ vector
        indices = np.argsort(-scores, kind="stable")[:limit]
        return [
            Source(
                id=self.chunks[i]["id"],
                title=self.chunks[i]["title"],
                url=self.chunks[i]["url"],
                text=self.chunks[i]["text"],
                score=float(scores[i]),
            )
            for i in indices
            if scores[i] >= self.threshold
        ]
