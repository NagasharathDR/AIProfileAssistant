import sys
import types

import pytest

from app.services.chunking import ProfileChunk
from app.services.retrieval import ProfileRetriever


class FakeEmbedder:
    def __init__(self, vectors_by_text, query_vectors):
        self.vectors_by_text = vectors_by_text
        self.query_vectors = query_vectors

    def embed(self, documents):
        return [self.vectors_by_text[document] for document in documents]

    def query_embed(self, query):
        return [self.query_vectors[query]]


def test_search_ranks_relevant_chunks_and_preserves_citations():
    chunks = [
        ProfileChunk("linkedin", 1, 1, "python backend experience"),
        ProfileChunk("resume", 2, 1, "project leadership history"),
        ProfileChunk("resume", 3, 1, "python API development"),
    ]
    embedder = FakeEmbedder(
        vectors_by_text={
            chunks[0].text: [1, 0],
            chunks[1].text: [0, 1],
            chunks[2].text: [0.8, 0.2],
        },
        query_vectors={"python experience": [1, 0]},
    )
    retriever = ProfileRetriever(chunks, embedder)

    results = retriever.search("python experience", top_k=2)

    assert [result.chunk for result in results] == [chunks[0], chunks[2]]
    assert results[0].chunk.source == "linkedin"
    assert results[0].chunk.page_number == 1
    assert results[0].score == pytest.approx(1.0)
    assert results[1].score == pytest.approx(0.9701425)


def test_search_rejects_empty_query_and_invalid_top_k():
    chunk = ProfileChunk("resume", 1, 1, "sample text")
    retriever = ProfileRetriever(
        [chunk],
        FakeEmbedder({"sample text": [1, 0]}, {"ok": [1, 0]}),
    )

    with pytest.raises(ValueError, match="query must not be empty"):
        retriever.search("  ")
    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        retriever.search("ok", top_k=0)


def test_retriever_rejects_empty_chunks():
    with pytest.raises(ValueError, match="At least one profile chunk is required"):
        ProfileRetriever([], FakeEmbedder({}, {}))


def test_retriever_rejects_mismatched_embedding_count():
    chunk = ProfileChunk("resume", 1, 1, "sample text")
    embedder = FakeEmbedder({"sample text": [1, 0]}, {})
    embedder.embed = lambda documents: []

    with pytest.raises(ValueError, match="one vector per profile chunk"):
        ProfileRetriever([chunk], embedder)


def test_from_chunks_falls_back_to_keyword_embedder(monkeypatch):
    class FakeTextEmbedding:
        def __init__(self, model_name):
            raise RuntimeError("model unavailable")

    monkeypatch.setitem(sys.modules, "fastembed", types.SimpleNamespace(TextEmbedding=FakeTextEmbedding))

    chunks = [
        ProfileChunk("resume", 1, 1, "python backend experience"),
        ProfileChunk("linkedin", 2, 1, "project leadership"),
    ]

    retriever = ProfileRetriever.from_chunks(chunks)
    results = retriever.search("python experience", top_k=1)

    assert results[0].chunk.text == "python backend experience"