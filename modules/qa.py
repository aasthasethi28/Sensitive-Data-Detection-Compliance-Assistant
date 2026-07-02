"""
qa.py

Enterprise RAG
Gemini + FAISS
"""

import os
import google.generativeai as genai

from dotenv import load_dotenv

from modules.utils import TextChunker
from modules.embeddings import EmbeddingModel
from modules.vector_store import VectorStore

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)


class DocumentQA:

    @staticmethod
    def ask(question, document):

        # Build FAISS only once (Lazy Loading)

        if document["vector_store"] is None:

            chunks = TextChunker.split(
                document["text"]
            )

            embeddings = EmbeddingModel.encode(
                chunks
            )

            vector_store = VectorStore(
                embeddings.shape[1]
            )

            vector_store.add(
                embeddings,
                chunks
            )

            document["chunks"] = chunks
            document["vector_store"] = vector_store

        # Create Question Embedding

        query_embedding = EmbeddingModel.encode(
            [question]
        )[0]

        # Retrieve Context

        context = document["vector_store"].search(
            query_embedding,
            k=6
        )

        context = "\n\n".join(context)

        # Gemini Prompt

        prompt = f"""
You are an Enterprise AI Compliance Assistant.

Use ONLY the information contained in the uploaded document.

If the answer cannot be found in the document, reply exactly:

'I could not find that information in the uploaded document.'

Answer professionally.

Document Context:

{context}

Question:

{question}

Answer:
"""

        # Gemini

        model = genai.GenerativeModel(
            "gemini-2.5-flash"
        )

        response = model.generate_content(
            prompt
        )

        return response.text