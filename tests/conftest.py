import asyncio
from typing import IO, AsyncGenerator, Dict, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.auth.security import get_password_hash
from app.interfaces import AbstractFileStorage
from main import app
from app.models import Base, User
from app.core.database import get_db_session
from app.domains import UserCreate
from app.repository import SqlAlchemyDatabaseRepo
from app.core import settings
from app.file_storage.minio_storage import get_file_storage

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


class InMemoryFileStorage(AbstractFileStorage):
    """
    Фейковое файловое хранилище, которое хранит файлы в словаре в памяти.
    Полностью имитирует интерфейс AbstractFileStorage для тестов.
    """
    def __init__(self):
        self.files: dict[str, bytes] = {}
        print("Initialized InMemoryFileStorage")

    def save(self, file: IO, filename: str, content_type: str) -> str:
        content = file.read()
        self.files[filename] = content
        print(f"Saved {filename} to in-memory storage.")
        return f"http://test-storage.com/service-images/{filename}"
    
    def delete(self, file_url: str) -> None:
        filename = file_url.split('/')[-1]
        if filename in self.files:
            del self.files[filename]
            print(f"Deleted {filename} from in-memory storage.")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DB_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
def in_memory_file_storage() -> InMemoryFileStorage:
    return InMemoryFileStorage()


@pytest.fixture(scope="function")
def override_get_file_storage(in_memory_file_storage: InMemoryFileStorage):
    def _override():
        return in_memory_file_storage
    return _override


@pytest.fixture(scope="function")
def override_get_db_session(db_session: AsyncSession):
    """Переопределяет зависимость get_db_session, чтобы использовать тестовую БД."""
    async def _override_get_db_session():
        yield db_session
    return _override_get_db_session


@pytest.fixture(scope="function")
def test_app(override_get_db_session, override_get_file_storage, monkeypatch):
    """Создает экземпляр приложения с подмененной зависимостью БД."""
    monkeypatch.setattr(settings, "DB_URL", TEST_DB_URL)

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_file_storage] = override_get_file_storage
    yield app
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(test_app) -> Generator[TestClient, None, None]:
    """Создает синхронный клиент для отправки запросов к приложению."""
    with TestClient(test_app) as test_client:
        yield test_client


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Создает и сохраняет обычного пользователя в тестовую БД."""
    user = User(login="testuser", password_hash=get_password_hash("password"))
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture(scope="function")
async def test_moderator(db_session: AsyncSession) -> User:
    """Создает и сохраняет пользователя-модератора."""
    moderator = User(login="moduser", password_hash=get_password_hash("password"), is_moderator=True)
    db_session.add(moderator)
    await db_session.commit()
    return moderator


@pytest.fixture(scope="function")
def test_user_token_headers(client: TestClient, test_user: User) -> Dict[str, str]:
    """Логинится обычным пользователем и возвращает заголовки с токеном."""
    login_response = client.post(
        "/auth/token",
        data={"username": test_user.login, "password": "password"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_moderator_token_headers(client: TestClient, test_moderator: User) -> Dict[str, str]:
    """Логинится модератором и возвращает заголовки с токеном."""
    login_response = client.post(
        "/auth/token",
        data={"username": test_moderator.login, "password": "password"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}