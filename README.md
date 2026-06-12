# MediBot: Role-Aware Advanced RAG Assistant

MediBot is a role-aware medical support assistant built for MediAssist Health Network. It uses FastAPI, Next.js, Qdrant Cloud, Groq, OpenAI embeddings, Docling-based document parsing, and SQLite SQL RAG.

The system enforces role-based access control at retrieval time so each user can only retrieve information from the document collections allowed for their role.

---

## Project Features

* Role-based login using demo users
* FastAPI backend
* Next.js frontend
* Qdrant Cloud vector database
* OpenAI embeddings for dense retrieval
* Groq LLM for answer generation
* Docling PDF parsing with HybridChunker
* PDF fallback parsing with `pypdf`
* SQLite SQL RAG for billing/database questions
* SQL access restricted to `billing_executive` and `admin`
* Sources shown for every answer
* Retrieval type shown in the frontend
* SQL query shown only when SQL RAG is allowed

---

## Role-Based Access Control

MediBot uses RBAC to restrict each role to only the collections they are allowed to access.

| Role              | Allowed Collections                            |
| ----------------- | ---------------------------------------------- |
| doctor            | general, clinical, nursing                     |
| nurse             | general, nursing                               |
| billing_executive | general, billing                               |
| technician        | general, equipment                             |
| admin             | general, clinical, nursing, billing, equipment |

SQL RAG is only allowed for:

```text
billing_executive
admin
```

Unauthorized roles, such as `nurse`, cannot access SQL/database results.

---

## Dataset Collections

The dataset is stored in:

```text
backend/data/mediassist_data
```

Expected folder structure:

```text
backend/data/mediassist_data/
├── billing/
├── clinical/
├── db/
├── equipment/
├── general/
└── nursing/
```

SQLite database:

```text
backend/data/mediassist_data/db/mediassist.db
```

---

## Metadata Attached to Every Chunk

Each indexed chunk includes the following metadata:

```text
source_document
collection
access_roles
section_title
chunk_type
```

This metadata is used for source display and RBAC filtering.

---

## Tech Stack

### Backend

* FastAPI
* LangChain
* Qdrant Cloud
* Groq
* OpenAI embeddings
* Docling
* pypdf
* SQLite

### Frontend

* Next.js
* React
* Tailwind CSS

---

## Environment Variables

Create this file:

```text
backend/.env
```

Example:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b

OPENAI_API_KEY=your_openai_api_key_here

QDRANT_URL=your_qdrant_cloud_url_here
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_COLLECTION=medibot_docs

HF_TOKEN=your_huggingface_token_optional

DATA_DIR=data/mediassist_data
DB_PATH=data/mediassist_data/db/mediassist.db
```

A safe example file is also included as:

```text
backend/.env.example
```

Do not commit real API keys.

---

## Backend Setup

Go to the backend folder:

```bash
cd backend
```

Create and activate virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the FastAPI backend:

```bash
uvicorn app.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

Swagger API docs:

```text
http://127.0.0.1:8000/docs
```

---

## Frontend Setup

Go to the frontend folder:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Run the frontend:

```bash
npm run dev
```

Frontend runs at:

```text
http://localhost:3000
```

---

## Demo Users

| Username     | Password   | Role              |
| ------------ | ---------- | ----------------- |
| dr.mehta     | doctor     | doctor            |
| nurse.priya  | nurse      | nurse             |
| billing.ravi | billing    | billing_executive |
| tech.anand   | technician | technician        |
| admin.sys    | admin      | admin             |

---

## API Endpoints

### Health Check

```text
GET /health
```

Returns backend status.

### Login

```text
POST /login
```

Example request:

```json
{
  "username": "nurse.priya",
  "password": "nurse"
}
```

### Chat

```text
POST /chat
```

Example request:

```json
{
  "question": "What is the leave policy?",
  "role": "nurse"
}
```

### Role Collections

```text
GET /collections/{role}
```

Example:

```text
GET /collections/nurse
```

---

## Running Ingestion

From the backend folder:

```bash
python run_ingestion.py
```

This parses the documents, creates chunks, attaches metadata, and indexes the chunks into Qdrant Cloud.

