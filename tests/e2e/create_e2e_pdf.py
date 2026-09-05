import sys
from pathlib import Path

import pymupdf


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: create_e2e_pdf.py OUTPUT_PATH")

    output_path = Path(sys.argv[1])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    document = pymupdf.open()
    page = document.new_page()
    page.insert_text(
        (72, 100),
        "Datapolitics Docker end-to-end test. This document verifies semantic search.",
        fontsize=14,
    )
    document.save(output_path)
    document.close()


if __name__ == "__main__":
    main()
