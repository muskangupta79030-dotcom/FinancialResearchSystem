import os

from backend.services.pdf_parser import extract_text_from_pdf
from backend.services.chunking import split_text_into_chunks
from backend.services.embeddings import generate_embeddings
from backend.services.vector_store import store_embeddings


def load_seed_documents():

    seed_folder = "backend/data/seed_documents"

    for filename in os.listdir(seed_folder):

        if filename.lower().endswith(".pdf"):

            file_path = os.path.join(seed_folder, filename)

            print(f"Processing: {filename}")

            text = extract_text_from_pdf(file_path)

            chunks = split_text_into_chunks(text)

            embeddings = generate_embeddings(chunks)

            store_embeddings(
                chunks,
                embeddings,
                filename
            )

            print(f"Completed: {filename}")
