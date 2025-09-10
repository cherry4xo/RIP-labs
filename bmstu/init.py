from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from bmstu.middlewares import init_middlewares
from bmstu_lab.views import router


def add_routes(app: FastAPI):
    app.include_router(router)


def init_app(app: FastAPI):
    main_app_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan_wrapper(app):
        async with main_app_lifespan(app) as maybe_state:
            yield maybe_state

    app.router.lifespan_context = lifespan_wrapper
    init_middlewares(app)
    add_routes(app)
    app.mount("/static", StaticFiles(directory="static"), name="static")