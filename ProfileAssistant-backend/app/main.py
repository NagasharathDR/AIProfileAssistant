from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.routing import Mount

from app.api.routes import router as api_router
from app.mcp_server import create_mcp_http_app, mcp_server


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    async with mcp_server.session_manager.run():
        yield


app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/")
def read_root():
    return {"message": "Welcome to the My Python Backend API"}

app.include_router(api_router)
app.mount("/", create_mcp_http_app())