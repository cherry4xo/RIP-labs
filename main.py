from fastapi import FastAPI

from bmstu.init import init_app


app = FastAPI()

init_app(app)