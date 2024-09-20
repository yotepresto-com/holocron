from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from app.core.permission import Permission
from app.models import User, Role, UserRole, RolePermission
from app.schemas import UserCreate, UserUpdate, RoleRead
from app.database import get_session

# from app.auth import get_and_set_current_user

router = APIRouter(prefix="/users", tags=["User"])


# Utility Functions
def get_role(db: Session, role_id: int):
    return db.query(Role).filter(Role.id == role_id).first()


@router.post("/")
async def create_user(user: UserCreate, session: Session = Depends(get_session)):
    new_user = User(**user.dict())
    session.add(new_user)

    try:
        session.commit()
        session.refresh(new_user)
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    return new_user


@router.get("/{user_id}")
async def read_user(user_id: int, session: Session = Depends(get_session)):
    result = session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}")
async def update_user(
    user_id: int, user_update: UserUpdate, session: Session = Depends(get_session)
):
    result = session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(user, key, value)

    try:
        session.commit()
        session.refresh(user)
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail="Error updating user: {}".format(str(e))
        )

    return user


@router.delete("/{user_id}", response_model=dict)
async def delete_user(user_id: int, session: Session = Depends(get_session)):
    result = session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    session.delete(user)
    session.commit()
    return {"detail": "User deleted successfully"}


@router.get("/")
async def list_users(
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    result = session.execute(select(User).offset(offset).limit(limit))
    return result.scalars().all()


@router.get("/search/email/{email}")
async def search_user_by_email(email: str, session: Session = Depends(get_session)):
    result = session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/search/username/{username}")
async def search_user_by_username(
    username: str, session: Session = Depends(get_session)
):
    result = session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}/activate")
async def activate_user(user_id: int, session: Session = Depends(get_session)):
    result = session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    session.commit()
    session.refresh(user)
    return {"detail": "User activated successfully", "user": user}


@router.put("/{user_id}/deactivate")
async def deactivate_user(user_id: int, session: Session = Depends(get_session)):
    result = session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    session.commit()
    session.refresh(user)
    return {"detail": "User deactivated successfully", "user": user}


@router.post(
    "/{user_id}/roles/{role_id}",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a role to a user",
)
def assign_role(user_id: int, role_id: int, db: Session = Depends(get_session)):
    # Fetch the user
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch the role
    db_role = get_role(db, role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Check if role is already assigned
    existing_assignment = (
        db.query(UserRole)
        .filter(UserRole.user_id == user_id, UserRole.role_id == role_id)
        .first()
    )
    if existing_assignment:
        raise HTTPException(status_code=400, detail="Role already assigned to user")

    # Assign Role to User
    user_role = UserRole(user_id=user_id, role_id=role_id)
    db.add(user_role)
    db.commit()

    return {"detail": "Role assigned to user successfully"}


@router.delete(
    "/{user_id}/roles/{role_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Remove a role from a user",
)
def remove_role(user_id: int, role_id: int, db: Session = Depends(get_session)):
    # Fetch the user-role assignment
    db_user_role = (
        db.query(UserRole)
        .filter(UserRole.user_id == user_id, UserRole.role_id == role_id)
        .first()
    )
    if not db_user_role:
        raise HTTPException(
            status_code=404, detail="Role assignment not found for user"
        )

    # Remove the role assignment
    db.delete(db_user_role)
    db.commit()

    return {"detail": "Role removed from user successfully"}


@router.get(
    "/{user_id}/roles/",
    response_model=List[RoleRead],
    status_code=status.HTTP_200_OK,
    summary="Get all roles assigned to a user",
)
def get_user_roles(user_id: int, db: Session = Depends(get_session)):
    # Fetch the user
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch all roles assigned to the user
    user_roles = db.query(Role).join(UserRole).filter(UserRole.user_id == user_id).all()

    # Optionally, include permissions for each role
    for role in user_roles:
        role.permissions = [
            Permission(rp.permission)
            for rp in db.query(RolePermission)
            .filter(RolePermission.role_id == role.id)
            .all()
        ]

    return user_roles
