import json

from app.services.orchestration import handle_question, detect_sources


def test_detect_sources_prioritizes_profile_for_profile_questions():
    sources = detect_sources("Tell me about my Python experience and resume details")

    assert sources == ["profile"]


def test_detect_sources_prioritizes_github_for_repo_questions():
    sources = detect_sources("Show me my GitHub repositories and recent pull requests")

    assert sources == ["github"]


def test_handle_question_combines_profile_and_github_evidence(monkeypatch):
    monkeypatch.setattr(
        "app.services.orchestration.search_profile",
        lambda query, top_k=4: json.dumps([
            {
                "source": "resume",
                "page_number": 3,
                "text": "Built Python APIs for internal tooling.",
                "score": 0.91,
            }
        ]),
    )
    monkeypatch.setattr(
        "app.services.orchestration.search_github_projects",
        lambda query, top_k=5: {
            "query": query,
            "data": [
                {
                    "repository": "ai-profile-assistant",
                    "description": "FastAPI MCP project for AI profile search.",
                }
            ],
        },
    )

    result = handle_question("What Python projects and experience do I have?")

    assert result["source"] == "mixed"
    assert result["profile_results"][0]["source"] == "resume"
    assert result["github_results"][0]["repository"] == "ai-profile-assistant"
    assert "Python" in result["final_answer"]
    assert "GitHub" in result["final_answer"]


def test_handle_question_uses_gemini_when_configured(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "demo-key")
    monkeypatch.setattr(
        "app.services.orchestration.search_profile",
        lambda query, top_k=4: json.dumps([
            {
                "source": "resume",
                "page_number": 4,
                "text": "Worked on a Python API project.",
                "score": 0.93,
            }
        ]),
    )
    monkeypatch.setattr(
        "app.services.orchestration.search_github_projects",
        lambda query, top_k=5: {
            "query": query,
            "data": [{"repository": "api-demo", "description": "Python API demo"}],
        },
    )
    monkeypatch.setattr(
        "app.services.orchestration.generate_corrected_answer",
        lambda question, profile_results, github_results: "Corrected answer from Gemini.",
    )

    result = handle_question("Tell me about my Python projects and resume")

    assert result["final_answer"] == "Corrected answer from Gemini."


def test_handle_question_rejects_empty_query():
    try:
        handle_question("   ")
        raise AssertionError("Expected ValueError")
    except ValueError as exc:
        assert "query must not be empty" in str(exc)
