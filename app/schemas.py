from pydantic import BaseModel, EmailStr, constr, Field
from typing import Optional, List
from app.core.permission import Permission


# User Schemas
class UserCreate(BaseModel):
    username: constr(strip_whitespace=True, min_length=1, max_length=50)
    email: EmailStr
    name: Optional[constr(strip_whitespace=True, max_length=100)] = Field(default=None)
    is_active: bool = Field(default=True)


class UserUpdate(BaseModel):
    username: Optional[constr(strip_whitespace=True, min_length=1, max_length=50)] = (
        Field(default=None)
    )
    email: Optional[EmailStr] = Field(default=None)
    name: Optional[constr(strip_whitespace=True, max_length=100)] = Field(default=None)


# Role Schemas
class RoleBase(BaseModel):
    name: str = Field(..., example="admin")
    description: Optional[str] = Field(
        None, example="Administrator role with full permissions."
    )


class RoleCreate(RoleBase):
    permissions: Optional[List[Permission]] = Field(
        default_factory=list, example=[Permission.CREATE_PRODUCT]
    )


class RoleRead(RoleBase):
    id: int
    permissions: List[Permission] = []
