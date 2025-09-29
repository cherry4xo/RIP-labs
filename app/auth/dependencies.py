from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt

from app import domains, use_cases
from app.core.database import get_db_session, AsyncSession
from app.repository import SqlAlchemyDatabaseRepo
from app.core import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> domains.UserRead:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    repo = SqlAlchemyDatabaseRepo(db)
    user = await repo.get_user_by_id(user_id=int(user_id))
    if user is None:
        raise credentials_exception
    return user


CurrentUserDep = Annotated[domains.UserRead, Depends(get_current_user)]

def require_moderator(user: CurrentUserDep):
    if not user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator rights required for this operation."
        )

ModeratorDep = Depends(require_moderator)