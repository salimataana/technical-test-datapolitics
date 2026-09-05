from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image

from pdf_search.config import OCR_DPI, OCR_LANGUAGE, OCR_MIN_TEXT_LENGTH
from pdf_search.ingestion.models import PageContent


class PdfExtractor:
    """Extract native PDF text and fall back to French OCR when needed."""

    def __init__(
        self,
        ocr_language: str = OCR_LANGUAGE,
        min_text_length: int = OCR_MIN_TEXT_LENGTH,
        dpi: int = OCR_DPI,
    ) -> None:
        if min_text_length < 0:
            raise ValueError("min_text_length must be non-negative")
        if dpi <= 0:
            raise ValueError("dpi must be positive")

        self.ocr_language = ocr_language
        self.min_text_length = min_text_length
        self.dpi = dpi

    def extract(self, pdf_path: Path) -> list[PageContent]:
        pdf_path = Path(pdf_path)
        if not pdf_path.is_file():
            raise FileNotFoundError(f"PDF file does not exist: {pdf_path}")

        pages = []
        document = pymupdf.open(pdf_path)

        try:
            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text").strip()
                extraction_method = "text"

                if len(text) < self.min_text_length:
                    text = self._extract_with_ocr(page)
                    extraction_method = "ocr"

                pages.append(
                    PageContent(
                        document_name=pdf_path.name,
                        page_number=page_number,
                        text=text,
                        extraction_method=extraction_method,
                    )
                )
        finally:
            document.close()

        return pages

    def _extract_with_ocr(self, page) -> str:
        pixmap = page.get_pixmap(dpi=self.dpi)
        image = Image.frombytes(
            "RGB",
            [pixmap.width, pixmap.height],
            pixmap.samples,
        )
        return pytesseract.image_to_string(
            image,
            lang=self.ocr_language,
        ).strip()
