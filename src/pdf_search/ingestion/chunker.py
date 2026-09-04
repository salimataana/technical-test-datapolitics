def chunk_text(
    text: str,
    document_name: str,
    page_number: int,
    extraction_method: str = "text",
    chunk_size: int = 1000,
    overlap: int = 150,
):
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between 0 and chunk_size - 1")

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        chunks.append(
            {
                "document_name": document_name,
                "page_number": page_number,
                "chunk_index": len(chunks),
                "extraction_method": extraction_method,
                "text": chunk,
            }
        )
        start += chunk_size - overlap

    return chunks
