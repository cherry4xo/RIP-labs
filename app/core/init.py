from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.middlewares import init_middlewares
# from app.views import router
from app.api import auth, orders, services
from app.core.database import get_session_manager


def add_routes(app: FastAPI):
    app.include_router(auth.router)
    app.include_router(orders.router)
    app.include_router(services.router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To run this function, command line argument '--lifespan=on' is required.
    """
    print("INFO:     Application startup...")
    
    sessionmanager = get_session_manager()

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