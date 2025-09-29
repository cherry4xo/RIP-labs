from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from app import domains
from app.core.database import DBSessionDep
from app.repository import SqlAlchemyDatabaseRepo
from app.auth.dependencies import CurrentUserDep
from app.auth import security

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=domains.UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: domains.UserCreate, db: DBSessionDep):
    repo = SqlAlchemyDatabaseRepo(db)
    db_user = await repo.get_user_by_login(user_data.login)
    if db_user:
        raise HTTPException(status_code=400, detail="Login already registered")
    
    new_user = await repo.create_user(user_data)
    await db.commit()
    return domains.UserRead.model_validate(new_user)


@router.post("/token", response_model=domains.Token)
async def login_for_access_token(
    db: DBSessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    repo = SqlAlchemyDatabaseRepo(db)
    user = await repo.get_user_by_login(form_data.username)
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = security.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=domains.UserRead)
async def read_users_me(current_user: CurrentUserDep):
    return current_user


@router.put("/users/me", response_model=domains.UserRead)
async def update_users_me(user_data: domains.UserUpdate, user: CurrentUserDep, db: DBSessionDep):
    repo = SqlAlchemyDatabaseRepo(db)
    if user_data.login and await repo.get_user_by_login(user_data.login):
        raise HTTPException(status_code=400, detail="This login is already taken.")
        
    updated_user_orm = await repo.update_user(user.id, user_data)
    await db.commit()
    return domains.UserRead.model_validate(updated_user_orm)