from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image



def extract_text_from_pdf(pdf_path: Path) -> list[dict]:
    """
    Extract text from each page of a PDF.

    Uses standard PDF text extraction first.
    Falls back to OCR when the page contains little or no text.
    """
    pages = []

    document = pymupdf.open(pdf_path)

    try:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            extraction_method = "text"

            if len(text) < 20:
                pixmap = page.get_pixmap(dpi=200)

                image = Image.frombytes(
                    "RGB",
                    [pixmap.width, pixmap.height],
                    pixmap.samples,
                )

                text = pytesseract.image_to_string(
                    image,
                    lang="fra+eng",
                ).strip()

                extraction_method = "ocr"

            pages.append(
                {
                    "document_name": pdf_path.name,
                    "page_number": page_number,
                    "text": text,
                    "extraction_method": extraction_method,
                }
            )
    finally:
        document.close()

    return pages