from fastapi import APIRouter

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

@router.get("/")
def read_root():
    return {"message": "Welcome to the API"}

@router.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "message": "Item retrieved successfully"}