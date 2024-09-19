from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from app.models import User
from app.schemas import UserCreate, UserUpdate
from app.database import get_session

# from app.auth import get_and_set_current_user

router = APIRouter()


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
async def update_user(user_id: int, user_update: UserUpdate, session: Session = Depends(get_session)):
    result = session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(user, key, value)

    session.commit()
    session.refresh(user)
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
    limit: int = Query(100, ge=1, le=1000)
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
async def search_user_by_username(username: str, session: Session = Depends(get_session)):
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
