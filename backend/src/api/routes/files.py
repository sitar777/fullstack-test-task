from typing import Annotated

from fastapi import APIRouter, Depends, Form
from fastapi.responses import FileResponse

from src.api.deps import get_validated_upload
from src.schemas import FileItem, FileUpdate, Title, ValidatedUpload
from src.services.file_service import (
    create_file,
    delete_file,
    get_file,
    get_file_path,
    list_files,
    update_file,
)
from src.tasks import scan_file_for_threats

router = APIRouter(tags=["files"])


@router.get("/files", response_model=list[FileItem])
async def list_files_view():
    return await list_files()


@router.post("/files", response_model=FileItem, status_code=201)
async def create_file_view(
    title: Annotated[Title, Form()],
    upload: Annotated[ValidatedUpload, Depends(get_validated_upload)],
):
    file_item = await create_file(
        title=title,
        content=upload.content,
        filename=upload.filename,
        content_type=upload.content_type,
    )
    scan_file_for_threats.delay(file_item.id)
    return file_item


@router.get("/files/{file_id}", response_model=FileItem)
async def get_file_view(file_id: str):
    return await get_file(file_id)


@router.patch("/files/{file_id}", response_model=FileItem)
async def update_file_view(
    file_id: str,
    payload: FileUpdate,
):
    return await update_file(file_id=file_id, title=payload.title)


@router.get("/files/{file_id}/download")
async def download_file(file_id: str):
    file_item, stored_path = await get_file_path(file_id)
    return FileResponse(
        path=stored_path,
        media_type=file_item.mime_type,
        filename=file_item.original_name,
    )


@router.delete("/files/{file_id}", status_code=204)
async def delete_file_view(file_id: str):
    await delete_file(file_id)
