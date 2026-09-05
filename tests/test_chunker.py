from pdf_search.ingestion.chunker import TextChunker
from pdf_search.ingestion.models import PageContent


def test_text_chunker():
    page = PageContent(
        document_name="test.pdf",
        page_number=1,
        text="a" * 2500,
        extraction_method="text",
    )

    chunks = TextChunker().split(page)

    assert len(chunks) == 3
    assert len(chunks[0].text) == 1000
    assert len(chunks[1].text) == 1000
    assert len(chunks[2].text) == 800


def test_empty_text_returns_no_chunks():
    page = PageContent(
        document_name="test.pdf",
        page_number=1,
        text="",
        extraction_method="text",
    )

    assert TextChunker().split(page) == []
