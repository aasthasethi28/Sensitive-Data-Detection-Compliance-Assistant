from uuid import uuid4

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

from modules.document_manager import DocumentManager
from modules.qa import DocumentQA


app = FastAPI(
    title="Enterprise AI Compliance Assistant",
    description="AI-powered sensitive data detection, risk assessment, compliance, and RAG platform.",
    version="1.0.0"
)


# =========================================================
# IN-MEMORY DOCUMENT STORE
# =========================================================

document_store = {}


# =========================================================
# CHAT REQUEST MODEL
# =========================================================

class ChatRequest(BaseModel):

    document_id: str

    question: str


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "Enterprise AI Compliance Assistant API is running",
        "status": "success"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }


# =========================================================
# SINGLE DOCUMENT UPLOAD
# =========================================================

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    manager = DocumentManager()

    document = manager.process_document(
        file
    )

    document_id = str(uuid4())

    document_store[document_id] = document

    return {

        "status": "success",

        "document": {

            "document_id": document_id,

            "filename": document["filename"],

            "detections": document["detections"],

            "risk": document["risk"],

            "report": document["report"]

        }

    }


# =========================================================
# MULTIPLE DOCUMENT UPLOAD
# =========================================================

@app.post("/documents/upload-multiple")
async def upload_multiple_documents(
    files: list[UploadFile] = File(...)
):

    manager = DocumentManager()

    documents = []

    for file in files:

        document = manager.process_document(
            file
        )

        document_id = str(uuid4())

        document_store[document_id] = document

        documents.append(

            {

                "document_id": document_id,

                "filename": document["filename"],

                "detections": document["detections"],

                "risk": document["risk"],

                "report": document["report"]

            }

        )

    return {

        "status": "success",

        "total_documents": len(documents),

        "documents": documents

    }


# =========================================================
# RAG CHAT
# =========================================================

@app.post("/chat")
async def chat(
    request: ChatRequest
):

    document = document_store.get(
        request.document_id
    )

    if document is None:

        return {

            "status": "error",

            "message": "Document not found."

        }

    if not request.question.strip():

        return {

            "status": "error",

            "message": "Question cannot be empty."

        }

    result = DocumentQA.ask(

        request.question,

        document

    )

    return {

        "status": "success",

        "document_id": request.document_id,

        "question": request.question,

        "answer": result["answer"],

        "sources": result["sources"]

    }