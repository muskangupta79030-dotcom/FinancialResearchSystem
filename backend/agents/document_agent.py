class DocumentAgent:

    def process_document(self, document_name):
        return {
            "document": document_name,
            "agent": "Document Agent",
            "status": "Document received successfully",
            "processing_steps": [
                "PDF Parsing",
                "Text Chunking",
                "Embedding Generation",
                "Vector Database Storage"
            ]
        }
