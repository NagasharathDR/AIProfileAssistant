from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def read_root():
    return {"message": "Welcome to the API"}

@router.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "message": "Item retrieved successfully"}