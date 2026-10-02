from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import Base, engine
from .api.auth import router as auth_router
from .api.chat import router as chat_router
from .api.documents import router as documents_router

Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, version="1.0.0")
allowed_origins = [
    origin.strip()
    for origin in (settings.cors_origins or "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]
allowed_origins = list(dict.fromkeys(allowed_origins + ["http://localhost:5173", "http://127.0.0.1:5173"]))
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(documents_router)


@app.get("/")
def root():
    return {"status": "ok", "service": settings.app_name, "message": "API is running"}


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}
