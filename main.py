
"""
main.py

Enterprise AI Compliance Assistant

FastAPI backend supporting:
- Single document upload
- Multiple document upload
- Sensitive data detection
- Risk classification
- AI compliance reports
- Single-document RAG
- Multi-document RAG
- Persistent SQLite storage
- Persistent FAISS indexes
"""

from contextlib import asynccontextmanager
from typing import Annotated
from uuid import uuid4

from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException
)

from fastapi.openapi.utils import get_openapi

from pydantic import BaseModel

from modules.document_manager import DocumentManager
from modules.qa import DocumentQA
from modules.storage import DocumentStorage


# =========================================================
# TEMPORARY IN-MEMORY DOCUMENT CACHE
# =========================================================

document_store = {}


# =========================================================
# APPLICATION LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Initialize SQLite and storage directories.

    DocumentStorage.initialize()

    # Restore previously saved documents.

    restored_documents = DocumentStorage.load_documents()

    document_store.update(
        restored_documents
    )

    print(
        f"Restored {len(document_store)} documents from storage."
    )

    yield


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Enterprise AI Compliance Assistant",
    description=(
        "AI-powered sensitive data detection, risk assessment, "
        "compliance, and RAG platform."
    ),
    version="1.0.0",
    lifespan=lifespan
)


# =========================================================
# CHAT REQUEST MODEL
# =========================================================

class ChatRequest(BaseModel):

    document_ids: list[str]

    question: str


# =========================================================
# CUSTOM OPENAPI SCHEMA
# =========================================================

def custom_openapi():

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes
    )

    schemas = openapi_schema.get(
        "components",
        {}
    ).get(
        "schemas",
        {}
    )

    for schema in schemas.values():

        properties = schema.get(
            "properties",
            {}
        )

        for property_schema in properties.values():

            if (
                property_schema.get("type") == "array"
                and "items" in property_schema
            ):

                items = property_schema["items"]

                if (
                    items.get("type") == "string"
                    and items.get(
                        "contentMediaType"
                    ) == "application/octet-stream"
                ):

                    items.pop(
                        "contentMediaType",
                        None
                    )

                    items["format"] = "binary"

    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi


# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get("/")
def root():

    return {
        "message": (
            "Enterprise AI Compliance Assistant API is running"
        ),
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
# LIST PERSISTED DOCUMENTS
# =========================================================

@app.get("/documents")
def list_documents():

    documents = DocumentStorage.list_documents()

    return {
        "status": "success",
        "total_documents": len(documents),
        "documents": documents
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

    document["document_id"] = document_id

    # Save document permanently in SQLite.

    DocumentStorage.save_document(
        document_id,
        document
    )

    # Keep document available during current execution.

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
    files: Annotated[
        list[UploadFile],
        File(
            description="Upload multiple documents"
        )
    ]
):

    if not files:

        raise HTTPException(
            status_code=400,
            detail="At least one document must be uploaded."
        )

    manager = DocumentManager()

    documents = []

    for file in files:

        document = manager.process_document(
            file
        )

        document_id = str(uuid4())

        document["document_id"] = document_id

        # Persist each document separately.

        DocumentStorage.save_document(
            document_id,
            document
        )

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
# CHAT - SINGLE DOCUMENT + MULTI-DOCUMENT RAG
# =========================================================

@app.post("/chat")
async def chat(
    request: ChatRequest
):

    # =====================================================
    # VALIDATE QUESTION
    # =====================================================

    if not request.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )


    # =====================================================
    # VALIDATE DOCUMENT IDS
    # =====================================================

    if not request.document_ids:

        raise HTTPException(
            status_code=400,
            detail="Select at least one document."
        )


    # Remove duplicate IDs while preserving order.

    selected_ids = list(
        dict.fromkeys(
            request.document_ids
        )
    )

    selected_documents = []

    missing_ids = []

    for document_id in selected_ids:

        document = document_store.get(
            document_id
        )

        if document is None:

            missing_ids.append(
                document_id
            )

        else:

            selected_documents.append(
                document
            )


    # =====================================================
    # HANDLE INVALID DOCUMENT IDS
    # =====================================================

    if missing_ids:

        raise HTTPException(
            status_code=404,
            detail={
                "message": "Some selected documents were not found.",
                "missing_document_ids": missing_ids
            }
        )


    # =====================================================
    # SINGLE-DOCUMENT RAG
    # =====================================================

    if len(selected_documents) == 1:

        result = DocumentQA.ask(
            request.question,
            selected_documents[0]
        )

        sources = [

            {
                **source,
                "document_id": selected_ids[0]
            }

            for source in result["sources"]

        ]


    # =====================================================
    # MULTI-DOCUMENT RAG
    # =====================================================

    else:

        result = DocumentQA.ask_multiple(
            request.question,
            selected_documents
        )

        sources = result["sources"]


    # =====================================================
    # PERSIST FAISS INDEXES
    # =====================================================

    for document_id, document in zip(
        selected_ids,
        selected_documents
    ):

        if document.get("vector_store") is not None:

            DocumentStorage.save_vector_store(
                document_id,
                document
            )


    # =====================================================
    # RETURN RESPONSE
    # =====================================================

    return {

        "status": "success",

        "document_ids": selected_ids,

        "total_documents": len(selected_documents),

        "question": request.question,

        "answer": result["answer"],

        "sources": sources

    }
