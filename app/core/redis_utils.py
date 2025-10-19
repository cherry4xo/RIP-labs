import jwt
from datetime import datetime, timedelta
from app.core import settings
from app.core.settings import redis_client


async def add_token_to_blacklist(token: str, expires_delta: timedelta = None) -> bool:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = payload.get("exp")

        if not exp:
            return False

        if expires_delta:
            expire_at = datetime.now() + expires_delta
        else:
            expire_at = datetime.fromtimestamp(exp)

        ttl = int((expire_at - datetime.now()).total_seconds())

        if ttl <= 0:
            return False

        await redis_client.setex(f"blacklist:{token}", ttl, "blacklisted")
        return True
    except jwt.PyJWTError:
        return False
    except Exception:
        return False


async def is_token_blacklisted(token: str) -> bool:
    try:
        result = await redis_client.get(f"blacklist:{token}")
        return result is not None
    except Exception:
        return False
