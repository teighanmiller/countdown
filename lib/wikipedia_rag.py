from __future__ import annotations

import threading
import numpy as np
import wikipedia
from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None
_model_lock = threading.Lock()


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def preload_model() -> None:
    """Load the sentence transformer in a background thread if not already loaded."""
    if _model is None:
        threading.Thread(target=_get_model, daemon=True).start()


def fetch_and_embed(query: str) -> tuple[list[str], np.ndarray]:
    """Fetch a Wikipedia article, chunk it, and return (chunks, embeddings)."""
    text = _fetch_wikipedia(query)
    chunks = _chunk(text, chunk_words=200)
    model = _get_model()
    embeddings = model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
    return chunks, embeddings


def _fetch_wikipedia(query: str, attempts: int = 3) -> str:
    """Fetch Wikipedia article text, retrying on transient failures."""
    for attempt in range(attempts):
        try:
            page = wikipedia.page(query, auto_suggest=True)
            return page.content
        except wikipedia.exceptions.DisambiguationError as e:
            try:
                page = wikipedia.page(e.options[0], auto_suggest=False)
                return page.content
            except Exception:
                pass
        except wikipedia.exceptions.PageError:
            return f"Topic: {query}. This is a specialised subject with limited available context."
        except Exception:
            if attempt == attempts - 1:
                # All retries exhausted — return a minimal fallback so generation can still proceed
                return f"Topic: {query}. Context unavailable; use your general knowledge of this subject."
    return f"Topic: {query}."


def retrieve(query: str, chunks: list[str], embeddings: np.ndarray, top_k: int = 5) -> list[str]:
    """Return the top-k chunks most relevant to query."""
    model = _get_model()
    q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    scores = (embeddings @ q_emb.T).flatten()
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [chunks[i] for i in top_indices]


def similarity(text_a: str, text_b: str) -> float:
    """Cosine similarity between two strings using the sentence transformer."""
    model = _get_model()
    embs = model.encode([text_a, text_b], convert_to_numpy=True, normalize_embeddings=True)
    return float(embs[0] @ embs[1])


def _chunk(text: str, chunk_words: int = 200) -> list[str]:
    words = text.split()
    return [
        " ".join(words[i : i + chunk_words])
        for i in range(0, len(words), chunk_words)
        if words[i : i + chunk_words]
    ]
