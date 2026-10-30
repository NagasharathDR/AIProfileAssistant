from fastapi import APIRouter, HTTPException

from app.services.github_mcp import search_github_projects
from app.services.orchestration import handle_question

router = APIRouter()

@router.get("/api/profile")
def read_sample_profile():
    return {
        "profile_type": "sample",
        "notice": "Illustrative sample data only; this is not a real person's profile.",
        "name": "Sample User",
        "title": "Example Professional",
        "summary": "Placeholder summary for demonstrating the profile API.",
        "skills": ["Example skill A", "Example skill B"],
        "experience": [
            {
                "role": "Sample role",
                "organization": "Example organization",
                "period": "Example dates",
            }
        ],
    }

@router.get("/api/github/projects")
async def read_github_projects(query: str = "python"):
    try:
        return await search_github_projects(query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get("/api/ask")
async def ask_question(question: str):
    try:
        return handle_question(question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get("/")
def read_root():
    return {"message": "Welcome to the API"}

@router.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "message": "Item retrieved successfully"}