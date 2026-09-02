from pathlib import Path

from pdf_search.search.faiss_store import load_index, load_metadata
from pdf_search.ingestion.embedder import create_embeddings
from pdf_search.search.faiss_store import search_index


index = load_index(Path("storage/index.faiss"))
metadata = load_metadata(Path("storage/metadata.json"))

print("Nombre de vecteurs :", index.ntotal)
print("Nombre de métadonnées :", len(metadata))

query = "Qui a signé la convention de mécénat ?"

query_embedding = create_embeddings([query])

scores, indices = search_index(
    index,
    query_embedding,
    top_k=5,
)

print("Indices trouvés :", indices)
print("Scores :", scores)

for score, index in zip(scores, indices):
    result = metadata[index]

    print("\n--- Résultat ---")
    print("Score :", score)
    print("Document :", result["document_name"])
    print("Page :", result["page_number"])
    print("Chunk :", result["chunk_index"])
    print("Texte :", result["text"])