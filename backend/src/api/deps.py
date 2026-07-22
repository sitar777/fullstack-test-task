from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.db import async_session_maker
from src.exceptions import EmptyFile, FileNotFound, FileTooLarge, StoredFileNotFound


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(FileNotFound)
    async def handle_file_not_found(request, exc):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "File not found"})

    @app.exception_handler(StoredFileNotFound)
    async def handle_stored_file_not_found(request, exc):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Stored file not found"})

    @app.exception_handler(EmptyFile)
    async def handle_empty_file(request, exc):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "File is empty"})

    @app.exception_handler(FileTooLarge)
    async def handle_file_too_large(request, exc):
        return JSONResponse(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            content={"detail": "File is too large"},
        )
