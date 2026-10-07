from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, File, UploadFile
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

from modules.document_manager import DocumentManager
from modules.qa import DocumentQA


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Enterprise AI Compliance Assistant",
    description=(
        "AI-powered sensitive data detection, risk assessment, "
        "compliance, and RAG platform."
    ),
    version="1.0.0"
)


# =========================================================
# TEMPORARY DOCUMENT STORE
# =========================================================

document_store = {}


# =========================================================
# CHAT REQUEST MODEL
# =========================================================

class ChatRequest(BaseModel):

    document_id: str

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

    # -----------------------------------------------------
    # Normalize uploaded-file representation for Swagger UI
    # -----------------------------------------------------
    #
    # FastAPI/Pydantic currently generates:
    #
    # {
    #     "type": "string",
    #     "contentMediaType": "application/octet-stream"
    # }
    #
    # Swagger UI in this environment displays that as a
    # text field instead of a file selector.
    #
    # Convert it to the OpenAPI binary representation:
    #
    # {
    #     "type": "string",
    #     "format": "binary"
    # }
    # -----------------------------------------------------

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

    document_id = str(
        uuid4()
    )

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

    manager = DocumentManager()

    documents = []

    for file in files:

        document = manager.process_document(
            file
        )

        document_id = str(
            uuid4()
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

        "total_documents": len(
            documents
        ),

        "documents": documents
    }


# =========================================================
# CHAT / RAG
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