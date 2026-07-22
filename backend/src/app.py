from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.deps import register_exception_handlers
from src.api.routes import alerts, files


def create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(files.router)
    app.include_router(alerts.router)
    return app


app = create_app()
