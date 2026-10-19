import json

import pytest

from app.mcp_server import search_profile
from app.services.chunking import ProfileChunk
from app.services.retrieval import RetrievedChunk


class FakeRetriever:
    def search(self, query, top_k):
        assert query == "python API experience"
        assert top_k == 2
        return [
            RetrievedChunk(
                chunk=ProfileChunk(
                    source="resume",
                    page_number=2,
                    chunk_index=1,
                    text="Built Python APIs.",
                ),
                score=0.876543,
            )
        ]


def test_search_profile_returns_ranked_text_with_source_and_page_citations(monkeypatch):
    monkeypatch.setattr("app.mcp_server.get_profile_retriever", FakeRetriever)

    results = json.loads(search_profile("python API experience", top_k=2))

    assert results == [
        {
            "source": "resume",
            "page_number": 2,
            "text": "Built Python APIs.",
            "score": 0.8765,
        }
    ]


@pytest.mark.parametrize(
    ("query", "top_k", "message"),
    [
        ("  ", 2, "query must not be empty"),
        ("python", 0, "top_k must be between 1 and 8"),
        ("python", 9, "top_k must be between 1 and 8"),
    ],
)
def test_search_profile_rejects_invalid_inputs(query, top_k, message):
    with pytest.raises(ValueError, match=message):
        search_profile(query, top_k)