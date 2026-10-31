# Enterprise AI Compliance Assistant

An AI-powered document compliance platform that combines document parsing, sensitive-data detection, weighted risk classification, compliance report generation, and grounded Retrieval-Augmented Generation (RAG).

This repository is being developed in two modes:

1. **Local mode** — run the application privately using Ollama + Qwen, local embeddings, FAISS, and local persistence.
2. **Cloud demo mode (planned)** — deploy a zero-cost, quota-limited portfolio demonstration using Vercel, Gemini API, Qdrant Cloud, and Supabase.

> **Important:** The cloud architecture in this README is a target design, not a completed deployment. The application must be migrated and tested in stages before it is described as cloud-ready or production-ready.

---

## Table of Contents

- [Project Goals](#project-goals)
- [Current Development Status](#current-development-status)
- [Current Local Architecture](#current-local-architecture)
- [Features](#features)
- [Current RAG Design](#current-rag-design)
- [Local Setup](#local-setup)
- [Target Free Cloud Architecture](#target-free-cloud-architecture)
- [Cloud Document Processing Workflow](#cloud-document-processing-workflow)
- [Cloud Migration Roadmap](#cloud-migration-roadmap)
- [Configuration Plan](#configuration-plan)
- [Free-Tier Limits and Reliability](#free-tier-limits-and-reliability)
- [Security and Privacy](#security-and-privacy)
- [Repository Sync Note](#repository-sync-note)
- [Tomorrow's Resume Checklist](#tomorrows-resume-checklist)
- [Planned Cloud Project Structure](#planned-cloud-project-structure)
- [Testing Plan](#testing-plan)
- [Known Limitations](#known-limitations)
- [Useful Official Documentation](#useful-official-documentation)

---

# Project Goals

The assistant is intended to help users inspect documents for potentially sensitive information, understand the associated risk, obtain a structured compliance-oriented report, and ask questions about one or more documents.

The system should:

- Accept supported business and academic document formats.
- Extract and clean document text.
- Detect sensitive-data patterns.
- Classify document risk using a weighted score.
- Generate a structured compliance report.
- Split documents into meaningful chunks.
- Generate embeddings and store them in a vector database.
- Retrieve relevant information for document-grounded questions.
- Support single-document and multi-document question answering.
- Preserve document metadata and processing results.
- Provide a web interface for a portfolio demonstration.

The current implementation is a development/portfolio project. It is **not a certified compliance product** and does not replace legal, security, or regulatory review.

---

# Current Development Status

The latest local working copy discussed and tested during development has the following status.

| Area | Latest local status |
|---|---|
| FastAPI backend | Implemented |
| PDF, DOCX, TXT, CSV parsing | Implemented |
| Text cleaning | Implemented |
| Sensitive-data detection | Implemented |
| 11 sensitive-data categories | Implemented |
| Weighted LOW / MEDIUM / HIGH risk classification | Implemented |
| AI compliance report | Implemented with local Qwen |
| Structure-aware chunking | Implemented |
| Local BGE embeddings | Implemented |
| FAISS vector search | Implemented |
| Semantic + keyword + phrase retrieval | Implemented |
| Broad and specific query handling | Implemented |
| Single-document RAG | Tested |
| Multi-document RAG | Tested |
| Ollama + Qwen integration | Tested |
| SQLite metadata persistence | Implemented and restart-tested |
| FAISS index persistence | Implemented and restart-tested |
| React frontend | Not started |
| Gemini cloud provider | Planned |
| Gemini cloud embeddings | Planned |
| Qdrant Cloud integration | Planned |
| Supabase integration | Planned |
| Authentication and per-user authorization | Planned |
| Vercel deployment | Not started |

The local functional checks confirmed during the development conversation include:

- Local Ollama connection and Qwen response.
- Compliance report generation using Qwen.
- Single-document question answering.
- Multi-document question answering.
- Questions about Operating Systems topics.
- Questions about resume technologies and projects.
- A question about information not present in a document; the model returned an unsupported/not-found style answer rather than inventing a value.
- Restoration of previously uploaded document records and vector indexes after restarting the FastAPI application.

These were manual development checks, not an automated CI test suite. They should be converted into repeatable tests later.

## Sensitive-data categories

The current detector is configured for 11 categories:

1. Email addresses
2. Phone numbers
3. PAN numbers
4. Aadhaar numbers
5. Credit card numbers
6. Bank account numbers
7. IFSC codes
8. Passwords
9. Employee IDs
10. API keys
11. Business information

The detector is pattern/rule based in the current implementation. Numeric patterns can produce false positives and require careful validation.

---

# Current Local Architecture

The local application is designed to run on the developer's machine.

```text
                    LOCAL DEVELOPMENT

                 User / Swagger UI
                         |
                         v
                  FastAPI (main.py)
                         |
                         v
                 Document Manager
                         |
             +-----------+-----------+
             |                       |
             v                       v
      Document Parser          Text Cleaner
             |                       |
             +-----------+-----------+
                         |
                         v
              Sensitive Data Detector
                         |
                         v
               Weighted Risk Classifier
                         |
                         v
             Qwen Compliance Report
                         |
                         v
                 Text Chunker
                         |
                         v
             BGE Sentence Embeddings
                         |
                         v
                  FAISS Index
                         |
                         v
                 Qwen RAG Answer
                         |
          +--------------+--------------+
          |                             |
          v                             v
    SQLite metadata              Local FAISS files
          |                             |
          +--------------+--------------+
                         |
                  Local uploads/
```

## Local AI provider

- Runtime: Ollama.
- Model currently used: `qwen3.5:4b`.
- Ollama host: `http://127.0.0.1:11434`.
- Python integration module: `modules/llm.py`.
- HTTP client: `httpx`.
- Local configuration is read from environment variables using `python-dotenv`.

The local model was installed and tested successfully. The local application should retain this option even after a cloud provider is introduced.

## Local embeddings and vector storage

- Embedding model: `BAAI/bge-small-en-v1.5`.
- Library: Sentence Transformers.
- Vector store: FAISS `IndexFlatL2`.
- Chunking: custom structure-aware chunker.
- Retrieval: semantic similarity combined with keyword and phrase relevance.

The local vector store is not a hosted vector database. FAISS indexes are stored on disk in the local project, and they are restored through the project's persistence layer.

## Local persistence

The latest local implementation uses:

- SQLite database: `storage/documents.db`.
- Persisted FAISS indexes: `storage/faiss_indexes/`.
- Original uploaded files: `uploads/`.
- Local in-memory cache: used at runtime and restored from persisted records during startup.

The application startup lifecycle initializes storage and restores documents. Uploaded document IDs can be reused after a restart when the corresponding saved records and indexes are available.

Local persistence is not the same as a multi-user cloud storage system. It does not provide hosted backups, user isolation, or production-grade access control.

## Local LLM configuration

A local `.env` file can contain:

```env
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3.5:4b
OLLAMA_TIMEOUT=180
```

Do not commit the actual `.env` file.

## Running locally

From Windows PowerShell, in the project directory:

```powershell
# Activate the existing virtual environment
.\\venv\\Scripts\\Activate.ps1

# Start Ollama separately if it is not already running
ollama serve

# Run the FastAPI application
uvicorn main:app --reload
```

API URLs:

- API root: `http://127.0.0.1:8000/`
- Health endpoint: `http://127.0.0.1:8000/health`
- Swagger documentation: `http://127.0.0.1:8000/docs`

Use the current local `requirements.txt` from the working copy. The requirements file on GitHub was found to be older and still contains legacy Gemini and LangChain dependencies; it must be reconciled with the actual local code before deployment.

---

# Features

## 1. Document processing

Supported formats in the current parser:

- PDF
- DOCX
- TXT
- CSV

The parser extracts text and passes it through the cleaning and analysis pipeline.

## 2. Sensitive-data detection

The detector searches for the 11 categories listed above. Detection output is used by the risk classifier and compliance report generator.

Detection results should be treated as findings that need validation. A match is not automatically proof of a compliance violation.

## 3. Risk classification

The classifier computes a weighted score and assigns one of three levels:

- LOW
- MEDIUM
- HIGH

The exact weights and thresholds should be documented alongside the classifier implementation and evaluated against a labelled test set.

## 4. Compliance report generation

The report generator uses the LLM to create a structured report from the extracted document content, detections, and risk assessment.

The report format includes sections such as:

- Document summary
- Executive summary
- Overall risk assessment
- Sensitive information detected
- Applicable compliance considerations
- Security risks
- Recommendations
- Final verdict

An LLM-generated report is an assistant output, not a legal determination or formal certification.

## 5. RAG question answering

The user can ask questions about a document or a selected group of documents. The retriever supplies relevant source chunks to the language model, and the model is instructed to stay grounded in the provided context.

The system should communicate when the requested information cannot be found in the retrieved material.

---

# Current RAG Design

```text
                User question
                      |
                      v
              Query preparation
                      |
                      v
              Query embedding
                      |
                      v
              FAISS vector search
                      |
                      v
           Semantic candidate chunks
                      |
                      v
      Keyword / phrase relevance filtering
                      |
                      v
             Context construction
                      |
                      v
             Local Qwen generation
                      |
                      v
               Grounded answer
                      |
                      v
             Source chunk references
```

## Structure-aware chunking

The custom chunker tries to preserve logical document sections rather than blindly splitting all text into equal-sized pieces.

- Recognizable section or heading boundaries are used where possible.
- Large sections are split into smaller chunks with overlap.
- A fallback splitting strategy is used when section structure is not recognizable.

## Query-aware retrieval

The QA pipeline distinguishes between broad and specific questions.

**Broad questions** ask for an overview or synthesis across a document. They need a wider selection of relevant chunks.

Examples:

- What does this document cover?
- Give me an overview of the syllabus.
- Summarize the main sections.

**Specific questions** ask about a particular fact or topic. They should retrieve a narrower set of chunks and filter irrelevant context.

Examples:

- Does the document mention SQL?
- What topics are included under Operating Systems?
- What is the eligibility requirement?

Retrieval distance or relevance scores must not be described as calibrated confidence probabilities unless a separate calibration method is implemented and validated.

## Multi-document RAG

The current local implementation supports selecting multiple document IDs and asking a question across those documents. Retrieval should preserve document identity and return source metadata so the answer can be traced to the relevant document.

---

# Target Free Cloud Architecture

The planned public portfolio demonstration will use the following services, subject to free-tier availability and limits.

| Layer | Planned service | Responsibility |
|---|---|---|
| Frontend | Vercel Hobby | React interface |
| API backend | Vercel Hobby / Python Function | FastAPI routes and orchestration |
| LLM generation | Gemini API free tier | Compliance report and RAG answers |
| Cloud embeddings | `gemini-embedding-001` | Embed document chunks and user questions |
| Vector database | Qdrant Cloud Free | Dedicated vector storage and retrieval |
| Relational database | Supabase PostgreSQL | Users, document metadata, risk and report records |
| File storage | Supabase Storage | Original uploaded documents |

**Qdrant remains the dedicated vector database.** Supabase PostgreSQL stores relational data; it is not being selected as a replacement for Qdrant. We are not planning to use pgvector for this design.

```text
                         CLOUD DEMO

                        User / Browser
                              |
                              v
                       React Frontend
                         (Vercel)
                              |
                              v
                       FastAPI Backend
                         (Vercel)
                              |
          +-------------------+--------------------+
          |                   |                    |
          v                   v                    v
     Gemini API          Qdrant Cloud          Supabase
          |                   |                    |
          |              Dense vectors        PostgreSQL
          |              + lexical search     Document rows
          |              + metadata filters   Detection data
          |                                   Risk and reports
          |                                        |
          |                                        v
          |                                Supabase Storage
          |                                Original documents
          |
          +-- LLM generation
          +-- Text embeddings
```

## Responsibilities by service

### Vercel

- Hosts the frontend.
- Hosts the FastAPI application as a Python Function.
- Stores environment variables for the deployed project.
- Routes API requests to the backend.
- Does not store application files or FAISS indexes as persistent local files.

Vercel Hobby is for personal and non-commercial use. This project should remain a personal/academic portfolio demonstration while using that plan.

### Gemini API

The cloud provider will be configurable rather than hard-coded into the whole application.

Planned responsibilities:

- Generate compliance reports.
- Generate grounded RAG responses.
- Generate embeddings for document chunks.
- Generate embeddings for user questions.

The model selected for text generation must be checked in Google AI Studio immediately before implementation because free-tier model availability, quotas, and rate limits can change.

The planned embedding model is `gemini-embedding-001`. Its requested output dimension must be fixed and used consistently for every vector in the corresponding Qdrant collection.

**Privacy restriction:** Google's Gemini API free tier states that submitted content may be used to improve its products. Do not send genuine confidential business documents, real personal data, customer records, credentials, or other sensitive documents through the unpaid API. Use synthetic or properly anonymised sample documents for the public demo.

### Qdrant Cloud

Qdrant is the dedicated cloud vector database.

It will store points containing:

- Vector embedding.
- Chunk text or a reference to the chunk text.
- Document ID.
- User/owner ID.
- Filename or document reference.
- Page number, where available.
- Section or heading, where available.
- Additional retrieval metadata.

It will support:

- Dense semantic retrieval.
- Metadata filtering by user and document.
- Single-document retrieval.
- Multi-document retrieval.
- Deletion of a document's vectors.
- Hybrid retrieval using dense and lexical/sparse signals, with an application-side fusion strategy where appropriate.

Qdrant's free cluster is intended for prototyping and testing, not guaranteed production workloads. Its documented free resources and inactivity behaviour are listed in [Qdrant's Cloud documentation](https://qdrant.tech/documentation/cloud/create-cluster/).

### Supabase PostgreSQL

Supabase PostgreSQL will store relational application data, for example:

- User profile or user ID reference.
- Document ID.
- Original filename.
- Supabase Storage object path.
- Upload timestamp.
- Processing status.
- Detection summary.
- Risk score and risk category.
- Compliance report text or report reference.
- Error state and processing metadata.

A document record should be associated with an authenticated owner. Row Level Security (RLS) policies must prevent one user from reading or changing another user's records.

### Supabase Storage

Supabase Storage will hold original uploaded files in a **private bucket**.

The intended flow is:

1. The frontend requests permission to upload.
2. The backend/auth layer validates the user and creates a short-lived signed upload URL or equivalent restricted upload permission.
3. The browser uploads the file directly to Supabase Storage.
4. The backend processes the stored object using a temporary download or signed URL.
5. The original object remains in private storage.
6. The document's metadata and processing state are saved in PostgreSQL.

This avoids sending large files through a Vercel Function request body.

---

# Cloud Document Processing Workflow

The target cloud workflow is:

1. **User authentication** — identify the user before upload or document access.
2. **Document upload** — upload the file directly to a private Supabase Storage bucket.
3. **Metadata creation** — create a document row with owner ID, object path, filename, and processing status.
4. **Document retrieval for processing** — FastAPI retrieves the file temporarily using a restricted signed URL or storage SDK.
5. **Parsing and cleaning** — reuse the existing parser and cleaner.
6. **Sensitive-data detection** — reuse the detector, subject to the privacy restrictions of the selected AI and hosting services.
7. **Risk classification** — reuse the weighted classifier.
8. **Chunking** — reuse the structure-aware `TextChunker`.
9. **Embedding generation** — use the cloud embedding provider in cloud mode.
10. **Vector insertion** — store vectors and metadata in Qdrant.
11. **Compliance report generation** — call Gemini and save the report and summary in Supabase PostgreSQL.
12. **Processing completion** — mark the document as processed and make it available in the dashboard.

## Cloud question-answering workflow

1. User submits a question and the document ID or selected document IDs.
2. Backend verifies that the user owns or is authorized to access those documents.
3. Backend generates an embedding for the question using the same cloud embedding model and dimensions used during indexing.
4. Qdrant searches only the selected documents and the authenticated user's data.
5. The retriever combines semantic and lexical relevance.
6. The backend builds a context containing the best source chunks.
7. Gemini generates a grounded answer.
8. The API returns the answer and source details.
9. The frontend displays the answer and lets the user inspect its source documents.

The question embedding model must match the document embedding model. Do not query a Qdrant collection with vectors from a different embedding model or vector dimension.

---

# Cloud Migration Roadmap

The migration must be incremental. Do not replace all modules in one step. Keep local mode usable while cloud mode is being added.

## Phase 0 — Preserve and synchronise the working project

Before changing code:

- Back up the working project.
- Confirm the local Git branch and working tree.
- Confirm the GitHub remote.
- Compare local code against the current GitHub `main` branch.
- Update `.gitignore` before staging any files.
- Never stage `.env`, uploaded documents, local databases, FAISS indexes, model caches, or virtual environments.
- Commit the latest tested local source files in a separate source-code commit.

This step matters because the GitHub branch was found to contain an older implementation than the latest local working copy.

## Phase 1 — Introduce a provider-switching LLM module

Primary file:

- `modules/llm.py`

Goal: support both local Ollama and cloud Gemini through one stable interface.

Expected configuration concept:

```env
LLM_PROVIDER=ollama

OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3.5:4b
OLLAMA_TIMEOUT=180

# Used only when LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=select_a_model_available_on_the_free_tier
```

Implementation requirements:

- Keep the existing Ollama implementation working.
- Add the Gemini implementation without changing the public method signature unnecessarily.
- Validate missing API keys and invalid provider values.
- Use clear error messages for quota exhaustion, invalid credentials, timeouts, and unavailable models.
- Do not silently fall back to a paid provider.
- Do not log API keys or document contents.

**Test before continuing:** test one short prompt through Ollama and one through Gemini, then confirm the provider switch selects the expected path.

## Phase 2 — Introduce provider-switching embeddings

Primary file:

- `modules/embeddings.py`

Goal: support both local BGE embeddings and cloud Gemini embeddings.

Local provider:

- `BAAI/bge-small-en-v1.5` through Sentence Transformers.

Cloud provider:

- `gemini-embedding-001`.

Implementation requirements:

- Use one consistent embedding interface.
- Fix the Gemini output dimensionality explicitly.
- Validate vector length, numeric values, and non-empty input.
- Batch requests within the model's limits.
- Handle API quota and rate-limit errors.
- Keep local BGE mode unchanged.

**Important:** local BGE vectors and Gemini vectors are not interchangeable. The BGE model and Gemini model produce different embedding spaces. Re-embed every cloud document with Gemini and store those vectors in a separate Qdrant collection from any vectors generated by a different model.

**Test before continuing:** compare output dimensions for document text and query text, insert a test vector into a temporary collection, and retrieve it using a query vector from the same model.

## Phase 3 — Add Qdrant as the cloud vector-store adapter

Primary file:

- `modules/vector_store.py`

Goal: retain FAISS for local mode and add Qdrant for cloud mode.

Configuration concept:

```env
VECTOR_STORE_PROVIDER=faiss
QDRANT_URL=https://your-cluster-url
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=enterprise_compliance_gemini_768
```

Implementation requirements:

- Keep FAISS operations available in local mode.
- Add Qdrant client initialisation for cloud mode.
- Create/validate the cloud collection with the exact embedding dimension.
- Use stable point IDs.
- Store document and owner metadata in the payload.
- Add insert, search, document-filter, and delete operations.
- Ensure the Qdrant API key remains server-side.
- Implement semantic and lexical/hybrid retrieval without losing document IDs or source metadata.

**Test before continuing:** insert vectors for two sample documents, retrieve by document ID, retrieve across multiple document IDs, confirm owner filtering, and delete one document's points.

## Phase 4 — Add Supabase database and file storage

Create the Supabase project and configure:

- PostgreSQL schema.
- Private Storage bucket.
- Authentication.
- Row Level Security.
- Server-side credentials.

Suggested relational tables (final schema to be designed before creating them):

### `documents`

- `id`
- `user_id`
- `filename`
- `storage_path`
- `mime_type`
- `file_size`
- `status`
- `risk_level`
- `risk_score`
- `created_at`
- `updated_at`

### `detection_results`

- `id`
- `document_id`
- `user_id`
- `category`
- `count`
- `severity`
- `details` (only the minimum necessary; avoid storing raw sensitive values)

### `compliance_reports`

- `id`
- `document_id`
- `user_id`
- `report_text`
- `created_at`
- `model_name`

The schema can be adjusted based on the existing response shapes and detector output.

Security requirements:

- Enable RLS on user-owned tables.
- Use the authenticated user ID in every query.
- Never expose the Supabase service-role key in the browser.
- Keep the Storage bucket private.
- Use signed URLs with short expiry.
- Verify ownership before returning, updating, downloading, or deleting a document.

## Phase 5 — Update document ingestion and persistence

Relevant modules:

- `modules/document_manager.py`
- `main.py`
- A new Supabase/storage adapter module may be introduced.
- The existing SQLite/FAISS persistence code remains for local mode.

Cloud mode must not depend on:

- A local SQLite database surviving between serverless requests.
- Local `uploads/` files surviving a redeployment.
- Local FAISS index files.
- An in-memory Python dictionary being shared by all requests.

Use the Supabase document row as the source of truth for document metadata and processing state. Use Supabase Storage for original files and Qdrant for vectors.

Processing must be idempotent or safely retryable so that a timeout does not create duplicate vector points or duplicate report rows.

## Phase 6 — Authentication and authorization

Before making the cloud demo public:

- Add user sign-in.
- Validate auth tokens in FastAPI.
- Enforce ownership on every document endpoint.
- Apply Supabase RLS policies.
- Add request-size limits and supported file-type validation.
- Add rate limits or reasonable per-user quotas.
- Ensure errors do not expose secrets, document contents, or internal stack traces.

A public portfolio demo with no authentication should not allow arbitrary visitors to retrieve or delete other users' documents.

## Phase 7 — Frontend

The frontend has not been started yet.

Recommended React screens:

1. Sign-in page.
2. Main dashboard.
3. Upload document page.
4. Document list with status.
5. Document details page.
6. Sensitive-data findings.
7. Risk classification panel.
8. Compliance report viewer.
9. Single-document chat.
10. Multi-document chat.

The frontend must call the FastAPI API and must not contain Gemini, Qdrant, or Supabase service-role secrets.

## Phase 8 — Deploy and verify

Deployment order:

1. Create/configure Qdrant Cloud.
2. Create/configure Supabase.
3. Configure the backend environment variables in Vercel.
4. Deploy FastAPI to Vercel and test the health endpoint.
5. Deploy the frontend to Vercel.
6. Configure the frontend's API base URL.
7. Verify CORS and authentication.
8. Test uploads, parsing, detection, reports, embeddings, vector retrieval, and chat.
9. Test document deletion across Supabase Storage, PostgreSQL, and Qdrant.
10. Verify the demo still works after a redeployment and after free services resume from an idle state.

Do not call the application production-ready merely because the first deployment succeeds.

---

# Configuration Plan

Keep provider selection explicit. The local and cloud environment variables should not be confused.

## Local mode

```env
LLM_PROVIDER=ollama
VECTOR_STORE_PROVIDER=faiss
EMBEDDING_PROVIDER=sentence_transformers

OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3.5:4b
OLLAMA_TIMEOUT=180
```

## Cloud demo mode

```env
LLM_PROVIDER=gemini
VECTOR_STORE_PROVIDER=qdrant
EMBEDDING_PROVIDER=gemini

GEMINI_API_KEY=...
GEMINI_MODEL=...
QDRANT_URL=...
QDRANT_API_KEY=...
QDRANT_COLLECTION=enterprise_compliance_gemini_768

SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_STORAGE_BUCKET=documents
```

This is a configuration template only. Use the exact environment variable names that the implementation eventually adopts. Store the service-role key only in the backend's protected environment. The browser may use a public/anon key only with correctly configured RLS and access policies.

---

# Free-Tier Limits and Reliability

The objective is a **$0 portfolio demonstration**. It is not possible to promise unlimited inference, indefinite storage, guaranteed uptime, or production-grade support at zero cost.

Review the provider plans before creating resources, and re-check them before deployment because quotas and terms can change.

| Service | Free-tier consideration |
|---|---|
| Vercel Hobby | Personal/non-commercial use only; function runtime, request size, package size, and usage quotas apply |
| Gemini API | Limited model availability and rate limits; free-tier input may be used to improve Google's products |
| Qdrant Cloud Free | Single-node cluster with limited compute and disk; idle clusters can be suspended and later deleted |
| Supabase Free | Limited database, file storage, and egress; low-activity projects can be paused |

## Vercel constraints

The FastAPI application runs as a serverless function, not as a permanent Ollama host.

Important implementation consequences:

- Do not run Ollama inside Vercel.
- Do not use local disk as permanent storage.
- Do not keep important state in global Python variables.
- Avoid loading PyTorch, Sentence Transformers, BGE model weights, or FAISS in cloud mode unless there is a specific tested reason.
- Use Gemini API for cloud embeddings.
- Send files directly from the browser to Supabase Storage using signed uploads rather than posting large files through a Vercel Function.
- Vercel Function request/response payload limits and the Python deployment bundle limit must be respected.
- Keep the cloud dependency list small. Consider a separate `requirements-cloud.txt` so local-only packages are not installed in the cloud function.
- Test parser dependencies and deployment bundle size before committing to Vercel as the backend host.

## Gemini free-tier constraints

- Model availability and limits can differ by model and change over time.
- Requests may be rate-limited or rejected after the quota is reached.
- Add clear handling for quota errors.
- Do not enable paid billing or silently fall back to a paid API.
- If the free quota is exhausted, return a clear message and allow the user to retry later.
- Do not use unpaid Gemini API for genuine confidential or personal documents.

## Qdrant free-tier constraints

- The free cluster is suitable for prototypes and testing.
- It has limited RAM, CPU, and disk.
- Free clusters can suspend after inactivity and may be deleted after an extended inactive period.
- Export important data or maintain a reproducible re-indexing path.
- Do not treat the free cluster as the only copy of important business records.

## Supabase free-tier constraints

- Free database and file-storage quotas apply.
- Free projects can pause after a period of low activity.
- Build a recovery checklist for resuming a paused project.
- Keep local development backups for the portfolio demo.
- Monitor database size, egress, and storage usage.

## Cost-control principle

The cloud configuration must not silently upgrade to paid services. Keep the project on free plans, check quotas, and show a useful error when a service's free allowance is exhausted. Do not add a payment method or enable paid overages unless a deliberate decision is made later.

---

# Security and Privacy

This project analyses sensitive-data patterns, so privacy and access control are central requirements.

For the local version:

- Keep `.env` outside Git.
- Keep uploaded files and local databases outside Git.
- Do not publish real documents in screenshots, test fixtures, or issue reports.
- Restrict access to the machine and local project folder.

For the cloud demo:

- Use synthetic or anonymised documents only.
- Do not submit actual PAN, Aadhaar, bank-account, card, password, API-key, HR, customer, or confidential company data to a free external AI API.
- Keep Gemini and Qdrant API keys on the server.
- Keep Supabase service-role credentials on the server.
- Use private Storage buckets and signed URLs.
- Enforce authentication and user ownership.
- Apply RLS and Qdrant payload filters.
- Minimise sensitive content stored in database rows and vector payloads.
- Provide a delete operation that removes the original file, metadata, detection/report records, and all Qdrant points.
- Avoid logging raw document text or detected secret values.
- Rotate any key that is accidentally committed.

The free cloud design is for a demonstration with non-sensitive sample documents. A real production compliance platform would need a separate security/privacy review, contractual review of data processing terms, encryption and key-management decisions, backup and recovery, monitoring, access controls, and appropriate paid infrastructure.

---

# Repository Sync Note

**This note is important before continuing.**

On 31 October 2026, the GitHub `main` branch was inspected. The remote source snapshot still showed the older implementation:

- `main.py` used an in-memory `document_store = {}`.
- The remote README described Gemini + BGE + FAISS.
- The remote `requirements.txt` still listed legacy `google-generativeai` and LangChain dependencies.
- The remote tree did not yet show the newer local `modules/llm.py` and storage/persistence files described in the current local development notes.

The latest local working copy discussed in development is newer:

- Ollama + Qwen integration through `modules/llm.py`.
- Qwen used by compliance generation and RAG.
- SQLite persistence and saved FAISS indexes.
- Document restoration on application startup.
- Single- and multi-document chat.

Therefore:

1. This README records the latest known local development status and the agreed cloud migration plan.
2. The current local Python source files still need to be synchronised to GitHub.
3. The README update alone does **not** mean the newer Python implementation has been pushed.
4. Before deployment, inspect the local working tree and push the tested source files to GitHub after checking that no secrets or local data are staged.

Do not overwrite the newer local source files with the older files currently visible on GitHub.

---

# Tomorrow's Resume Checklist

Use this as the exact starting sequence when continuing development.

## Step 1 — Open the existing project

Open the existing project directory in VS Code and activate its current virtual environment.

Windows PowerShell:

```powershell
cd "C:\\Users\\COER UNIVERSITY\\Desktop\\Sensitive Data Detection & Compliance Assistant"
.\\venv\\Scripts\\Activate.ps1
```

If the project directory has moved, use its actual current location.

## Step 2 — Inspect Git status before committing

```powershell
git status
git branch --show-current
git remote -v
```

Check which source files are modified and confirm the active branch.

## Step 3 — Protect local and sensitive files

Before staging files, check `.gitignore`. It should exclude at least:

```gitignore
.env
**/.env
venv/
.venv/
__pycache__/
*.py[cod]
uploads/
storage/
*.db
*.sqlite
*.sqlite3
extracted_text/
.streamlit/
.vscode/
.DS_Store
Thumbs.db
```

Do not commit:

- `.env` or API keys.
- Uploaded source documents.
- `storage/documents.db`.
- `storage/faiss_indexes/`.
- Virtual environments.
- Downloaded model weights and caches.
- Any real sensitive test data.

Check the staged files with `git status` before committing.

## Step 4 — Synchronise the tested local implementation to GitHub

The remote branch is older than the latest local code. Review the actual local changes first. Stage only the intended source/configuration files, for example:

```powershell
git add main.py modules requirements.txt .gitignore
git status
```

The exact staging list depends on the local changes and any new files. Do not use `git add .` blindly.

After verifying the staged diff:

```powershell
git diff --cached
git commit -m "Sync local Qwen and persistent RAG implementation"
git push origin main
```

If Git reports a rejected push or remote changes, stop and reconcile the branch safely; do not force-push.

## Step 5 — Verify the local version still works

Run the checks appropriate to the current implementation:

```powershell
pip check
python -c "from modules.llm import LocalLLM; print(LocalLLM.generate('Reply with LOCAL MODEL READY'))"
python -c "import main; print('FastAPI application loaded successfully')"
```

Then start the server:

```powershell
uvicorn main:app --reload
```

Use Swagger at `http://127.0.0.1:8000/docs` and confirm upload, document listing, single-document chat, and multi-document chat. Do not assume a test passed until its output confirms it.

## Step 6 — Start Phase 1 of the cloud migration

Only after the local source is safely backed up and synchronised:

1. Open `modules/llm.py`.
2. Preserve the working Ollama provider.
3. Add Gemini as a second provider behind a configuration setting.
4. Test Ollama mode again.
5. Test Gemini with a harmless synthetic prompt.
6. Confirm Gemini quota errors are handled without paid fallback.
7. Do not change embeddings or the vector database in this phase.

**Stop after Phase 1 is tested.** Move to embeddings in a separate change.

---

# Planned Cloud Project Structure

This is a possible future structure, not a statement that all these files already exist.

```text
enterprise-ai-compliance-assistant/
|
|-- main.py
|-- requirements.txt
|-- requirements-cloud.txt
|-- .env.example
|-- .gitignore
|-- README.md
|
|-- modules/
|   |-- llm.py
|   |-- parser.py
|   |-- cleaner.py
|   |-- document_manager.py
|   |-- embeddings.py
|   |-- vector_store.py
|   |-- qa.py
|   |-- compliance.py
|   |-- classifier.py
|   |-- analytics.py
|   |-- dashboard.py
|   |-- storage/
|   |   |-- local_storage.py
|   |   |-- supabase_storage.py
|   |
|   |-- detector/
|       |-- detector.py
|       |-- ...
|
|-- frontend/
|   |-- package.json
|   |-- src/
|   |   |-- pages/
|   |   |-- components/
|   |   |-- services/
|   |   |-- ...
|
|-- tests/
|   |-- test_parser.py
|   |-- test_detector.py
|   |-- test_classifier.py
|   |-- test_llm_providers.py
|   |-- test_embeddings.py
|   |-- test_vector_store.py
|   |-- test_rag.py
|   |-- ...
|
|-- uploads/       # local only; ignored by Git
|-- storage/       # local only; ignored by Git
```

The cloud deployment should use a small dependency set. Local-only packages such as Ollama-related local dependencies, Sentence Transformers, PyTorch, and FAISS should not be loaded in the Vercel cloud execution path unless they are explicitly required and proven to fit the deployment constraints.

---

# Testing Plan

Every migration phase should have its own tests.

| Area | Test |
|---|---|
| LLM provider selection | Ollama and Gemini are selected from configuration |
| LLM errors | Invalid key, unavailable model, timeout, and quota exhaustion |
| Embeddings | Same model and dimensions used for document and query vectors |
| Qdrant insertion | Insert multiple chunks with metadata |
| Qdrant retrieval | Retrieve relevant chunks for one document |
| Document filtering | Do not return chunks from unselected documents |
| User isolation | User A cannot retrieve User B's vectors or metadata |
| Document deletion | Remove file, metadata, reports, and vectors |
| Parser | PDF, DOCX, TXT, and CSV |
| Sensitive detector | Positive and negative examples for each category |
| Classifier | Verify scoring and LOW/MEDIUM/HIGH thresholds |
| Compliance report | Output includes expected sections and is grounded in analysis |
| RAG | Broad, specific, and unsupported questions |
| Multi-document RAG | Results preserve source document identity |
| Persistence | Data remains available after a function restart/redeployment within the external services |
| Deployment | Health route, CORS, environment variables, quotas, and error handling |

---

# Known Limitations

- This is a work-in-progress portfolio project.
- A public cloud demo is not yet deployed.
- The React frontend is not yet implemented.
- The free cloud services have quotas and may pause/suspend resources.
- Free Gemini API usage is not appropriate for real sensitive documents.
- Pattern-based detection can produce false positives and false negatives.
- LLM reports and answers require evaluation and human review.
- Current local manual tests are not a substitute for an automated evaluation suite.
- The cloud architecture requires authentication, access control, and deletion workflows before public use.

---

# Useful Official Documentation

Review current pricing and provider limits before deployment:

- [Vercel FastAPI deployment](https://vercel.com/docs/frameworks/backend/fastapi)
- [Vercel Function limitations](https://vercel.com/docs/functions/limitations)
- [Vercel Hobby plan](https://vercel.com/docs/plans/hobby)
- [Gemini API pricing and free-tier details](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini embeddings](https://ai.google.dev/gemini-api/docs/embeddings)
- [Qdrant Cloud free cluster](https://qdrant.tech/documentation/cloud/create-cluster/)
- [Qdrant hybrid queries](https://qdrant.tech/documentation/search/hybrid-queries/)
- [Supabase pricing](https://supabase.com/pricing)
- [Supabase Storage](https://supabase.com/docs/guides/storage)
- [Supabase Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase project pausing](https://supabase.com/docs/guides/platform/free-project-pausing)

---

## Development Principle

Continue the project one component at a time:

```text
Preserve local implementation
           |
           v
Synchronise tested source to GitHub
           |
           v
LLM provider abstraction
           |
           v
Cloud embeddings
           |
           v
Qdrant vector database
           |
           v
Supabase database and storage
           |
           v
Cloud document ingestion and persistence
           |
           v
Authentication and security
           |
           v
React frontend
           |
           v
Vercel deployment and end-to-end testing
```

**Immediate next task:** synchronise the latest local Qwen + persistent-storage source files to GitHub, then implement and test the provider switch in `modules/llm.py`. Keep Ollama working locally throughout the migration.
