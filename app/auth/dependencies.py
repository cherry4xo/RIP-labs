from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status, Header

from app import domains
from app.core.database import get_db_session, AsyncSession
from app.repository import SqlAlchemyDatabaseRepo


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    x_user_id: Optional[str] = Header(default="3")
) -> domains.UserRead:
    """
    Заглушка для авторизации: получает user_id из заголовка X-User-Id.
    По умолчанию использует user_id=1.
    """
    try:
        user_id = int(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-User-Id header"
        )

    repo = SqlAlchemyDatabaseRepo(db)
    user = await repo.get_user_by_id(user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return user


CurrentUserDep = Annotated[domains.UserRead, Depends(get_current_user)]

def require_moderator(user: CurrentUserDep):
    if not user.is_moderator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator rights required for this operation."
        )

ModeratorDep = Depends(require_moderator)
