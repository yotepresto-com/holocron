from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
from app.core.permission import Permission

router = APIRouter(prefix="/permission", tags=["Permissions"])


class PermissionModel(BaseModel):
    name: str
    description: str


@router.get("/", response_model=List[PermissionModel], summary="Get Permission Catalog")
async def get_permissions():
    """
    Retrieve the list of all available permissions.
    """
    return [
        PermissionModel(name=perm.value, description=perm.description)
        for perm in Permission
    ]
