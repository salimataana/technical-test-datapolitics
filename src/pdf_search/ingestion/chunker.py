def chunk_text(
    text: str,
    document_name: str,
    page_number: int,
    chunk_size: int = 1000,
    overlap: int = 150,
):
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

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
                "text": chunk,
            }
        )
        start += chunk_size - overlap

    return chunks