"""
qa.py

Enterprise RAG
Hugging Face Embeddings + FAISS + Gemini

Responsibilities:
- Build document vector stores
- Detect broad vs specific questions
- Retrieve relevant document chunks
- Combine semantic and lexical relevance
- Generate grounded answers with Gemini
- Support single-document and multi-document RAG
- Return source metadata
"""

import os
import re

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
    # STOPWORDS
    # =====================================================

    STOPWORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "does",
        "do",
        "for",
        "from",
        "give",
        "how",
        "in",
        "include",
        "included",
        "is",
        "it",
        "me",
        "of",
        "on",
        "or",
        "please",
        "the",
        "this",
        "to",
        "under",
        "what",
        "which",
        "with",
        "within",
        "would"
    }


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
    # QUERY TOKENIZATION
    # =====================================================

    @staticmethod
    def extract_keywords(text):

        words = re.findall(
            r"\b[a-zA-Z0-9][a-zA-Z0-9_-]*\b",
            text.lower()
        )

        keywords = [

            word

            for word in words

            if (
                len(word) > 1
                and word not in DocumentQA.STOPWORDS
            )

        ]

        return set(keywords)


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
    # CALCULATE KEYWORD RELEVANCE
    # =====================================================

    @staticmethod
    def calculate_keyword_score(
        question,
        chunk
    ):

        question_keywords = DocumentQA.extract_keywords(
            question
        )

        chunk_keywords = DocumentQA.extract_keywords(
            chunk
        )

        if not question_keywords:

            return 0.0, False

        matched_keywords = (
            question_keywords
            & chunk_keywords
        )

        keyword_ratio = (
            len(matched_keywords)
            / len(question_keywords)
        )

        # -------------------------------------------------
        # Exact phrase matching
        # -------------------------------------------------

        normalized_question = " ".join(
            question.lower().split()
        )

        normalized_chunk = " ".join(
            chunk.lower().split()
        )

        phrase_match = False

        if len(question_keywords) >= 2:

            ordered_keywords = [
                word
                for word in re.findall(
                    r"\b[a-zA-Z0-9][a-zA-Z0-9_-]*\b",
                    question.lower()
                )
                if (
                    word not in DocumentQA.STOPWORDS
                    and len(word) > 1
                )
            ]

            if len(ordered_keywords) >= 2:

                phrase = " ".join(
                    ordered_keywords
                )

                phrase_match = (
                    phrase in normalized_chunk
                )

        return keyword_ratio, phrase_match


    # =====================================================
    # HYBRID RETRIEVAL
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

        if total_chunks == 0:

            return []


        # =================================================
        # BROAD QUERY
        # =================================================

        if DocumentQA.is_broad_query(
            question
        ):

            candidate_k = min(
                12,
                total_chunks
            )

            results = document["vector_store"].search(
                query_embedding,
                k=candidate_k
            )

            return results


        # =================================================
        # SPECIFIC QUERY
        # =================================================

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


        # =================================================
        # HYBRID SCORING
        # =================================================

        ranked_results = []

        for result in results:

            chunk = result["chunk"]

            distance = result["distance"]

            # -------------------------------------------------
            # Semantic relevance
            # -------------------------------------------------

            semantic_score = (
                1.0
                / (1.0 + distance)
            )

            # -------------------------------------------------
            # Keyword relevance
            # -------------------------------------------------

            keyword_ratio, phrase_match = (
                DocumentQA.calculate_keyword_score(
                    question,
                    chunk
                )
            )

            # -------------------------------------------------
            # Hybrid score
            # -------------------------------------------------

            hybrid_score = (
                0.35 * semantic_score
                + 0.40 * keyword_ratio
                + 0.25 * float(phrase_match)
            )

            ranked_results.append(
                {
                    "chunk": chunk,
                    "distance": distance,
                    "hybrid_score": hybrid_score,
                    "keyword_score": keyword_ratio,
                    "phrase_match": phrase_match
                }
            )


        # =================================================
        # SORT BY HYBRID RELEVANCE
        # =================================================

        ranked_results.sort(
            key=lambda result: result["hybrid_score"],
            reverse=True
        )


        # =================================================
        # SELECT RELEVANT RESULTS
        # =================================================

        lexical_matches = [

            result

            for result in ranked_results

            if (
                result["keyword_score"] > 0
                or result["phrase_match"]
            )

        ]


        if lexical_matches:

            selected = lexical_matches[:4]

        else:

            selected = ranked_results[:3]


        return selected


    # =====================================================
    # ASK QUESTION - SINGLE DOCUMENT
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
        # DOCUMENT SOURCE
        # =================================================

        source_metadata = document.get(
            "source",
            {}
        )

        filename = source_metadata.get(
            "filename",
            document.get(
                "filename",
                "Unknown document"
            )
        )


        # =================================================
        # BUILD CONTEXT + SOURCES
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
                    "document": filename,
                    "chunk": chunk,
                    "distance": distance,
                    "hybrid_score": result.get(
                        "hybrid_score"
                    ),
                    "keyword_score": result.get(
                        "keyword_score"
                    ),
                    "phrase_match": result.get(
                        "phrase_match"
                    )
                }
            )


        context = "\n\n".join(
            context_parts
        )


        # =================================================
        # SINGLE-DOCUMENT PROMPT
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

