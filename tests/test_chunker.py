from pdf_search.ingestion.chunker import chunk_text


def test_chunk_text():
    text = "a" * 2500

    chunks = chunk_text(
        text=text,
        document_name="test.pdf",
        page_number=1,
        chunk_size=1000,
        overlap=150,
    )

    assert len(chunks) == 3
    assert len(chunks[0]["text"]) == 1000
    assert len(chunks[1]["text"]) == 1000
    assert len(chunks[2]["text"]) == 800


def test_empty_text_returns_no_chunks():
    chunks = chunk_text(
        text="",
        document_name="test.pdf",
        page_number=1,
    )

    assert chunks == []