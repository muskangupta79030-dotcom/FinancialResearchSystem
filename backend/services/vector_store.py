import chromadb

client = chromadb.PersistentClient(
    path="backend/data/chroma_db"
)

collection = client.get_or_create_collection(
    name="financial_documents"
)


def store_embeddings(chunks, embeddings, filename):
    """
    Store document chunks and their embeddings in ChromaDB.
    """

    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        collection.add(
            ids=[f"{filename}_{i}"],
            documents=[chunk],
            embeddings=[embedding],
            metadatas=[
                {
                    "filename": filename,
                    "chunk_index": i
                }
            ]
        )

    return len(chunks)


def search_documents(query_embedding, top_k=5, filename=None):
    """
    Search the vector database for the most relevant document chunks.
    """

    where_filter = None

    if filename:
        where_filter = {
            "filename": filename
        }

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    retrieved_chunks = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):
        retrieved_chunks.append(
            {
                "document": document,
                "filename": metadata.get("filename", "Unknown"),
                "chunk_index": metadata.get("chunk_index", -1),
                "distance": distance
            }
        )

    return retrieved_chunks
