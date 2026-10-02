from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = "STUDENT"
    department: str | None = None
    semester: int | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChatRequest(BaseModel):
    conversation_id: int | None = None
    message: str
    subject: str | None = None
    semester: int | None = None
    mode: str = "General Problem Solving"

class ChatResponse(BaseModel):
    conversation_id: int
    answer: str
    sources: list[dict] = []
