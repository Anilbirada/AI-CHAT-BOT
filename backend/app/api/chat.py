import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..database import get_db
from ..models import User, Conversation, Message
from ..schemas import ChatRequest
from ..utils.security import decode_token
from ..services.rag_service import retrieve, build_context
from ..services.agent_service import run_agent_turn, stream_agent_turn

router=APIRouter(prefix="/api", tags=["chat"]); bearer=HTTPBearer(auto_error=False)
def current_user(creds:HTTPAuthorizationCredentials | None=Depends(bearer),db:Session=Depends(get_db)):
    if creds is None:
        raise HTTPException(401,"Authentication required")
    try: uid=int(decode_token(creds.credentials)["sub"])
    except Exception: raise HTTPException(401,"Invalid or expired token")
    user=db.get(User,uid)
    if not user: raise HTTPException(401,"User not found")
    return user


def _get_recent_history(db: Session, conversation_id: int, limit: int = 8):
    history = db.scalars(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(limit)
    ).all()
    return [{"role": item.role, "content": item.content} for item in reversed(history)]


@router.post("/chat")
async def chat(data:ChatRequest,user=Depends(current_user),db:Session=Depends(get_db)):
    if not data.message or not data.message.strip():
        raise HTTPException(400, "Please enter a message before sending.")

    convo=db.get(Conversation,data.conversation_id) if data.conversation_id else None
    if not convo:
        convo=Conversation(user_id=user.id,title=data.message[:60]); db.add(convo); db.commit(); db.refresh(convo)
    if convo.user_id != user.id: raise HTTPException(403,"Forbidden")

    user_message = data.message.strip()
    db.add(Message(conversation_id=convo.id,role="user",content=user_message)); db.commit()
    results=retrieve(db,user_message,data.subject,data.semester,user.role)
    context=build_context(results)
    history = _get_recent_history(db, convo.id)

    try:
        agent_response = await run_agent_turn(user_message, history=history, context=context, subject=data.subject, semester=data.semester, mode=data.mode, role=user.role)
        text = agent_response["answer"]
        intent = agent_response["intent"]
    except Exception as exc:
        raise HTTPException(503, str(exc)) from exc

    sources=[{"filename":d.filename,"page":c.page_number} for c,d in results]
    db.add(Message(conversation_id=convo.id,role="assistant",content=text,sources=sources)); db.commit()

    convo.title = convo.title or user_message[:60]
    convo.updated_at = __import__("datetime").datetime.utcnow()
    db.commit()
    return {"conversation_id":convo.id,"answer":text,"sources":sources,"intent":intent}


@router.post("/chat/stream")
async def chat_stream(data:ChatRequest,user=Depends(current_user),db:Session=Depends(get_db)):
    if not data.message or not data.message.strip():
        raise HTTPException(400, "Please enter a message before sending.")

    convo=db.get(Conversation,data.conversation_id) if data.conversation_id else None
    if not convo:
        convo=Conversation(user_id=user.id,title=data.message[:60]); db.add(convo); db.commit(); db.refresh(convo)
    if convo.user_id != user.id: raise HTTPException(403,"Forbidden")

    user_message = data.message.strip()
    db.add(Message(conversation_id=convo.id,role="user",content=user_message)); db.commit()
    results=retrieve(db,user_message,data.subject,data.semester,user.role)
    context=build_context(results)
    history = _get_recent_history(db, convo.id)

    async def generate():
        try:
            partial = []
            async for chunk in stream_agent_turn(user_message, history=history, context=context, subject=data.subject, semester=data.semester, mode=data.mode, role=user.role):
                partial.append(chunk)
                yield f"data: {json.dumps({'type':'token','content':chunk})}\n\n"
            response_text = "".join(partial)
            sources=[{"filename":d.filename,"page":c.page_number} for c,d in results]
            db.add(Message(conversation_id=convo.id,role="assistant",content=response_text,sources=sources)); db.commit()
            convo.title = convo.title or user_message[:60]
            convo.updated_at = __import__("datetime").datetime.utcnow()
            db.commit()
            yield "data: [DONE]\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type':'error','content':str(exc)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})

@router.get("/chats")
def chats(user=Depends(current_user),db:Session=Depends(get_db)):
    return [{"id":c.id,"title":c.title,"updated_at":c.updated_at.isoformat()} for c in db.scalars(select(Conversation).where(Conversation.user_id==user.id).order_by(Conversation.updated_at.desc())).all()]

@router.get("/chats/{conversation_id}/messages")
def chat_messages(conversation_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    convo=db.get(Conversation, conversation_id)
    if not convo or convo.user_id != user.id:
        raise HTTPException(404, "Conversation not found")
    return [{
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "sources": m.sources or [],
        "created_at": m.created_at.isoformat(),
    } for m in db.scalars(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())).all()]
