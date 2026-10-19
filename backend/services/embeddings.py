from sentence_transformers import SentenceTransformer

_model = None


def get_model():
    global _model

    if _model is None:
        _model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            device="cpu"
        )

    return _model


def generate_embeddings(chunks):
    if not chunks:
        return []

    model = get_model()

    embeddings = model.encode(
        chunks,
        batch_size=4,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=False
    )

    return embeddings.tolist()
