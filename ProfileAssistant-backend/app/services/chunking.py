from dataclasses import dataclass

from app.core.config import Config
from app.services.pdf_sources import PdfPageText


@dataclass(frozen=True)
class ProfileChunk:
    source: str
    page_number: int
    chunk_index: int
    text: str


def chunk_profile_pages(
    pages: list[PdfPageText],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[ProfileChunk]:
    """Split page text into bounded chunks while retaining its citation metadata."""
    chunk_size = Config.PROFILE_CHUNK_SIZE if chunk_size is None else chunk_size
    overlap = Config.PROFILE_CHUNK_OVERLAP if overlap is None else overlap
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size.")

    chunks = []
    step = chunk_size - overlap
    for page in pages:
        text = page.text.strip()
        for chunk_index, start in enumerate(range(0, len(text), step), start=1):
            chunk_text = text[start : start + chunk_size].strip()
            if chunk_text:
                chunks.append(
                    ProfileChunk(
                        source=page.source,
                        page_number=page.page_number,
                        chunk_index=chunk_index,
                        text=chunk_text,
                    )
                )
    return chunks