The indexed Qdrant collection is:

```text
medibot_docs
```

After indexing, create payload indexes:

```bash
python create_qdrant_indexes.py
```

---

## RAG Flow

```text
User logs in with role
        ↓
User asks question
        ↓
Backend checks role
        ↓
If billing/database question:
    SQL RAG is used only for billing_executive or admin
        ↓
Otherwise:
    Qdrant retrieval runs with RBAC metadata filter
        ↓
Allowed chunks are retrieved
        ↓
Chunks are reranked
        ↓
Groq generates answer
        ↓
Frontend displays answer, sources, and retrieval type
```

---

## Architecture Diagram

```text
                 ┌────────────────────┐
                 │   Next.js Frontend  │
                 │ Login + Chat UI     │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │   FastAPI Backend   │
                 │ /login /chat        │
                 └─────────┬──────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                 │
          ▼                                 ▼
┌────────────────────┐           ┌────────────────────┐
│ Qdrant Vector RAG  │           │ SQLite SQL RAG      │
│ RBAC metadata      │           │ billing/admin only  │
│ filtering          │           │                     │
└─────────┬──────────┘           └─────────┬──────────┘
          │                                │
          ▼                                ▼
┌────────────────────┐           ┌────────────────────┐
│ Indexed Documents  │           │ mediassist.db       │
│ Docling chunks     │           │ Billing data        │
└────────────────────┘           └────────────────────┘
```

---

## Final Demo Checklist

### 1. Qdrant RAG Test

Role:

```text
nurse
```

Question:

```text
What is the leave policy?
```

Expected result:

* Retrieval type: `qdrant_rag`
* Sources include `leave_policy.pdf`
* Sources are only from collections allowed for nurse: `general` and `nursing`

---

### 2. SQL RAG Allowed Test

Role:

```text
billing_executive
```

Question:

```text
Show me the total claim amount by status
```

Expected result:

* Retrieval type: `sql_rag`
* Source includes `mediassist.db`
* SQL query is shown
* Claim totals are displayed

---

### 3. SQL RAG Blocked Test

Role:

```text
nurse
```

Question:

```text
Show me the total claim amount by status
```

Expected result:

* SQL data is not exposed
* No claim totals are shown
* `mediassist.db` is not returned as a source
* The answer says the information could not be found in accessible documents

---

## Screenshots

Add screenshots in this folder:

```text
screenshots/
```

Recommended screenshots:

```text
screenshots/nurse-leave-policy.png
screenshots/billing-sql-rag.png
screenshots/nurse-sql-blocked.png
```

Then add them here:

### Nurse Leave Policy

![Nurse Leave Policy](screenshots/nurse-leave-policy.png)

### Billing Executive SQL RAG

![Billing Executive SQL RAG](screenshots/billing-sql-rag.png)

### Nurse SQL Blocked

![Nurse SQL Blocked](screenshots/nurse-sql-blocked.png)

---

## Tool Substitutions and Notes

Docling was used for PDF parsing and HybridChunker-based chunking.

When Hugging Face model downloads were unstable, a `pypdf` fallback parser was added so ingestion could continue.

OpenAI embeddings were used for dense Qdrant indexing and search.

Groq was used for final answer generation.

Qdrant Cloud was used as the vector database.

FastEmbed and sentence-transformers are included in the requirements for hybrid sparse retrieval and cross-encoder reranking support. In this implementation, a lightweight keyword boost reranker is used because local Hugging Face model downloads were unstable in the development environment.

---

## Security Notes

* Real `.env` files are ignored by Git.
* API keys should not be committed.
* SQL queries are restricted to safe `SELECT` statements only.
* SQL RAG is blocked for unauthorized roles.
* Qdrant retrieval uses role-based metadata filters.

---

## Project Status

Completed:

* Backend API
* Frontend UI
* RBAC collection filtering
* Qdrant document retrieval
* SQL RAG
* SQL role restriction
* Source display
* Retrieval type display
* Demo test cases

Optional future improvements:

* Add production authentication
* Add full hybrid dense + sparse Qdrant retrieval
* Add cross-encoder reranking when local model downloads are stable
* Add deployment instructions
