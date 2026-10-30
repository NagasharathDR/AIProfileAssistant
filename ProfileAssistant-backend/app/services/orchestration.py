import json
from typing import Any

from app.core.config import Config
from app.mcp_server import search_profile
from app.services.gemini import classify_question_source, generate_corrected_answer
from app.services.github_mcp import search_github_projects

PROFILE_KEYWORDS = {
    "profile",
    "resume",
    "linkedin",
    "experience",
    "experience-level",
    "skills",
    "skill",
    "education",
    "background",
    "worked at",
    "worked with",
    "career",
    "project experience",
    "python experience",
    "python",
}

GITHUB_KEYWORDS = {
    "github",
    "repository",
    "repo",
    "repos",
    "pull request",
    "pull requests",
    "pr",
    "issue",
    "issues",
    "commit",
    "commits",
    "contribution",
    "contributions",
    "project",
    "projects",
}


def detect_sources(question: str) -> list[str]:
    """Detect whether a query should use profile, GitHub, or both sources.

    If Gemini is configured, the model decides the source. Otherwise we use the
    existing keyword-based fallback to keep the system deterministic without the
    LLM.
    """
    normalized = (question or "").strip().lower()
    if not normalized:
        return []

    if Config.get_gemini_api_key():
        llm_source = classify_question_source(question)
        if llm_source in {"profile", "github", "mixed"}:
            return [llm_source]

    has_profile = any(keyword in normalized for keyword in PROFILE_KEYWORDS)
    has_github = any(keyword in normalized for keyword in GITHUB_KEYWORDS)

    if has_profile and has_github:
        return ["mixed"]
    if has_profile:
        return ["profile"]
    if has_github:
        return ["github"]
    return ["profile", "github"]


def _normalize_profile_results(raw_result: Any) -> list[dict[str, Any]]:
    if raw_result is None:
        return []

    if isinstance(raw_result, str):
        try:
            raw_result = json.loads(raw_result)
        except json.JSONDecodeError:
            return []

    if isinstance(raw_result, dict):
        if "data" in raw_result and isinstance(raw_result["data"], list):
            raw_result = raw_result["data"]
        elif "results" in raw_result and isinstance(raw_result["results"], list):
            raw_result = raw_result["results"]
        elif "content" in raw_result and isinstance(raw_result["content"], list):
            raw_result = raw_result["content"]
        else:
            raw_result = [raw_result]

    if not isinstance(raw_result, list):
        return []

    normalized: list[dict[str, Any]] = []
    for item in raw_result:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "source": item.get("source") or "profile",
                "page_number": item.get("page_number"),
                "text": item.get("text") or item.get("summary") or "",
                "score": item.get("score"),
            }
        )
    return normalized


def _normalize_github_results(raw_result: Any) -> list[dict[str, Any]]:
    if raw_result is None:
        return []

    if isinstance(raw_result, dict):
        for key in ("data", "items", "results", "content"):
            if key in raw_result and isinstance(raw_result[key], list):
                raw_result = raw_result[key]
                break
        else:
            raw_result = [raw_result]

    if not isinstance(raw_result, list):
        return []

    normalized: list[dict[str, Any]] = []
    for item in raw_result:
        if not isinstance(item, dict):
            continue

        repo_name = (
            item.get("repository")
            or item.get("repo")
            or item.get("full_name")
            or item.get("name")
            or "GitHub project"
        )
        description = item.get("description") or item.get("summary") or item.get("text") or ""
        normalized.append(
            {
                "repository": repo_name,
                "description": description,
                "source": "github",
                "matched_text": description,
            }
        )
    return normalized


def _build_final_answer(question: str, profile_results: list[dict[str, Any]], github_results: list[dict[str, Any]], source: str) -> str:
    text = question.strip()
    if not profile_results and not github_results:
        return "I could not find strong profile or GitHub evidence for that question."

    if source == "mixed":
        profile_summary = "; ".join(
            result.get("text") or result.get("description") or "profile evidence"
            for result in profile_results[:2]
        ) or "profile evidence"
        github_summary = "; ".join(
            result.get("repository") or result.get("matched_text") or "GitHub project"
            for result in github_results[:2]
        ) or "GitHub project evidence"
        return (
            "Based on your profile and GitHub evidence, your Python background and project work align with "
            f"the following: {profile_summary}. On GitHub, the relevant work includes {github_summary}."
        )

    if profile_results and not github_results:
        excerpts = "; ".join(
            result.get("text") or "profile evidence" for result in profile_results[:3]
        )
        return f"Based on the profile evidence, the answer is: {excerpts}."

    if github_results and not profile_results:
        repos = "; ".join(
            result.get("repository") or "GitHub project" for result in github_results[:3]
        )
        return f"Based on the GitHub evidence, the most relevant projects are: {repos}."

    excerpts = "; ".join(
        result.get("text") or result.get("description") or "evidence"
        for result in (profile_results + github_results)[:3]
    )
    return f"Using the evidence available for '{text}', the answer is: {excerpts}."


def handle_question(question: str) -> dict[str, Any]:
    """Route a question to the appropriate MCP sources and return the assembled response."""
    if not question or not question.strip():
        raise ValueError("query must not be empty.")

    question_text = question.strip()
    sources = detect_sources(question_text)
    source = "mixed" if "mixed" in sources else sources[0]

    profile_results: list[dict[str, Any]] = []
    github_results: list[dict[str, Any]] = []

    if source in {"profile", "mixed"}:
        profile_payload = search_profile(question_text, top_k=4)
        profile_results = _normalize_profile_results(profile_payload)

    if source in {"github", "mixed"}:
        github_payload = search_github_projects(question_text, top_k=5)
        github_results = _normalize_github_results(github_payload)

    final_answer = _build_final_answer(question_text, profile_results, github_results, source)
    if Config.get_gemini_api_key():
        final_answer = generate_corrected_answer(question_text, profile_results, github_results)

    return {
        "question": question_text,
        "source": source,
        "profile_results": profile_results,
        "github_results": github_results,
        "final_answer": final_answer,
    }
