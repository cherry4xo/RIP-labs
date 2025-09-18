from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.middlewares import init_middlewares
from app.views import router
from app.core.database import sessionmanager
from app.models import Base


def add_routes(app: FastAPI):
    app.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To run this function, command line argument '--lifespan=on' is required.
    """
    print("INFO:     Application startup...")
    
    async with sessionmanager._engine.begin() as conn:
        print("INFO:     Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("INFO:     Database tables created.")

    yield

    print("INFO:     Application shutdown...")
    if sessionmanager._engine is not None:
        await sessionmanager.close()


def create_app():
    app = FastAPI(lifespan=lifespan)

    init_middlewares(app)
    add_routes(app)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    return app