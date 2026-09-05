from pdf_search.config import CHUNK_OVERLAP, CHUNK_SIZE
from pdf_search.ingestion.models import PageContent, TextChunk


class TextChunker:
    """Split page text into overlapping character-based chunks."""

    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be between 0 and chunk_size - 1")

        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, page: PageContent) -> list[TextChunk]:
        return self.split_text(
            text=page.text,
            document_name=page.document_name,
            page_number=page.page_number,
            extraction_method=page.extraction_method,
        )

    def split_text(
        self,
        text: str,
        document_name: str,
        page_number: int,
        extraction_method: str = "text",
    ) -> list[TextChunk]:
        text = text.strip()
        if not text:
            return []

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(
                    TextChunk(
                        document_name=document_name,
                        page_number=page_number,
                        chunk_index=len(chunks),
                        extraction_method=extraction_method,
                        text=chunk,
                    )
                )
            start += self.chunk_size - self.overlap

        return chunks
