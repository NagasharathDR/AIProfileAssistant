import pytest

from app.services.chunking import ProfileChunk, chunk_profile_pages
from app.services.pdf_sources import PdfPageText


def test_chunking_respects_size_and_preserves_citation_metadata():
    pages = [PdfPageText(source="resume", page_number=3, text="x" * 2300)]

    chunks = chunk_profile_pages(pages, chunk_size=1000, overlap=150)

    assert [chunk.chunk_index for chunk in chunks] == [1, 2, 3]
    assert all(len(chunk.text) <= 1000 for chunk in chunks)
    assert all(chunk.source == "resume" and chunk.page_number == 3 for chunk in chunks)


def test_chunking_keeps_the_configured_overlap():
    text = "0123456789" * 12
    chunks = chunk_profile_pages(
        [PdfPageText(source="linkedin", page_number=1, text=text)],
        chunk_size=50,
        overlap=10,
    )

    assert chunks[0].text[-10:] == chunks[1].text[:10]


def test_chunking_keeps_pages_separate_and_numbers_chunks_per_page():
    pages = [
        PdfPageText(source="linkedin", page_number=1, text="first page"),
        PdfPageText(source="linkedin", page_number=2, text="second page"),
    ]

    chunks = chunk_profile_pages(pages, chunk_size=20, overlap=0)

    assert chunks == [
        ProfileChunk("linkedin", 1, 1, "first page"),
        ProfileChunk("linkedin", 2, 1, "second page"),
    ]


def test_chunking_skips_empty_pages():
    pages = [PdfPageText(source="resume", page_number=1, text="  ")]

    assert chunk_profile_pages(pages) == []


@pytest.mark.parametrize(
    ("chunk_size", "overlap", "message"),
    [
        (0, 0, "chunk_size must be a positive integer"),
        (10, -1, "overlap must be non-negative"),
        (10, 10, "smaller than chunk_size"),
    ],
)
def test_chunking_rejects_invalid_limits(chunk_size, overlap, message):
    with pytest.raises(ValueError, match=message):
        chunk_profile_pages([], chunk_size=chunk_size, overlap=overlap)