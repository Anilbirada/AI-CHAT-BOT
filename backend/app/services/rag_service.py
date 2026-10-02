from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from ..models import DocumentChunk, Document

FALLBACK = "I couldn't find sufficient information in the available academic materials to answer this confidently. Please upload the relevant syllabus/notes or ask your professor."
MAX_CONTEXT_CHARS = 3000


def retrieve(db: Session, query: str, subject: str | None = None, semester: int | None = None, role: str = "STUDENT"):
    terms = [t.lower() for t in query.split() if len(t) > 3][:8]
    stmt = select(DocumentChunk, Document).join(Document, Document.id == DocumentChunk.document_id)
    if semester:
        stmt = stmt.where(or_(Document.semester == semester, Document.semester.is_(None)))
    if role == "STUDENT":
        stmt = stmt.where(Document.access_level.in_(["STUDENT", "PUBLIC"]))

    if terms:
        stmt = stmt.where(or_(*[DocumentChunk.content.ilike(f"%{term}%") for term in terms]))

    rows = db.execute(stmt.limit(25)).all()
    scored = []
    for chunk, doc in rows:
        text = (chunk.content or "").lower()
        score = sum(text.count(t) for t in terms)
        if subject and (subject.lower() in text):
            score += 3
        if score > 0:
            scored.append((score, chunk, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(c, d) for s, c, d in scored[:3]]


def build_context(results):
    context = "\n\n".join(f"[Source: {d.filename}, page {c.page_number or 'N/A'}]\n{c.content}" for c, d in results)
    if len(context) > MAX_CONTEXT_CHARS:
        return context[:MAX_CONTEXT_CHARS].rstrip() + "\n... [context truncated for speed]"
    return context
