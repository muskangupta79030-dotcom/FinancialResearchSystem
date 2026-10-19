from pydantic import BaseModel


class Document(BaseModel):
    filename: str
    status: str
    total_characters: int
    total_chunks: int
