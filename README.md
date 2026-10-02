# DSCE AI Academic Assistant

Premium full-stack foundation for the DSCE AI Academic Assistant. The design follows the supplied specification: modular RAG architecture, role-based access, document ingestion, academic citations, student/professor/admin expansion points, and a modern responsive academic UI.

## Quick start with Docker
1. Install Docker Desktop.
2. From this folder run: `docker compose up --build`
3. Frontend: http://localhost:5173
4. Backend docs: http://localhost:8000/docs
5. Health: http://localhost:8000/health

## Local backend
`cd backend`
`python -m venv .venv`
Windows: `.venv\\Scripts\\activate`
`pip install -r requirements.txt`
`uvicorn app.main:app --reload`

## Local frontend
`cd frontend`
`npm install`
`npm run dev`

## Important
- No real DSCE syllabus, rules, CO/PO mappings, exam patterns, or official documents are invented.
- Configure an LLM provider through the service abstraction before treating responses as production AI.
- Add pgvector embeddings/reranking in the RAG service for semantic retrieval.
- Staff upload is protected by backend role checks.
- Replace development JWT/database secrets before deployment.
