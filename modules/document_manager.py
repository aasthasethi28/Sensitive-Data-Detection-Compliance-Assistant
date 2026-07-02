import os

from modules.parser import DocumentParser
from modules.cleaner import TextCleaner

from modules.detector.detector import SensitiveDataDetector

from modules.classifier import RiskClassifier
from modules.compliance import ComplianceGenerator


class DocumentManager:

    def __init__(self):

        self.documents = []

    # Save uploaded file

    def save_uploaded_file(self, uploaded_file):

        os.makedirs("uploads", exist_ok=True)

        file_path = os.path.join(
            "uploads",
            uploaded_file.name
        )

        with open(file_path, "wb") as file:
            file.write(uploaded_file.getbuffer())

        return file_path

    # Process one document

    def process_document(self, uploaded_file):

        # Save file
        file_path = self.save_uploaded_file(uploaded_file)

        # Parse
        raw_text = DocumentParser.parse(file_path)

        # Clean
        clean_text = TextCleaner.clean(raw_text)

        # Sensitive Data Detection
        detections = SensitiveDataDetector.detect(
            clean_text
        )

        # Risk Classification
        risk = RiskClassifier.classify_document(
            detections
        )

        # Compliance Report
        report = ComplianceGenerator.generate(
            clean_text,
            detections,
            risk
        )

        # Lazy Loading
        # These will be created only when the chatbot is used.
        document = {

            "filename": uploaded_file.name,

            "text": clean_text,

            "detections": detections,

            "risk": risk,

            "report": report,

            "chunks": None,

            "vector_store": None

        }

        self.documents.append(document)

        return document

    # Process multiple documents

    def process_documents(self, uploaded_files):

        self.documents = []

        for uploaded_file in uploaded_files:

            self.process_document(uploaded_file)

        return self.documents