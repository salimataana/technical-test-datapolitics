import faiss
import json

def create_index(embeddings):
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return index

def save_index(index, output_path):
    faiss.write_index(index, str(output_path))


def load_index(input_path):
    return faiss.read_index(str(input_path))


def save_metadata(metadata, output_path):
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)


def load_metadata(input_path):
    with open(input_path, "r", encoding="utf-8") as file:
        return json.load(file)


def search_index(index, query_embedding, top_k=5):
    scores, indices = index.search(query_embedding, top_k)
    return scores[0], indices[0]