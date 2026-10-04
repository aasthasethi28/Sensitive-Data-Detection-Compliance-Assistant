"""
qa.py

Enterprise RAG
Hugging Face Embeddings + FAISS + Gemini

Responsibilities:
- Build document vector stores
- Detect broad vs specific questions
- Retrieve relevant document chunks
- Filter weak retrieval results
- Generate grounded answers with Gemini
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

    # =====================================================
    # QUERY TYPE DETECTION
    # =====================================================

    @staticmethod
    def is_broad_query(question):

        question_lower = question.lower().strip()

        broad_keywords = [

            "what is this document",
            "what is the document",
            "what is this about",
            "what is the syllabus",
            "what does this document contain",
            "what does the document contain",
            "summarize",
            "summary",
            "overview",
            "give me an overview",
            "explain the document",
            "describe the document",
            "tell me about this document",
            "tell me about the document",
            "main topics",
            "all topics",
            "all sections",
            "list all",
            "entire document",
            "whole document"

        ]

        return any(
            keyword in question_lower
            for keyword in broad_keywords
        )


    # =====================================================
    # CREATE VECTOR STORE LAZILY
    # =====================================================

    @staticmethod
    def build_vector_store(document):

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


    # =====================================================
    # RETRIEVE RELEVANT CHUNKS
    # =====================================================

    @staticmethod
    def retrieve_chunks(
        question,
        document
    ):

        query_embedding = EmbeddingModel.encode(
            [question]
        )[0]

        total_chunks = len(
            document["chunks"]
        )

        # -------------------------------------------------
        # Candidate retrieval
        # -------------------------------------------------

        if DocumentQA.is_broad_query(
            question
        ):

            candidate_k = min(
                12,
                total_chunks
            )

        else:

            candidate_k = min(
                8,
                total_chunks
            )

        results = document["vector_store"].search(
            query_embedding,
            k=candidate_k
        )

        if not results:

            return []

        # -------------------------------------------------
        # Relevance filtering
        #
        # FAISS uses L2 distance.
        # Smaller distance = more similar.
        #
        # We use a generous threshold here because
        # embeddings are document-dependent.
        # -------------------------------------------------

        if DocumentQA.is_broad_query(
            question
        ):

            max_distance = 1.30

        else:

            max_distance = 1.00

        filtered_results = [

            result

            for result in results

            if result["distance"] <= max_distance

        ]

        # -------------------------------------------------
        # Safety fallback
        #
        # Never return an empty context merely because
        # the threshold was slightly too strict.
        # -------------------------------------------------

        if not filtered_results:

            filtered_results = results[:1]

        return filtered_results


    # =====================================================
    # ASK QUESTION
    # =====================================================

    @staticmethod
    def ask(
        question,
        document
    ):

        # =================================================
        # BUILD VECTOR STORE
        # =================================================

        DocumentQA.build_vector_store(
            document
        )

        # =================================================
        # RETRIEVE RELEVANT CHUNKS
        # =================================================

        results = DocumentQA.retrieve_chunks(
            question,
            document
        )

        # =================================================
        # HANDLE NO RESULTS
        # =================================================

        if not results:

            return {

                "answer": (
                    "I could not find relevant information "
                    "in the uploaded document."
                ),

                "sources": []

            }

        # =================================================
        # BUILD CONTEXT
        # =================================================

        context_parts = []

        sources = []

        for result in results:

            chunk = result["chunk"]

            distance = result["distance"]

            context_parts.append(
                chunk
            )

            sources.append(
                {
                    "chunk": chunk,
                    "distance": distance
                }
            )

        context = "\n\n".join(
            context_parts
        )

        # =================================================
        # PROMPT
        # =================================================

        prompt = f"""
You are an Enterprise AI Compliance Assistant.

Answer the user's question using ONLY the information
contained in the provided document context.

IMPORTANT RULES:

1. Do not use outside knowledge.

2. Do not invent information.

3. Do not make assumptions that are not supported
   by the document.

4. If the answer cannot be determined from the
   provided context, say exactly:

"I could not find that information in the uploaded document."

5. For broad questions or document-wide questions,
   synthesize information across the provided context.

6. For specific questions, focus only on information
   relevant to the user's question.

7. Do not mention information from unrelated sections
   unless it is necessary to answer the question.

8. Give a clear and professional answer.

=========================================================
DOCUMENT CONTEXT
=========================================================

{context}

=========================================================
USER QUESTION
=========================================================

{question}

=========================================================
ANSWER
=========================================================
"""

        # =================================================
        # GEMINI
        # =================================================

        model = genai.GenerativeModel(
            "gemini-2.5-flash"
        )

        response = model.generate_content(
            prompt
        )

        answer = response.text

        # =================================================
        # RETURN ANSWER + SOURCES
        # =================================================

        return {

            "answer": answer,

            "sources": sources

        }