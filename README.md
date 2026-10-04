# Enterprise AI Compliance Assistant

An AI-powered document compliance and question-answering system combining sensitive-data detection, risk classification, AI-generated compliance reports, semantic retrieval, and grounded Retrieval-Augmented Generation (RAG).

> **Current status:** The FastAPI backend and core RAG pipeline are implemented. A separate frontend is planned for a later phase.

---

## Overview

The current backend workflow is:

```text
Document Upload
      ↓
Document Parsing
      ↓
Text Cleaning
      ↓
Sensitive Data Detection
      ↓
Risk Classification
      ↓
AI Compliance Report
      ↓
Structure-Aware Chunking
      ↓
Hugging Face Embeddings
      ↓
FAISS Vector Search
      ↓
Gemini-Powered RAG Q&A
```

The RAG pipeline is implemented directly with Hugging Face Sentence Transformers, FAISS, and Gemini.

**LangChain is not used.**

---

## Current Features

### Document Processing

The backend currently supports:

- Single document upload
- Multiple document upload
- PDF
- DOCX
- TXT
- CSV
- Text cleaning and preprocessing

### Sensitive Data Detection

The system currently detects 11 categories:

1. Email addresses
2. Phone numbers
3. Employee IDs
4. IFSC codes
5. PAN numbers
6. Aadhaar numbers
7. Bank account numbers
8. Credit card numbers
9. Passwords
10. API keys
11. Business information

### Risk Classification

Detected information is converted into a weighted document-level risk score.

Current risk levels:

- LOW
- MEDIUM
- HIGH

### AI Compliance Reports

Gemini generates structured reports containing:

- Document Summary
- Executive Summary
- Overall Risk Assessment
- Sensitive Information Detected
- Applicable Compliance Standards
- Security Risks
- Recommendations
- Final Verdict

---

# Retrieval-Augmented Generation (RAG)

The project contains a document-specific RAG question-answering pipeline.

## Architecture

```text
User Question
      ↓
Question Embedding
      ↓
FAISS Retrieval
      ↓
Relevant Document Chunks
      ↓
Context Construction
      ↓
Gemini 2.5 Flash
      ↓
Grounded Answer
```

### Embeddings

Embedding model:

```text
BAAI/bge-small-en-v1.5
```

implemented using Hugging Face Sentence Transformers.

Embeddings are normalized before being stored in FAISS.

### Vector Store

The project directly uses:

```text
FAISS IndexFlatL2
```

The vector store maintains:

- Document chunks
- Embeddings
- Retrieval distances

### Answer Generation

Gemini 2.5 Flash is used directly through the Google Generative AI API.

The generation prompt instructs the model to:

- Use only retrieved document context
- Avoid unsupported assumptions
- Avoid inventing information
- State when information cannot be found
- Focus on the user's question
- Synthesize information for broad document-level questions

---

# Structure-Aware Chunking

The current RAG pipeline uses a custom structure-aware chunker.

Instead of relying only on fixed-size text splitting, it first attempts to identify section boundaries such as:

```text
Section 1
Section 2
Section 3
...
```

This keeps logically related content together.

Large sections are divided into smaller chunks with overlap.

Documents without recognizable section structure use a fixed-size fallback strategy.

This was tested against a GATE Computer Science syllabus and produced coherent section-level chunks.

---

# Query-Aware Retrieval

The current system distinguishes between broad and specific questions.

### Broad Questions

Examples:

```text
What is the syllabus of the exam?

What does this document contain?

Give me an overview of the document.
```

Broad questions retrieve more context so the model can synthesize information across the document.

### Specific Questions

Examples:

```text
Does the syllabus include SQL?

What topics are covered under Operating System?
```

Specific questions retrieve a smaller candidate set and apply a retrieval-distance filtering baseline.

> FAISS distance is used as a retrieval signal and is **not** treated as a calibrated confidence probability.

---

# FastAPI Backend

The current backend is implemented with FastAPI.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API status |
| GET | `/health` | Health check |
| POST | `/documents/upload` | Upload and process one document |
| POST | `/documents/upload-multiple` | Upload and process multiple documents |
| POST | `/chat` | Ask a grounded question about a document |

---

## Single Document Upload

```http
POST /documents/upload
```

Processes one document and returns:

- Document ID
- Filename
- Sensitive-data detections
- Risk assessment
- Compliance report

---

## Multiple Document Upload

```http
POST /documents/upload-multiple
```

Processes multiple uploaded documents independently and assigns each document a unique ID.

---

## RAG Chat

```http
POST /chat
```

Example request:

```json
{
  "document_id": "your-document-id",
  "question": "Does the document contain SQL?"
}
```

The response includes:

- Document ID
- Question
- Grounded answer
- Retrieved source chunks
- Retrieval distances

---

# Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| Backend | FastAPI |
| API Server | Uvicorn |
| Embeddings | Hugging Face Sentence Transformers |
| Embedding Model | BAAI/bge-small-en-v1.5 |
| Vector Store | FAISS |
| LLM | Google Gemini 2.5 Flash |
| Configuration | python-dotenv |
| API Validation | Pydantic |

### Deliberate Architecture Choices

The current RAG pipeline does **not** use:

- LangChain
- ChromaDB
- OpenAI API

The components are integrated directly to keep the pipeline lightweight and transparent.

---

# Project Structure

Current relevant structure:

```text
Sensitive Data Detection & Compliance Assistant/
│
├── main.py
├── requirements.txt
├── .gitignore
│
├── modules/
│   ├── parser.py
│   ├── cleaner.py
│   ├── document_manager.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── qa.py
│   ├── compliance.py
│   ├── classifier.py
│   ├── analytics.py
│   ├── dashboard.py
│   │
│   └── detector/
│       ├── detector.py
│       └── ...
│
├── uploads/              # Local uploads; ignored by Git
├── extracted_text/       # Generated files; ignored by Git
└── .env                  # Local credentials; ignored by Git
```

---

# Running the Backend

## 1. Activate the Virtual Environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

## 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

## 3. Configure Gemini

Create a local `.env` file:

```env
GEMINI_API_KEY=your_api_key_here
```

Never commit `.env` to GitHub.

## 4. Start FastAPI

```powershell
uvicorn main:app --reload
```

The API runs at:

```text
http://127.0.0.1:8000
```

Interactive Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Tested RAG Examples

The current backend was tested using a GATE Computer Science syllabus.

### Broad Question

```text
What is the syllabus of the exam?
```

The system successfully generated an answer covering the major syllabus sections.

### Specific Question

```text
Does the syllabus include SQL?
```

The system correctly identified SQL under:

```text
Section 9: Databases
```

### Section-Specific Question

```text
What topics are covered under Operating System?
```

The system correctly retrieved the Operating System section and returned its listed topics.

These tests confirm that the current structure-aware chunking and basic retrieval pipeline are functioning.

---

# Development Status

## Completed

- [x] Document parsing
- [x] Text cleaning
- [x] Sensitive-data detection
- [x] Risk classification
- [x] AI compliance report generation
- [x] Hugging Face embeddings
- [x] FAISS vector store
- [x] RAG question answering
- [x] FastAPI backend
- [x] Single-document upload API
- [x] Multiple-document upload API
- [x] Structure-aware chunking
- [x] Query-aware retrieval
- [x] Basic retrieval-distance filtering
- [x] FastAPI Swagger testing
- [x] GitHub checkpoint

## Next Development Steps

- [ ] Hybrid retrieval using semantic similarity + keyword/phrase relevance
- [ ] Improve retrieval precision for highly specific questions
- [ ] Better source/relevance presentation
- [ ] Persistent document storage
- [ ] Multi-document RAG improvements
- [ ] Conversation memory
- [ ] Separate frontend
- [ ] Frontend-backend integration
- [ ] Production deployment
- [ ] Evaluation and benchmarking

---

# Current Development Considerations

### Temporary Document Storage

Documents are currently stored in an in-memory dictionary:

```python
document_store = {}
```

Uploaded documents therefore do not persist across a FastAPI restart.

Persistent storage will be introduced in a later phase.

### Retrieval Precision

The current semantic retrieval works for tested questions, but highly specific questions can still return semantically related but unnecessary chunks.

The next planned improvement is hybrid retrieval combining semantic similarity with keyword/phrase relevance.

### Detection Precision

Pattern-based sensitive-data detection can produce false positives for some numeric identifiers.

Future work will improve validation and contextual filtering for numeric sensitive-data patterns.

---

# Security

Sensitive credentials and uploaded documents are excluded from Git through `.gitignore`.

The repository should never contain:

```text
.env
API keys
Private uploaded documents
Virtual environments
Generated cache files
```

If an API key is accidentally exposed, it should be revoked or rotated immediately.

---

# Development Approach

The project is being developed incrementally:

```text
Detection
   ↓
Classification
   ↓
Compliance
   ↓
Embeddings
   ↓
FAISS
   ↓
RAG
   ↓
FastAPI
   ↓
Retrieval Improvements
   ↓
Frontend
   ↓
Deployment
```

This makes the system easier to test, debug, and evaluate component by component.

---

# Future Vision

The final system is intended to become a production-style enterprise compliance platform capable of:

- Uploading multiple enterprise documents
- Detecting sensitive information
- Assessing document risk
- Generating compliance reports
- Asking grounded questions over documents
- Supporting multi-document knowledge retrieval
- Providing traceable sources
- Maintaining conversational context
- Presenting compliance analytics through a dedicated frontend
- Running as a deployable FastAPI-based AI application

---

## License

This project is currently developed as a personal/academic portfolio project.
