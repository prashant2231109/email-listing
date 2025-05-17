from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    created_at: datetime

class EmailFilter(BaseModel):
    subject: Optional[str] = None
    sender: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class EmailCreate(BaseModel):
    recipient: EmailStr
    subject: str
    body: str
    html_body: Optional[str] = None

class EmailResponse(BaseModel):
    id: str
    subject: str
    sender: str
    date: datetime
    body: str
    folder: str
    read: bool
    created_at: datetime

class EmailFetchRequest(BaseModel):
    email_address: EmailStr
    password: str
    folder: str = "INBOX"
    limit: int = Field(10, ge=1, le=50)

class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 20