from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Document, DocumentChunk
from .chat import current_user
from ..config import settings
from ..services.document_service import extract_text, chunk_text

router=APIRouter(prefix="/api/documents", tags=["documents"])
@router.post("/upload")
async def upload(file:UploadFile=File(...), user=Depends(current_user), db:Session=Depends(get_db)):
    suffix=Path(file.filename).suffix.lower()
    if suffix not in {".pdf",".docx",".txt"}: raise HTTPException(400,"Only PDF, DOCX and TXT are supported")
    if user.role not in {"ADMIN","PROFESSOR"}: raise HTTPException(403,"Only staff can upload knowledge documents")
    root=Path(settings.storage_path); root.mkdir(parents=True,exist_ok=True)
    safe=f"{user.id}_{Path(file.filename).name}"; path=root/safe; path.write_bytes(await file.read())
    doc=Document(filename=file.filename,document_type=suffix[1:].upper(),uploaded_by=user.id,access_level="STUDENT"); db.add(doc); db.commit(); db.refresh(doc)
    for page,text in extract_text(str(path),suffix):
        for piece in chunk_text(text): db.add(DocumentChunk(document_id=doc.id,content=piece,page_number=page,metadata_json={"source":file.filename}))
    db.commit(); return {"id":doc.id,"filename":doc.filename,"status":"INGESTED"}

@router.get("")
def list_documents(user=Depends(current_user),db:Session=Depends(get_db)):
    return [{"id":d.id,"filename":d.filename,"type":d.document_type,"access_level":d.access_level} for d in db.query(Document).all() if user.role != "STUDENT" or d.access_level in {"STUDENT","PUBLIC"}]