8. Give a moderately detailed answer rather than
   a very short or one-line response.

9. For a normal factual question, provide approximately
   3 to 6 clear sentences when the available context
   supports that level of detail.

10. If the question asks for an explanation, explain
    the relevant information clearly in a short paragraph
    or two short paragraphs.

11. If the document contains multiple relevant items,
    topics, components, or points, use bullet points
    when this makes the answer easier to understand.

12. Mention the relevant section or topic from the
    document when it helps clarify the answer.

13. Do not unnecessarily repeat the user's question.

14. Do not make the response excessively long.

15. Every factual statement in the answer must be
    supported by the provided document context.

16. If only limited information is available in the
    context, give only that information rather than
    filling the gaps with outside knowledge.

17. Keep the answer professional, clear, natural,
    and easy to understand.

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


    # =====================================================
    # ASK QUESTION - MULTIPLE DOCUMENTS
    # =====================================================

    @staticmethod
    def ask_multiple(
        question,
        documents
    ):

        all_results = []


        # =================================================
        # RETRIEVE FROM EACH DOCUMENT
        # =================================================

        for document in documents:

            DocumentQA.build_vector_store(
                document
            )

            results = DocumentQA.retrieve_chunks(
                question,
                document
            )

            source_metadata = document.get(
                "source",
                {}
            )

            filename = source_metadata.get(
                "filename",
                document.get(
                    "filename",
                    "Unknown document"
                )
            )


            for result in results:

                all_results.append(
                    {
                        "document": filename,
                        "chunk": result["chunk"],
                        "distance": result["distance"],
                        "hybrid_score": result.get(
                            "hybrid_score"
                        ),
                        "keyword_score": result.get(
                            "keyword_score"
                        ),
                        "phrase_match": result.get(
                            "phrase_match"
                        )
                    }
                )


        # =================================================
        # HANDLE NO RESULTS
        # =================================================

        if not all_results:

            return {

                "answer": (
                    "I could not find that information "
                    "in the uploaded documents."
                ),

                "sources": []

            }


        # =================================================
        # GLOBAL RANKING
        # =================================================

        all_results.sort(
            key=lambda result: result[
                "hybrid_score"
            ],
            reverse=True
        )


        # =================================================
        # SELECT TOP RESULTS
        # =================================================

        selected_results = all_results[:8]


        # =================================================
        # BUILD MULTI-DOCUMENT CONTEXT
        # =================================================

        context_parts = []

        for result in selected_results:

            context_parts.append(
                f"""
DOCUMENT: {result["document"]}

CONTENT:
{result["chunk"]}
"""
            )


        context = "\n\n".join(
            context_parts
        )


        # =================================================
        # BUILD SOURCES
        # =================================================

        sources = []

        for result in selected_results:

            sources.append(
                {
                    "document": result["document"],
                    "chunk": result["chunk"],
                    "distance": result["distance"],
                    "hybrid_score": result[
                        "hybrid_score"
                    ],
                    "keyword_score": result[
                        "keyword_score"
                    ],
                    "phrase_match": result[
                        "phrase_match"
                    ]
                }
            )


        # =================================================
        # MULTI-DOCUMENT GEMINI PROMPT
        # =================================================

        prompt = f"""
You are an Enterprise AI Compliance Assistant.

Answer the user's question using ONLY the information
contained in the provided document context.

The context may contain information from multiple
uploaded documents.

IMPORTANT RULES:

1. Use only information supported by the provided
   documents.

2. Do not use outside knowledge.

3. Do not invent information.

4. Do not assume that information exists in a document
   if it is not present in the supplied context.

5. Clearly distinguish information coming from different
   documents when necessary.

6. When useful, mention the document name from which
   the information was obtained.

7. If multiple documents provide relevant information,
   synthesize the information into one clear answer.

8. If the documents contain different or conflicting
   information, clearly identify the difference and
   mention the relevant document names.

9. Give a moderately detailed answer rather than a
   one-line response.

10. For a normal factual question, provide approximately
    3 to 6 clear sentences when the available context
    supports that level of detail.

11. If the question requires explanation, provide one
    or two short paragraphs with enough detail to make
    the answer understandable.

12. If multiple points are relevant, use bullet points
    when that improves readability.

13. Do not unnecessarily repeat the user's question.

14. Do not make the response excessively long.

15. Every factual statement must be supported by the
    supplied document context.

16. If only limited information is available, provide
    only that information instead of filling gaps with
    outside knowledge.

17. If the requested information cannot be found in
    the supplied document context, respond exactly:

I could not find that information in the uploaded documents.

=========================================================
USER QUESTION
=========================================================

{question}

=========================================================
DOCUMENT CONTEXT
=========================================================

{context}

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