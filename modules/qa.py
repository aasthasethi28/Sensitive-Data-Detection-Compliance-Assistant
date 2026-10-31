
"""
qa.py

Enterprise RAG
Hugging Face Embeddings + FAISS + Local Ollama LLM

Responsibilities:
- Build document vector stores
- Detect broad, specific and comparison questions
- Retrieve relevant document chunks
- Combine semantic and lexical relevance
- Support single-document and multi-document RAG
- Balance retrieval across selected documents
- Filter irrelevant document sources
- Generate grounded answers using local Qwen
- Return document-level source metadata
"""

from re import findall

from modules.utils import TextChunker
from modules.embeddings import EmbeddingModel
from modules.vector_store import VectorStore
from modules.llm import LocalLLM, OLLAMA_MODEL


class DocumentQA:

    # =====================================================
    # LOCAL MODEL CONFIGURATION
    # =====================================================

    MODEL_NAME = OLLAMA_MODEL


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
    # GENERATE LOCAL LLM RESPONSE
    # =====================================================

    @staticmethod
    def generate_answer(prompt):

        return LocalLLM.generate(
            prompt,
            temperature=0.2,
            num_ctx=8192
        )


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
            "whole document",

            "compare",
            "comparison",
            "differences between",
            "similarities between",
            "across these documents",
            "across the documents"

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

        words = findall(
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

            if not chunks:

                document["chunks"] = []

                return

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
        # EXACT PHRASE MATCHING
        # -------------------------------------------------

        normalized_chunk = " ".join(
            chunk.lower().split()
        )

        phrase_match = False

        if len(question_keywords) >= 2:

            ordered_keywords = [

                word

                for word in findall(
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

        total_chunks = len(
            document["chunks"]
        )

        if total_chunks == 0:

            return []

        if document["vector_store"] is None:

            return []

        query_embedding = EmbeddingModel.encode(
            [question]
        )[0]


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

            return document["vector_store"].search(
                query_embedding,
                k=candidate_k
            )


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

            semantic_score = (
                1.0
                / (1.0 + distance)
            )

            keyword_ratio, phrase_match = (
                DocumentQA.calculate_keyword_score(
                    question,
                    chunk
                )
            )

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
        # SORT RESULTS
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

            return lexical_matches[:4]

        return ranked_results[:3]


    # =====================================================
    # ASK QUESTION - SINGLE DOCUMENT
    # =====================================================

    @staticmethod
    def ask(
        question,
        document
    ):

        DocumentQA.build_vector_store(
            document
        )

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
                    "I could not find that information "
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

            context_parts.append(
                chunk
            )

            sources.append(
                {
                    "document": filename,
                    "chunk": chunk,
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

I could not find that information in the uploaded document.

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
        # LOCAL QWEN GENERATION
        # =================================================

        answer = DocumentQA.generate_answer(
            prompt
        )


        # =================================================
        # RETURN ANSWER + SOURCES
        # =================================================

        return {

            "answer": answer,

            "sources": sources

        }


    # =====================================================
    # NORMALIZE RETRIEVAL RESULT
    # =====================================================

    @staticmethod
    def normalize_result(
        question,
        result,
        document
    ):

        chunk = result["chunk"]

        distance = float(
            result["distance"]
        )

        keyword_score = result.get(
            "keyword_score"
        )

        phrase_match = result.get(
            "phrase_match"
        )

        # Calculate missing lexical scores.

        if (
            keyword_score is None
            or phrase_match is None
        ):

            calculated_keyword_score, calculated_phrase_match = (
                DocumentQA.calculate_keyword_score(
                    question,
                    chunk
                )
            )

            if keyword_score is None:

                keyword_score = calculated_keyword_score

            if phrase_match is None:

                phrase_match = calculated_phrase_match


        # Calculate missing hybrid score.

        hybrid_score = result.get(
            "hybrid_score"
        )

        if hybrid_score is None:

            semantic_score = (
                1.0
                / (1.0 + max(distance, 0.0))
            )

            hybrid_score = (
                0.35 * semantic_score
                + 0.40 * keyword_score
                + 0.25 * float(phrase_match)
            )


        # Document metadata.

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

        return {

            "document_id": document.get(
                "document_id"
            ),

            "document": filename,

            "chunk": chunk,

            "distance": distance,

            "hybrid_score": hybrid_score,

            "keyword_score": keyword_score,

            "phrase_match": phrase_match

        }


    # =====================================================
    # BALANCED RETRIEVAL FOR BROAD QUESTIONS
    # =====================================================

    @staticmethod
    def balanced_retrieval(
        document_groups,
        maximum_results=8
    ):

        """
        Select chunks in round-robin order.

        This prevents one selected document from
        dominating broad comparison questions.
        """

        selected_results = []

        maximum_depth = max(
            (
                len(group)
                for group in document_groups
            ),
            default=0
        )

        for rank in range(maximum_depth):

            for group in document_groups:

                if rank < len(group):

                    selected_results.append(
                        group[rank]
                    )

                    if len(selected_results) >= maximum_results:

                        return selected_results

        return selected_results


    # =====================================================
    # ASK QUESTION - MULTIPLE DOCUMENTS
    # =====================================================

    @staticmethod
    def ask_multiple(
        question,
        documents
    ):

        document_groups = []


        # =================================================
        # RETRIEVE INDEPENDENTLY FROM EACH DOCUMENT
        # =================================================

        for document in documents:

            DocumentQA.build_vector_store(
                document
            )

            results = DocumentQA.retrieve_chunks(
                question,
                document
            )

            normalized_results = [

                DocumentQA.normalize_result(
                    question,
                    result,
                    document
                )

                for result in results

            ]

            normalized_results.sort(
                key=lambda result: result["hybrid_score"],
                reverse=True
            )

            if normalized_results:

                document_groups.append(
                    normalized_results
                )


        # =================================================
        # HANDLE NO RESULTS
        # =================================================

        if not document_groups:

            return {

                "answer": (
                    "I could not find that information "
                    "in the uploaded documents."
                ),

                "sources": []

            }


        # =================================================
        # BROAD / COMPARISON QUESTIONS
        # =================================================

        if DocumentQA.is_broad_query(question):

            selected_results = DocumentQA.balanced_retrieval(
                document_groups,
                maximum_results=8
            )


        # =================================================
        # SPECIFIC QUESTIONS
        # =================================================

        else:

            all_results = [

                result

                for group in document_groups

                for result in group

            ]

            lexical_matches = [

                result

                for result in all_results

                if (
                    result["keyword_score"] > 0
                    or result["phrase_match"]
                )

            ]


            # -------------------------------------------------
            # CASE 1: LEXICAL MATCHES FOUND
            # -------------------------------------------------

            if lexical_matches:

                selected_results = lexical_matches

                selected_results.sort(
                    key=lambda result: result["hybrid_score"],
                    reverse=True
                )

                selected_results = selected_results[:8]


            # -------------------------------------------------
            # CASE 2: SEMANTIC-ONLY FALLBACK
            # -------------------------------------------------

            else:

                all_results.sort(
                    key=lambda result: result["hybrid_score"],
                    reverse=True
                )

                best_score = all_results[0]["hybrid_score"]

                relevance_threshold = max(
                    0.18,
                    best_score * 0.75
                )

                selected_results = [

                    result

                    for result in all_results

                    if result["hybrid_score"] >= relevance_threshold

                ][:8]

                if not selected_results:

                    selected_results = [
                        all_results[0]
                    ]


        # =================================================
        # HANDLE EMPTY SELECTION
        # =================================================

        if not selected_results:

            return {

                "answer": (
                    "I could not find that information "
                    "in the uploaded documents."
                ),

                "sources": []

            }


        # =================================================
        # BUILD DOCUMENT-LABELLED CONTEXT
        # =================================================

        context_parts = []

        for result in selected_results:

            context_parts.append(
                f"""
DOCUMENT NAME: {result["document"]}

DOCUMENT ID: {result["document_id"]}

CONTENT:

{result["chunk"]}
"""
            )

        context = "\n\n".join(
            context_parts
        )


        # =================================================
        # BUILD SOURCE METADATA
        # =================================================

        sources = []

        for result in selected_results:

            sources.append(
                {
                    "document_id": result["document_id"],
                    "document": result["document"],
                    "chunk": result["chunk"],
                    "distance": result["distance"],
                    "hybrid_score": result["hybrid_score"],
                    "keyword_score": result["keyword_score"],
                    "phrase_match": result["phrase_match"]
                }
            )


        # =================================================
        # MULTI-DOCUMENT PROMPT
        # =================================================

        prompt = f"""
You are an Enterprise AI Compliance Assistant.

Answer the user's question using ONLY information
contained in the supplied document context.

The context may contain information from multiple
selected documents.

STRICT GROUNDING RULES:

1. Use only facts explicitly supported by the supplied
   document context.

2. Never use outside knowledge to complete missing facts.

3. Never invent technologies, projects, qualifications,
   responsibilities, dates or achievements.

4. Do not infer the purpose or technical domain of a
   project from its name alone.

5. Keep projects, employment experience, education,
   certifications and achievements clearly distinguished.

6. Do not turn an achievement or internship into a
   project unless the document explicitly identifies it
   as one.

7. Use the document name when attributing information.

8. When answering a comparison question, compare the
   documents using their retrieved content.

9. Give each selected document fair consideration when
   relevant context from it is available.

10. If only one document contains evidence relevant to
    a specific question, answer from that document.
    Do not force unrelated information from other
    documents into the answer.

11. If documents contain conflicting information,
    identify the conflict and name the relevant sources.

12. Give a moderately detailed answer.

13. For normal factual questions, provide approximately
    3 to 6 sentences when supported by the context.

14. Use headings and bullet points when multiple
    categories or items are relevant.

15. Do not repeat the user's question unnecessarily.

16. Every factual statement must be supported by the
    supplied context.

17. If the requested information cannot be found in
    the supplied context, respond exactly:

I could not find that information in the uploaded documents.

=========================================================
USER QUESTION
=========================================================

{question}

=========================================================
RETRIEVED DOCUMENT CONTEXT
=========================================================

{context}

=========================================================
ANSWER
=========================================================
"""


        # =================================================
        # LOCAL QWEN GENERATION
        # =================================================

        answer = DocumentQA.generate_answer(
            prompt
        )


        # =================================================
        # RETURN ANSWER + SOURCES
        # =================================================

        return {

            "answer": answer,

            "sources": sources

        }
