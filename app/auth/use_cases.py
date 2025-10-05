from app import domains
from app.interfaces import AbstractDatabaseRepo, AbstractFileStorage
from app.auth import security
from app.interfaces import VulnerabilityAssessmentNotFoundError, ReportNotFoundError
from fastapi import HTTPException, status


async def register_new_user(repo: AbstractDatabaseRepo, user_data: domains.UserCreate) -> domains.UserRead:
    """
    Register a new user.
    Raises HTTPException if login is already registered.
    """
    db_user = await repo.get_user_by_login(user_data.login)
    if db_user:
        raise HTTPException(status_code=400, detail="Login already registered")
    
    new_user = await repo.create_user(user_data)
    return domains.UserRead.model_validate(new_user)


async def authenticate_user(repo: AbstractDatabaseRepo, username: str, password: str) -> dict:
    """
    Authenticate a user and generate access token.
    Raises HTTPException for invalid credentials.
    """
    user = await repo.get_user_by_login(username)
    if not user or not security.verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = security.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


async def update_user_profile(repo: AbstractDatabaseRepo, user_id: int, user_data: domains.UserUpdate) -> domains.UserRead:
    """
    Update user profile information.
    Raises HTTPException if login is already taken.
    """
    if user_data.login:
        existing_user = await repo.get_user_by_login(user_data.login)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="This login is already taken.")
        
    updated_user_orm = await repo.update_user(user_id, user_data)
    return domains.UserRead.model_validate(updated_user_orm)
