from pydantic import BaseModel, EmailStr, constr, Field
from typing import Optional


class UserCreate(BaseModel):
    username: constr(strip_whitespace=True, min_length=1, max_length=50)
    email: EmailStr
    name: constr(strip_whitespace=True, max_length=100) = Field(default=None)
    is_active: bool = Field(default=True)


class UserUpdate(BaseModel):
    username: Optional[constr(strip_whitespace=True, min_length=1, max_length=50)] = Field(default=None)
    email: Optional[EmailStr] = Field(default=None)
    name: Optional[constr(strip_whitespace=True, max_length=100)] = Field(default=None)
