"""
document_manager.py

Responsible for processing uploaded documents.

Workflow

Upload
    ↓
Parser
    ↓
Cleaner
    ↓
Sensitive Data Detection
    ↓
Risk Classification
    ↓
Compliance Report

NOTE:
Embeddings and Vector Store are NOT created here.
They are created lazily when the user asks the first question.
"""

import os

from modules.parser import DocumentParser
from modules.cleaner import TextCleaner

from modules.detector.detector import SensitiveDataDetector

from modules.classifier import RiskClassifier
from modules.compliance import ComplianceGenerator


class DocumentManager:

    def __init__(self):

        self.documents = []

    def save_uploaded_file(self, uploaded_file):

        os.makedirs("uploads", exist_ok=True)

        file_path = os.path.join(
            "uploads",
            uploaded_file.filename
            if hasattr(uploaded_file, "filename")
            else uploaded_file.name
        )

        # FastAPI UploadFile
        if hasattr(uploaded_file, "file"):

            with open(file_path, "wb") as file:

                file.write(
                    uploaded_file.file.read()
                )

        # Streamlit UploadedFile
        else:

            with open(file_path, "wb") as file:

                file.write(
                    uploaded_file.getbuffer()
                )

        return file_path

    def process_document(self, uploaded_file):

        file_path = self.save_uploaded_file(
            uploaded_file
        )

        raw_text = DocumentParser.parse(
            file_path
        )

        clean_text = TextCleaner.clean(
            raw_text
        )

        detections = SensitiveDataDetector.detect(
            clean_text
        )

        risk = RiskClassifier.classify_document(
            detections
        )

        report = ComplianceGenerator.generate(
            clean_text,
            detections,
            risk
        )

        filename = (
            uploaded_file.filename
            if hasattr(uploaded_file, "filename")
            else uploaded_file.name
        )

        document = {

            "filename": filename,

            "text": clean_text,

            "detections": detections,

            "risk": risk,

            "report": report,

            "chunks": None,

            "vector_store": None

        }

        self.documents.append(
            document
        )

        return document

    def process_documents(self, uploaded_files):

        self.documents = []

        for uploaded_file in uploaded_files:

            self.process_document(
                uploaded_file
            )

        return self.documents