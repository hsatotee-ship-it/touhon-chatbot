import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


# --- Auth ---
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: str | None = None
    role: str | None = None
    is_active: bool | None = None


# --- Documents ---
class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    page_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentDetail(DocumentResponse):
    ocr_text: str | None = None
    gcs_path: str


# --- Chat ---
class ChatRequest(BaseModel):
    message: str
    session_id: uuid.UUID | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    session_id: uuid.UUID


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    sources: list
    created_at: datetime

    class Config:
        from_attributes = True


# --- Admin ---
class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    details: dict
    ip_address: str | None
    created_at: datetime

    class Config:
        from_attributes = True
