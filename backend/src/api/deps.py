from collections.abc import AsyncIterator

from fastapi import FastAPI, File, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.db import async_session_maker
from src.exceptions import FileNotFound, StoredFileNotFound
from src.schemas import ValidatedUpload


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


async def get_validated_upload(file: UploadFile = File(...)) -> ValidatedUpload:
    return ValidatedUpload.model_validate(
        {
            "content": await file.read(),
            "filename": file.filename or "upload",
            "content_type": file.content_type,
        }
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    async def handle_validation_error(request, exc):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(FileNotFound)
    async def handle_file_not_found(request, exc):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "File not found"})

    @app.exception_handler(StoredFileNotFound)
    async def handle_stored_file_not_found(request, exc):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Stored file not found"})

