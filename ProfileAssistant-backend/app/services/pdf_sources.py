from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.core.config import Config


class PdfSourceError(ValueError):
    """Raised when a configured profile PDF cannot be safely extracted."""


@dataclass(frozen=True)
class PdfPageText:
    source: str
    page_number: int
    text: str


def extract_pdf_pages(
    pdf_path: Path,
    source: str,
    max_bytes: int | None = None,
    max_pages: int | None = None,
) -> list[PdfPageText]:
    """Extract non-empty page text from a bounded, configured PDF source."""
    max_bytes = Config.PROFILE_PDF_MAX_BYTES if max_bytes is None else max_bytes
    max_pages = Config.PROFILE_PDF_MAX_PAGES if max_pages is None else max_pages
    if max_bytes <= 0 or max_pages <= 0:
        raise ValueError("PDF extraction limits must be positive integers.")

    if not pdf_path.is_file():
        raise PdfSourceError(f"PDF source '{source}' was not found.")

    try:
        if pdf_path.stat().st_size > max_bytes:
            raise PdfSourceError(f"PDF source '{source}' exceeds the {max_bytes}-byte limit.")
        with pdf_path.open("rb") as pdf_file:
            pdf_bytes = pdf_file.read(max_bytes + 1)
    except OSError as exc:
        raise PdfSourceError(f"PDF source '{source}' could not be read.") from exc

    if len(pdf_bytes) > max_bytes:
        raise PdfSourceError(f"PDF source '{source}' exceeds the {max_bytes}-byte limit.")

    try:
        reader = PdfReader(BytesIO(pdf_bytes), strict=True)
        if reader.is_encrypted:
            raise PdfSourceError(f"PDF source '{source}' is encrypted and cannot be extracted.")
        if len(reader.pages) > max_pages:
            raise PdfSourceError(f"PDF source '{source}' exceeds the {max_pages}-page limit.")

        extracted_pages = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                extracted_pages.append(
                    PdfPageText(source=source, page_number=page_number, text=text)
                )
    except PdfSourceError:
        raise
    except Exception as exc:
        raise PdfSourceError(f"PDF source '{source}' could not be parsed or extracted.") from exc

    if not extracted_pages:
        raise PdfSourceError(f"PDF source '{source}' contains no extractable text.")
    return extracted_pages