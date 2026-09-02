from pathlib import Path

import pymupdf


data_dir = Path("data")

for pdf_path in sorted(data_dir.glob("*.pdf")):
    document = pymupdf.open(pdf_path)

    page_count = len(document)
    total_chars = 0

    for page in document:
        text = page.get_text("text")
        total_chars += len(text.strip())

    document.close()

    print(f"{pdf_path.name}")
    print(f"  Pages : {page_count}")
    print(f"  Caractères extraits : {total_chars}")
    print()