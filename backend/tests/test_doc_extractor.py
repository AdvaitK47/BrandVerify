"""
Tests for document text extraction.
"""

import pytest

from backend.services.doc_extractor import DocumentError, extract_document


def test_docx_text_table_and_footer_are_extracted(tmp_path):
    docx = pytest.importorskip("docx")

    document = docx.Document()
    document.add_paragraph("Our engine is guaranteed to be 10X faster.")
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Plan"
    table.rows[0].cells[1].text = "Enterprise"
    document.sections[0].footer.paragraphs[0].text = "Past performance is not a guarantee."
    path = tmp_path / "brief.docx"
    document.save(path)

    result = extract_document(path)

    assert result.page_count == 1
    assert result.has_text
    assert "guaranteed to be 10X faster" in result.text
    assert "Plan | Enterprise" in result.text
    assert "Past performance is not a guarantee." in result.text


def test_pdf_text_is_extracted_per_page(tmp_path):
    fitz = pytest.importorskip("fitz")

    pdf = fitz.open()
    pdf.new_page().insert_text((72, 72), "Page one has zero downtime.")
    pdf.new_page().insert_text((72, 72), "Page two footer text.")
    path = tmp_path / "deck.pdf"
    pdf.save(str(path))
    pdf.close()

    result = extract_document(path)

    assert result.page_count == 2
    assert "zero downtime" in result.pages[0]
    assert "Page two" in result.pages[1]


def test_unsupported_extension_is_rejected(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("hello")

    with pytest.raises(DocumentError):
        extract_document(path)


def test_corrupt_docx_is_rejected_cleanly(tmp_path):
    pytest.importorskip("docx")
    path = tmp_path / "broken.docx"
    path.write_bytes(b"this is not a real word file")

    with pytest.raises(DocumentError):
        extract_document(path)


def test_corrupt_pdf_is_rejected_cleanly(tmp_path):
    pytest.importorskip("fitz")
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"this is not a real pdf")

    with pytest.raises(DocumentError):
        extract_document(path)
