
"""
storage.py

Persistent storage layer for Enterprise AI Compliance Assistant.

Responsibilities:
- Initialize SQLite database
- Save processed document metadata and extracted text
- Persist sensitive-data detections and risk assessments
- Save compliance reports
- Persist FAISS vector indexes
- Restore documents and vector indexes after server restart
"""

import json
import re
import sqlite3

from pathlib import Path

import faiss

from modules.vector_store import VectorStore


# =========================================================
# STORAGE CONFIGURATION
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

STORAGE_DIR = PROJECT_ROOT / "storage"

DATABASE_PATH = STORAGE_DIR / "documents.db"

FAISS_DIR = STORAGE_DIR / "faiss_indexes"


class DocumentStorage:

    # =====================================================
    # DATABASE CONNECTION
    # =====================================================

    @staticmethod
    def get_connection():

        connection = sqlite3.connect(
            DATABASE_PATH,
            timeout=30
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        return connection


    # =====================================================
    # INITIALIZE STORAGE
    # =====================================================

    @classmethod
    def initialize(cls):

        STORAGE_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        FAISS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        connection = cls.get_connection()

        try:

            connection.execute(
                "PRAGMA journal_mode = WAL"
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (

                    document_id TEXT PRIMARY KEY,

                    filename TEXT NOT NULL,

                    source_json TEXT NOT NULL,

                    text_content TEXT NOT NULL,

                    detections_json TEXT NOT NULL,

                    risk_json TEXT NOT NULL,

                    report TEXT,

                    chunks_json TEXT,

                    index_path TEXT,

                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP

                )
                """
            )

            connection.commit()

        finally:

            connection.close()


    # =====================================================
    # JSON SERIALIZATION
    # =====================================================

    @staticmethod
    def serialize(data):

        return json.dumps(
            data,
            ensure_ascii=False,
            default=str
        )


    # =====================================================
    # SAVE DOCUMENT
    # =====================================================

    @classmethod
    def save_document(
        cls,
        document_id,
        document
    ):

        if not document_id:

            raise ValueError(
                "Document ID cannot be empty."
            )

        connection = cls.get_connection()

        try:

            connection.execute(
                """
                INSERT INTO documents (

                    document_id,
                    filename,
                    source_json,
                    text_content,
                    detections_json,
                    risk_json,
                    report

                )

                VALUES (?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(document_id)

                DO UPDATE SET

                    filename = excluded.filename,

                    source_json = excluded.source_json,

                    text_content = excluded.text_content,

                    detections_json = excluded.detections_json,

                    risk_json = excluded.risk_json,

                    report = excluded.report,

                    updated_at = CURRENT_TIMESTAMP

                """,

                (

                    document_id,

                    document["filename"],

                    cls.serialize(
                        document.get("source", {})
                    ),

                    document["text"],

                    cls.serialize(
                        document["detections"]
                    ),

                    cls.serialize(
                        document["risk"]
                    ),

                    document["report"]

                )

            )

            connection.commit()

        finally:

            connection.close()


    # =====================================================
    # SAVE FAISS VECTOR INDEX
    # =====================================================

    @classmethod
    def save_vector_store(
        cls,
        document_id,
        document
    ):

        vector_store = document.get(
            "vector_store"
        )

        if vector_store is None:

            raise ValueError(
                "Document does not have a built vector store."
            )

        safe_document_id = re.sub(
            r"[^a-zA-Z0-9_-]",
            "_",
            document_id
        )

        index_path = FAISS_DIR / (
            f"{safe_document_id}.faiss"
        )

        chunks = document.get(
            "chunks"
        )

        if chunks is None:

            chunks = vector_store.documents

        # Save FAISS index to disk.

        faiss.write_index(
            vector_store.index,
            str(index_path)
        )

        connection = cls.get_connection()

        try:

            cursor = connection.execute(
                """
                UPDATE documents

                SET

                    chunks_json = ?,

                    index_path = ?,

                    updated_at = CURRENT_TIMESTAMP

                WHERE document_id = ?

                """,

                (

                    cls.serialize(chunks),

                    str(index_path),

                    document_id

                )

            )

            if cursor.rowcount == 0:

                raise ValueError(
                    f"Document {document_id} is not registered in SQLite."
                )

            connection.commit()

        finally:

            connection.close()


    # =====================================================
    # LOAD ALL DOCUMENTS
    # =====================================================

    @classmethod
    def load_documents(cls):

        connection = cls.get_connection()

        try:

            rows = connection.execute(
                """
                SELECT *
                FROM documents
                ORDER BY created_at ASC
                """
            ).fetchall()

        finally:

            connection.close()


        documents = {}

        for row in rows:

            document_id = row["document_id"]

            chunks = (

                json.loads(
                    row["chunks_json"]
                )

                if row["chunks_json"]

                else None

            )

            document = {

                "document_id": document_id,

                "filename": row["filename"],

                "source": json.loads(
                    row["source_json"]
                ),

                "text": row["text_content"],

                "detections": json.loads(
                    row["detections_json"]
                ),

                "risk": json.loads(
                    row["risk_json"]
                ),

                "report": row["report"],

                "chunks": None,

                "vector_store": None,

                "created_at": row["created_at"]

            }


            # =================================================
            # RESTORE FAISS INDEX
            # =================================================

            index_path_value = row["index_path"]

            if (
                index_path_value
                and chunks is not None
            ):

                index_path = Path(
                    index_path_value
                )

                if index_path.is_file():

                    index = faiss.read_index(
                        str(index_path)
                    )

                    if index.ntotal != len(chunks):

                        raise ValueError(
                            f"FAISS index and chunk count mismatch "
                            f"for document {document_id}."
                        )

                    vector_store = VectorStore(
                        index.d
                    )

                    vector_store.index = index

                    vector_store.documents = chunks

                    document["chunks"] = chunks

                    document["vector_store"] = vector_store


            documents[document_id] = document


        return documents


    # =====================================================
    # GET ONE DOCUMENT
    # =====================================================

    @classmethod
    def get_document(
        cls,
        document_id
    ):

        documents = cls.load_documents()

        return documents.get(
            document_id
        )


    # =====================================================
    # LIST STORED DOCUMENTS
    # =====================================================

    @classmethod
    def list_documents(cls):

        connection = cls.get_connection()

        try:

            rows = connection.execute(
                """
                SELECT
                    document_id,
                    filename,
                    created_at,
                    updated_at

                FROM documents

                ORDER BY created_at DESC
                """
            ).fetchall()

        finally:

            connection.close()

        return [

            dict(row)

            for row in rows

        ]
