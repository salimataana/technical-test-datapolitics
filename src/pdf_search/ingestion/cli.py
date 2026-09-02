import sys
from pathlib import Path

from pdf_search.ingestion.chunker import chunk_text
from pdf_search.ingestion.extractor import extract_text_from_pdf
from pdf_search.ingestion.embedder import create_embeddings
from pdf_search.search.faiss_store import create_index
from pdf_search.search.faiss_store import save_index
from pdf_search.search.faiss_store import save_metadata



def main():
    input_folder = sys.argv[1]
    pdf_folder = Path(input_folder)
    pdf_files = list(pdf_folder.glob("*.pdf"))

    print("Nombre de PDF trouvés :", len(pdf_files))
    print("Dossier reçu :", input_folder)

    all_chunks = []

    for pdf_file in pdf_files:
        pages = extract_text_from_pdf(pdf_file)
        print(pdf_file.name, "→", len(pages), "pages")

        for page in pages:
            chunks = chunk_text(
                page["text"],
                page["document_name"],
                page["page_number"],
            )

            all_chunks.extend(chunks)

            print("   Page", page["page_number"], "→", len(chunks), "chunks")

    texts = [chunk["text"] for chunk in all_chunks]
    embeddings = create_embeddings(texts)
    index = create_index(embeddings)
    output_path = Path("storage/index.faiss")
    save_index(index, output_path)
    metadata_path = Path("storage/metadata.json")
    save_metadata(all_chunks, metadata_path)
    print("Metadata sauvegardées :", metadata_path)
    print("Index FAISS sauvegardé :", output_path)
    print("Nombre de vecteurs dans FAISS :", index.ntotal)
    print("Nombre d'embeddings :", len(embeddings))

    print("Nombre total de chunks :", len(all_chunks))