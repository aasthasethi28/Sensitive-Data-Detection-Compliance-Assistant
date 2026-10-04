"""
utils.py

Document Text Chunking

Provides structure-aware chunking for documents while
keeping a fixed-size fallback for documents that do not
contain clear section boundaries.
"""


import re


class TextChunker:

    # =====================================================
    # MAIN SPLIT FUNCTION
    # =====================================================

    @staticmethod
    def split(text):

        if not text or not text.strip():

            return []

        text = text.strip()

        # -------------------------------------------------
        # Try structure-aware chunking first
        # -------------------------------------------------

        sections = TextChunker._split_into_sections(
            text
        )

        # -------------------------------------------------
        # If sections were detected, process them
        # -------------------------------------------------

        if len(sections) > 1:

            chunks = []

            for section in sections:

                section_chunks = TextChunker._split_large_section(
                    section
                )

                chunks.extend(
                    section_chunks
                )

            return chunks

        # -------------------------------------------------
        # Otherwise use fixed-size fallback
        # -------------------------------------------------

        return TextChunker._fixed_size_chunks(
            text
        )


    # =====================================================
    # STRUCTURE-AWARE SECTION DETECTION
    # =====================================================

    @staticmethod
    def _split_into_sections(text):

        # Common section patterns such as:
        #
        # Section 1
        # Section 1:
        # SECTION 1
        # Section 1 - Probability
        # 1. Probability
        # 1) Probability
        #
        pattern = re.compile(
            r"(?im)^(?:"
            r"section\s+\d+"
            r"|section\s+[ivxlcdm]+"
            r"|\d+\.\s+[A-Z]"
            r"|\d+\)\s+[A-Z]"
            r")"
        )

        matches = list(
            pattern.finditer(text)
        )

        if len(matches) < 2:

            return []

        sections = []

        # -------------------------------------------------
        # Text before the first detected section
        # -------------------------------------------------

        first_start = matches[0].start()

        prefix = text[:first_start].strip()

        if prefix:

            sections.append(
                prefix
            )

        # -------------------------------------------------
        # Extract each section
        # -------------------------------------------------

        for index, match in enumerate(matches):

            start = match.start()

            if index + 1 < len(matches):

                end = matches[index + 1].start()

            else:

                end = len(text)

            section = text[start:end].strip()

            if section:

                sections.append(
                    section
                )

        return sections


    # =====================================================
    # HANDLE LARGE SECTIONS
    # =====================================================

    @staticmethod
    def _split_large_section(section):

        max_size = 1200

        if len(section) <= max_size:

            return [section]

        chunks = []

        start = 0

        while start < len(section):

            end = start + max_size

            chunk = section[start:end].strip()

            if chunk:

                chunks.append(
                    chunk
                )

            # Small overlap to preserve context
            # when a section has to be divided.

            start = end - 150

        return chunks


    # =====================================================
    # FIXED-SIZE FALLBACK
    # =====================================================

    @staticmethod
    def _fixed_size_chunks(text):

        chunk_size = 1000

        overlap = 150

        chunks = []

        start = 0

        while start < len(text):

            end = start + chunk_size

            chunk = text[start:end].strip()

            if chunk:

                chunks.append(
                    chunk
                )

            if end >= len(text):

                break

            start = end - overlap

        return chunks