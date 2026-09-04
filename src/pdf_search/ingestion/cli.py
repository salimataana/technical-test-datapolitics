import sys
from pathlib import Path

from pdf_search.ingestion.chunker import chunk_text
from pdf_search.ingestion.extractor import extract_text_from_pdf
from pdf_search.ingestion.embedder import create_embeddings
from pdf_search.search.faiss_store import create_index, save_index, save_metadata


def main():
    input_folder = sys.argv[1]
    pdf_folder = Path(input_folder)
    pdf_files = list(pdf_folder.glob("*.pdf"))

    print("Nombre de PDF trouvés :", len(pdf_files))
    print("Dossier reçu :", input_folder)

    all_chunks = []

    # Statistiques d'extraction
    total_pages = 0
    ocr_pages = 0

    for pdf_file in pdf_files:
        pages = extract_text_from_pdf(pdf_file)

        total_pages += len(pages)

        ocr_count = sum(
            1
            for page in pages
            if page["extraction_method"] == "ocr"
        )

        ocr_pages += ocr_count

        print(
            pdf_file.name,
            "→",
            len(pages),
            "pages",
            "| OCR :",
            ocr_count,
        )

        for page in pages:
            chunks = chunk_text(
                page["text"],
                page["document_name"],
                page["page_number"],
                extraction_method=page["extraction_method"],
            )

            all_chunks.extend(chunks)

            print(
                "   Page",
                page["page_number"],
                "Méthode :", page["extraction_method"],
                "→",
                len(chunks),
                "chunks",
            )

    # Création des embeddings dans le même ordre que les chunks
    texts = [chunk["text"] for chunk in all_chunks]
    embeddings = create_embeddings(texts)

    # Création de l'index FAISS
    index = create_index(embeddings)

    # Création des métadonnées avec l'identifiant du vecteur
    metadata = []

    for vector_id, chunk in enumerate(all_chunks):
        metadata.append(
            {
                "vector_id": vector_id,
                "document_name": chunk["document_name"],
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
                "extraction_method": chunk["extraction_method"],
                "text": chunk["text"],
            }
        )

    # Création du dossier de sortie s'il n'existe pas
    output_dir = Path("storage")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sauvegarde de l'index FAISS
    index_path = output_dir / "index.faiss"
    save_index(index, index_path)

    # Sauvegarde des métadonnées
    metadata_path = output_dir / "metadata.json"
    save_metadata(metadata, metadata_path)

    print("Metadata sauvegardées :", metadata_path)
    print("Index FAISS sauvegardé :", index_path)
    print("Nombre de vecteurs dans FAISS :", index.ntotal)
    print("Nombre d'embeddings :", len(embeddings))
    print("Nombre total de chunks :", len(all_chunks))
    print("Nombre total de pages :", total_pages)
    print("Nombre de pages avec OCR :", ocr_pages)


if __name__ == "__main__":
    main()