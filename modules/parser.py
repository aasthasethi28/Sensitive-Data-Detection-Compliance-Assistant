from pathlib import Path

import fitz          
import pandas as pd
from docx import Document


class DocumentParser:
    """
    A utility class responsible for extracting
    text from different document formats.
    """

    @staticmethod
    def parse_pdf(file_path):
        """Extract text from PDF."""

        text = ""

        pdf = fitz.open(file_path)

        for page in pdf:
            text += page.get_text()

        pdf.close()

        return text


    @staticmethod
    def parse_txt(file_path):
        """Read TXT file."""

        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()


    @staticmethod
    def parse_csv(file_path):
        """Convert CSV into readable text."""

        df = pd.read_csv(file_path)

        text = ""

        for _, row in df.iterrows():

            row_text = ""

            for column in df.columns:

                row_text += f"{column}: {row[column]} | "

            text += row_text + "\n"

        return text


    @staticmethod
    def parse_docx(file_path):
        """Extract text from DOCX."""

        document = Document(file_path)

        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )


    @staticmethod
    def parse(file_path):
        """
        Automatically determine
        document type.
        """

        extension = Path(file_path).suffix.lower()

        if extension == ".pdf":
            return DocumentParser.parse_pdf(file_path)

        elif extension == ".txt":
            return DocumentParser.parse_txt(file_path)

        elif extension == ".csv":
            return DocumentParser.parse_csv(file_path)

        elif extension == ".docx":
            return DocumentParser.parse_docx(file_path)

        else:
            raise ValueError(
                f"Unsupported file format: {extension}"
            )