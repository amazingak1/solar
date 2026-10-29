from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class Role(str, Enum):
    admin = "admin"
    owner = "owner"
    investor = "investor"


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Role = Role.owner


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: Role
    created_at: datetime

    class Config:
        from_attributes = True


class UserInDB(BaseModel):
    id: Optional[str] = None
    name: str
    email: str
    hashed_password: str
    role: Role
    created_at: datetime = Field(default_factory=datetime.utcnow)
