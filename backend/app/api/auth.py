from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..database import get_db
from ..models import User
from ..schemas import RegisterRequest, LoginRequest
from ..utils.security import hash_password, verify_password, create_token

router=APIRouter(prefix="/api/auth", tags=["auth"])
@router.post("/register")
def register(data:RegisterRequest, db:Session=Depends(get_db)):
    if db.scalar(select(User).where(User.email==data.email)): raise HTTPException(409,"Email already registered")
    role=data.role.upper()
    if role not in {"STUDENT","FACULTY","ADMIN"}: raise HTTPException(400,"Invalid role")
    user=User(name=data.name,email=data.email,password_hash=hash_password(data.password),role=role,department=data.department,semester=data.semester)
    db.add(user); db.commit(); db.refresh(user)
    return {"access_token":create_token(user.id,user.role),"user":{"id":user.id,"name":user.name,"email":user.email,"role":user.role}}

@router.post("/login")
def login(data:LoginRequest, db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==data.email))
    if not user or not verify_password(data.password,user.password_hash): raise HTTPException(401,"Invalid email or password")
    return {"access_token":create_token(user.id,user.role),"user":{"id":user.id,"name":user.name,"email":user.email,"role":user.role}}
