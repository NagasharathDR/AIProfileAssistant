import json
from typing import Any
from urllib import error, request

from app.core.config import Config


def _default_fallback_answer(question: str, profile_results: list[dict[str, Any]], github_results: list[dict[str, Any]]) -> str:
    if profile_results and github_results:
        profile_excerpt = profile_results[0].get("text") or "profile evidence"
        github_excerpt = github_results[0].get("repository") or "GitHub project evidence"
        return (
            f"Based on the filtered evidence, the answer is: {profile_excerpt}. "
            f"On GitHub, the relevant work includes {github_excerpt}."
        )
    if profile_results:
        return f"Based on the profile evidence, the answer is: {profile_results[0].get('text') or 'profile evidence'}."
    if github_results:
        return f"Based on the GitHub evidence, the most relevant project is: {github_results[0].get('repository') or 'GitHub project evidence'}."
    return f"I could not find enough evidence to answer '{question}' accurately."


def _extract_text(response_payload: dict[str, Any]) -> str:
    candidates = response_payload.get("candidates") or []
    for candidate in candidates:
        content = candidate.get("content") or {}
        parts = content.get("parts") or []
        text_parts = [part.get("text", "") for part in parts if isinstance(part, dict)]
        if text_parts:
            return "\n".join(text_parts).strip()
    return ""


def _gemini_url(action: str, api_key: str) -> str:
    return (
        f"{Config.get_gemini_api_base_url()}/v1beta/models/{Config.get_gemini_model()}:{action}"
        f"?key={api_key}"
    )


def generate_corrected_answer(question: str, profile_results: list[dict[str, Any]], github_results: list[dict[str, Any]]) -> str:
    """Ask Gemini to rewrite the answer using only the evidence gathered from MCP sources."""
    api_key = Config.get_gemini_api_key()
    if not api_key:
        return _default_fallback_answer(question, profile_results, github_results)

    evidence = {
        "question": question,
        "profile_results": profile_results,
        "github_results": github_results,
    }
    prompt = (
        "You are a careful answer assistant. Use only the evidence below and do not invent facts. "
        "Return a concise answer in plain English. If evidence is missing, say so clearly.\n\n"
        f"Evidence JSON:\n{json.dumps(evidence, ensure_ascii=True, default=str)}"
    )

    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    request_obj = request.Request(
        _gemini_url("generateContent", api_key),
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(request_obj, timeout=30) as response:
            body = response.read().decode("utf-8")
    except (error.HTTPError, error.URLError, TimeoutError, ValueError):
        return _default_fallback_answer(question, profile_results, github_results)

    try:
        response_payload = json.loads(body)
    except json.JSONDecodeError:
        return _default_fallback_answer(question, profile_results, github_results)

    text = _extract_text(response_payload)
    if text:
        return text.strip()
    return _default_fallback_answer(question, profile_results, github_results)


def classify_question_source(question: str) -> str:
    """Ask Gemini which source should answer the question: profile, github, or mixed."""
    api_key = Config.get_gemini_api_key()
    if not api_key:
        return ""

    prompt = (
        "Return only one word: profile, github, or mixed. "
        "Choose based on whether the question is about resume/profile facts, GitHub repositories/projects, or both.\n\n"
        f"Question: {question}"
    )

    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    request_obj = request.Request(
        _gemini_url("generateContent", api_key),
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(request_obj, timeout=30) as response:
            body = response.read().decode("utf-8")
    except (error.HTTPError, error.URLError, TimeoutError, ValueError):
        return ""

    try:
        response_payload = json.loads(body)
    except json.JSONDecodeError:
        return ""

    text = _extract_text(response_payload)
    normalized = (text or "").strip().lower().replace(" ", "")
    if normalized in {"profile", "github", "mixed"}:
        return normalized
    return ""
