from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from app import domains
from app.core.database import DBSessionDep
from app.repository import SqlAlchemyDatabaseRepo
from app.auth.dependencies import CurrentUserDep
from app.auth import security, use_cases

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=domains.UserRead, status_code=status.HTTP_201_CREATED)
async def register_user_endpoint(user_data: domains.UserCreate, db: DBSessionDep):
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        new_user = await use_cases.register_new_user(repo, user_data)
        await db.commit()
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/token", response_model=domains.Token)
async def login_for_access_token_endpoint(
    db: DBSessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        token_data = await use_cases.authenticate_user(repo, form_data.username, form_data.password)
        return token_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/me", response_model=domains.UserRead)
async def read_users_me(current_user: CurrentUserDep):
    return current_user


@router.put("/users/me", response_model=domains.UserRead)
async def update_users_me_endpoint(user_data: domains.UserUpdate, user: CurrentUserDep, db: DBSessionDep):
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        updated_user = await use_cases.update_user_profile(repo, user.id, user_data)
        await db.commit()
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout")
async def logout_user(current_user: CurrentUserDep):
    """
    Деавторизация пользователя (заглушка).
    В текущей версии с заглушкой авторизации не выполняет реальных действий.
    """
    return {"message": "Successfully logged out"}
