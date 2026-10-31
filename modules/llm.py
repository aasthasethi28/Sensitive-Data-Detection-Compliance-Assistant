"""
llm.py

Local LLM integration using Ollama.

Responsibilities:
- Connect to locally running Ollama
- Generate responses using Qwen
- Provide a shared interface for QA and compliance
- Handle connection and generation errors
"""

import os

import httpx

from dotenv import load_dotenv


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://127.0.0.1:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen3.5:4b"
)

OLLAMA_TIMEOUT = float(
    os.getenv(
        "OLLAMA_TIMEOUT",
        "180"
    )
)


class LocalLLM:

    """
    Generates responses using a locally running
    Ollama model.
    """

    # =====================================================
    # GENERATE RESPONSE
    # =====================================================

    @staticmethod
    def generate(
        prompt,
        temperature=0.2,
        num_ctx=8192
    ):

        if not prompt or not prompt.strip():

            raise ValueError(
                "Prompt cannot be empty."
            )

        url = (
            f"{OLLAMA_HOST.rstrip('/')}"
            "/api/generate"
        )

        payload = {

            "model": OLLAMA_MODEL,

            "prompt": prompt,

            "stream": False,

            "keep_alive": "10m",

            "options": {

                "temperature": temperature,

                "num_ctx": num_ctx

            }

        }

        # =================================================
        # SEND REQUEST TO LOCAL OLLAMA SERVER
        # =================================================

        response = httpx.post(
            url,
            json=payload,
            timeout=httpx.Timeout(
                OLLAMA_TIMEOUT,
                connect=5.0
            )
        )

        response.raise_for_status()

        result = response.json()

        answer = result.get(
            "response",
            ""
        ).strip()

        if not answer:

            raise RuntimeError(
                "Ollama returned an empty response."
            )

        return answer
