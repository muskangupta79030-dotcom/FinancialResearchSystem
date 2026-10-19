from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os

from backend.services.seed_loader import load_seed_documents

from backend.agents.document_agent import DocumentAgent
from backend.agents.extraction_agent import ExtractionAgent
from backend.agents.red_flag_agent import RedFlagAgent
from backend.agents.research_agent import ResearchAgent
from backend.agents.comparison_agent import ComparisonAgent
from backend.agents.report_agent import ReportAgent

from backend.services.pdf_parser import extract_text_from_pdf
from backend.services.chunking import split_text_into_chunks
from backend.services.embeddings import generate_embeddings
from backend.services.vector_store import store_embeddings


app = FastAPI(
    title="Multi-Agent Financial Research System",
    description="Backend API for financial document analysis",
    version="1.0.0"
)


# =========================================================
# CORS CONFIGURATION
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():
    return {
        "message": "Financial Research Backend is running"
    }


# =========================================================
# DOCUMENT AGENT
# =========================================================

@app.get("/document/{document_name}")
def process_document(document_name: str):

    agent = DocumentAgent()

    return agent.process_document(document_name)


# =========================================================
# COMPLETE DOCUMENT PROCESSING PIPELINE
# =========================================================

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    upload_folder = "backend/data/uploads"

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    file_path = os.path.join(
        upload_folder,
        file.filename
    )

    # =====================================================
    # STEP 1: Save uploaded PDF
    # =====================================================

    with open(file_path, "wb") as buffer:

        content = await file.read()

        buffer.write(content)

    # =====================================================
    # STEP 2: Document Agent
    # =====================================================

    document_agent = DocumentAgent()

    document_result = document_agent.process_document(
        file.filename
    )

    # =====================================================
    # STEP 3: Extract text from PDF
    # =====================================================

    extracted_text = extract_text_from_pdf(
        file_path
    )

    # =====================================================
    # STEP 4: Extraction Agent
    # =====================================================

    extraction_agent = ExtractionAgent()

    extracted_metrics = extraction_agent.extract_metrics(
        extracted_text
    )

    # =====================================================
    # STEP 5: Red Flag Agent
    # =====================================================

    red_flag_agent = RedFlagAgent()

    red_flag_analysis = red_flag_agent.analyze(
        extracted_text,
        extracted_metrics
    )

    # =====================================================
    # STEP 6: Split document into chunks
    # =====================================================

    chunks = split_text_into_chunks(
        extracted_text
    )

    # =====================================================
    # STEP 7: Generate embeddings
    # =====================================================

    embeddings = generate_embeddings(
        chunks
    )

    # =====================================================
    # STEP 8: Store embeddings in ChromaDB
    # =====================================================

    stored_count = store_embeddings(
        chunks,
        embeddings,
        file.filename
    )

    # =====================================================
    # STEP 9: Return complete pipeline result
    # =====================================================

    return {

        "filename": file.filename,

        "pipeline": [
            "Document Agent",
            "Extraction Agent",
            "Red Flag Agent",
            "Embedding Generation",
            "Vector Database Storage"
        ],

        "document_agent": document_result,

        "extracted_metrics": extracted_metrics,

        "red_flag_analysis": red_flag_analysis,

        "document_processing": {

            "total_characters": len(
                extracted_text
            ),

            "total_chunks": len(
                chunks
            ),

            "embedding_count": len(
                embeddings
            ),

            "embedding_dimension": (
                len(embeddings[0])
                if embeddings
                else 0
            ),

            "stored_in_vector_database": stored_count
        },

        "first_chunk": (
            chunks[0]
            if chunks
            else ""
        )
    }


# =========================================================
# EXTRACTION ENDPOINT
# =========================================================

@app.post("/extract")
async def extract_metrics(
    file: UploadFile = File(...)
):

    upload_folder = "backend/data/uploads"

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    file_path = os.path.join(
        upload_folder,
        file.filename
    )

    # =====================================================
    # SAVE FILE
    # =====================================================

    with open(file_path, "wb") as buffer:

        content = await file.read()

        buffer.write(content)

    # =====================================================
    # EXTRACT TEXT
    # =====================================================

    text = extract_text_from_pdf(
        file_path
    )

    # =====================================================
    # EXTRACTION AGENT
    # =====================================================

    extraction_agent = ExtractionAgent()

    metrics = extraction_agent.extract_metrics(
        text
    )

    # =====================================================
    # RED FLAG AGENT
    # =====================================================

    red_flag_agent = RedFlagAgent()

    red_flag_analysis = red_flag_agent.analyze(
        text,
        metrics
    )

    return {

        "filename": file.filename,

        "extracted_metrics": metrics,

        "red_flag_analysis": red_flag_analysis
    }


# =========================================================
# RESEARCH AGENT
# =========================================================

@app.post("/research")
def research_documents(
    query: str,
    top_k: int = 5,
    filename: str = None
):

    research_agent = ResearchAgent()

    result = research_agent.research(
        query=query,
        top_k=top_k,
        filename=filename
    )

    return result


# =========================================================
# COMPARISON AGENT
# =========================================================

@app.post("/compare")
def compare_documents(
    company1: str,
    company2: str,
    query: str = (
        "Compare revenue, net income "
        "and operating income"
    ),
    top_k: int = 5
):

    comparison_agent = ComparisonAgent()

    result = comparison_agent.compare(
        company1=company1,
        company2=company2,
        query=query,
        top_k=top_k
    )

    return result


# =========================================================
# REPORT AGENT
# =========================================================

@app.post("/report")
def generate_financial_report(
    company_name: str,
    filename: str = None
):

    # =====================================================
    # FIND DOCUMENT
    # =====================================================

    if not filename:
        filename = company_name

    upload_folder = "backend/data/uploads"
    seed_folder = "backend/data/seed_documents"

    upload_path = os.path.join(
        upload_folder,
        filename
    )

    seed_path = os.path.join(
        seed_folder,
        filename
    )

    if os.path.exists(upload_path):

        file_path = upload_path

    elif os.path.exists(seed_path):

        file_path = seed_path

    else:

        return {
            "status": "error",
            "message": (
                f"Document '{filename}' was not found "
                "in the uploaded or seed document folders."
            )
        }

    # =====================================================
    # EXTRACT DOCUMENT TEXT
    # =====================================================

    text = extract_text_from_pdf(
        file_path
    )

    if not text:

        return {
            "status": "error",
            "message": (
                "No text could be extracted "
                "from the selected document."
            ),
            "filename": filename
        }

    # =====================================================
    # EXTRACTION AGENT
    # =====================================================

    extraction_agent = ExtractionAgent()

    extracted_metrics = extraction_agent.extract_metrics(
        text
    )

    # =====================================================
    # RED FLAG AGENT
    # =====================================================

    red_flag_agent = RedFlagAgent()

    red_flag_analysis = red_flag_agent.analyze(
        text,
        extracted_metrics
    )

    # =====================================================
    # REPORT AGENT
    # =====================================================

    report_agent = ReportAgent()

    report = report_agent.generate_report(
        company_name=company_name,
        extracted_metrics=extracted_metrics,
        red_flag_analysis=red_flag_analysis
    )

    return {
        "filename": filename,
        "report": report
    }


# =========================================================
# LOAD SEED DOCUMENTS
# =========================================================

@app.post("/seed-documents/load")
def load_seed_data():

    load_seed_documents()

    return {
        "message": "Seed documents loaded successfully"
    }
