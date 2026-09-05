from pathlib import Path

from pdf_search.ingestion.extractor import PdfExtractor


def test_pdf_extractor_reads_native_text():
    pdf_path = Path("data/Ordre_du_jour_18-06-2026.pdf")

    pages = PdfExtractor().extract(pdf_path)

    assert len(pages) > 0
    assert pages[0].document_name == pdf_path.name
    assert pages[0].page_number == 1


def test_pdf_extractor_uses_ocr_for_scanned_pdf():
    pdf_path = Path(
        "data/AFF-2026.06.11-DP-26A0019-19-PLACE-DES-HAUTS-TAILLIS-ACCORD.pdf"
    )

    pages = PdfExtractor().extract(pdf_path)

    assert len(pages) > 0
    assert pages[0].extraction_method == "ocr"
    assert len(pages[0].text) > 0
