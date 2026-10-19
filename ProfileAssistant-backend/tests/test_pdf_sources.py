from pathlib import Path

import pytest

from app.services.pdf_sources import PdfSourceError, extract_pdf_pages


def make_text_pdf(page_texts: list[str]) -> bytes:
    page_objects = []
    page_ids = [4 + (index * 2) for index in range(len(page_texts))]
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_texts)} >>".encode("ascii"),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    for index, text in enumerate(page_texts):
        page_id = page_ids[index]
        content_id = page_id + 1
        page_objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] ".encode("ascii")
            + f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>".encode("ascii")
        )
        stream = f"BT /F1 12 Tf 40 200 Td ({text}) Tj ET".encode("ascii")
        page_objects.append(
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
            + stream + b"\nendstream"
        )
    objects.extend(page_objects)

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_number, content in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_number} 0 obj\n".encode("ascii"))
        pdf.extend(content)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)


def test_extract_pdf_pages_preserves_source_and_one_based_page_numbers(tmp_path):
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_bytes(make_text_pdf(["LinkedIn page one", "LinkedIn page two"]))

    pages = extract_pdf_pages(pdf_path, source="linkedin")

    assert [(page.source, page.page_number, page.text) for page in pages] == [
        ("linkedin", 1, "LinkedIn page one"),
        ("linkedin", 2, "LinkedIn page two"),
    ]


def test_extract_pdf_pages_rejects_malformed_pdf(tmp_path):
    pdf_path = tmp_path / "malformed.pdf"
    pdf_path.write_bytes(b"this is not a PDF")

    with pytest.raises(PdfSourceError, match="could not be parsed or extracted"):
        extract_pdf_pages(pdf_path, source="resume")


def test_extract_pdf_pages_rejects_pdf_without_extractable_text(tmp_path):
    pdf_path = tmp_path / "image-only.pdf"
    pdf_path.write_bytes(make_text_pdf(["", ""]))

    with pytest.raises(PdfSourceError, match="contains no extractable text"):
        extract_pdf_pages(pdf_path, source="resume")


def test_extract_pdf_pages_rejects_oversized_pdf(tmp_path):
    pdf_path = tmp_path / "large.pdf"
    pdf_path.write_bytes(make_text_pdf(["Text that exceeds the small test limit"]))

    with pytest.raises(PdfSourceError, match="exceeds the 20-byte limit"):
        extract_pdf_pages(pdf_path, source="resume", max_bytes=20)


def test_extract_pdf_pages_rejects_too_many_pages(tmp_path):
    pdf_path = tmp_path / "many-pages.pdf"
    pdf_path.write_bytes(make_text_pdf(["First page", "Second page"]))

    with pytest.raises(PdfSourceError, match="exceeds the 1-page limit"):
        extract_pdf_pages(pdf_path, source="resume", max_pages=1)


def test_extract_pdf_pages_reports_missing_source(tmp_path):
    missing_path = Path(tmp_path / "missing.pdf")

    with pytest.raises(PdfSourceError, match="was not found"):
        extract_pdf_pages(missing_path, source="linkedin")