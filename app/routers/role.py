from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models import (
    Role,
    RolePermission,
    User,
    UserRole,
)
from app.schemas import (
    RoleCreate,
    RoleRead,
)
from app.database import get_session
from app.core.permission import Permission  # Import the Permission Enum

router = APIRouter(prefix="/roles", tags=["Role"])


# Utility Functions
def get_role(db: Session, role_id: int):
    return db.query(Role).filter(Role.id == role_id).first()


def get_role_by_name(db: Session, name: str):
    return db.query(Role).filter(Role.name == name).first()


# Endpoints


@router.post(
    "/",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
)
def create_role(role: RoleCreate, db: Session = Depends(get_session)):
    # Check if role name already exists
    db_role = get_role_by_name(db, role.name)
    if db_role:
        raise HTTPException(
            status_code=400, detail="Role with this name already exists"
        )

    # Create Role
    db_role = Role(name=role.name, description=role.description)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)

    # Assign Permissions
    if role.permissions:
        permissions = [
            RolePermission(role_id=db_role.id, permission=perm.value)
            for perm in role.permissions
        ]
        print(permissions)
        db.bulk_save_objects(permissions)
        db.commit()

    # Refresh to get updated relationships
    db.refresh(db_role)
    db_role.permissions = [
        Permission(rp.permission)
        for rp in db.query(RolePermission)
        .filter(RolePermission.role_id == db_role.id)
        .all()
    ]

    return db_role


@router.get("/", response_model=List[RoleRead], summary="List roles with pagination")
def list_roles(skip: int = 0, limit: int = 10, db: Session = Depends(get_session)):
    roles = db.query(Role).offset(skip).limit(limit).all()
    for role in roles:
        role.permissions = [
            Permission(rp.permission)
            for rp in db.query(RolePermission)
            .filter(RolePermission.role_id == role.id)
            .all()
        ]
    return roles


@router.get(
    "/{role_id}", response_model=RoleRead, summary="Retrieve a specific role by ID"
)
def read_role(role_id: int, db: Session = Depends(get_session)):
    db_role = get_role(db, role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    db_role.permissions = [
        Permission(rp.permission)
        for rp in db.query(RolePermission)
        .filter(RolePermission.role_id == db_role.id)
        .all()
    ]
    return db_role


@router.put("/{role_id}", response_model=RoleRead, summary="Update an existing role")
def update_role(
    role_id: int, role_update: RoleCreate, db: Session = Depends(get_session)
):
    db_role = get_role(db, role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role_update.name:
        # Check if new name is unique
        existing_role = get_role_by_name(db, role_update.name)
        if existing_role and existing_role.id != role_id:
            raise HTTPException(
                status_code=400, detail="Role with this name already exists"
            )
        db_role.name = role_update.name

    if role_update.description is not None:
        db_role.description = role_update.description

    db.commit()
    db.refresh(db_role)

    # Handle Permissions Update
    if role_update.permissions is not None:
        # Remove existing permissions
        db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
        db.commit()

        # Add new permissions
        new_permissions = [
            RolePermission(role_id=role_id, permission=perm.value)
            for perm in role_update.permissions
        ]
        db.bulk_save_objects(new_permissions)
        db.commit()

    # Refresh to get updated permissions
    db_role = get_role(db, role_id)
    db_role.permissions = [
        Permission(rp.permission)
        for rp in db.query(RolePermission)
        .filter(RolePermission.role_id == db_role.id)
        .all()
    ]
    return db_role


@router.delete(
    "/{role_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a role"
)
def delete_role(role_id: int, db: Session = Depends(get_session)):
    db_role = get_role(db, role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    db.delete(db_role)
    db.commit()
    return
