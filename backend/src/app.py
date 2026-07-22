from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette import status

from src.exceptions import EmptyFile, FileNotFound, FileTooLarge, StoredFileNotFound
from src.schemas import AlertItem, FileItem, FileUpdate
from src.services.alert_service import list_alerts
from src.services.file_service import create_file, delete_file, get_file, get_file_path, list_files, update_file
from src.tasks import scan_file_for_threats

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
    return JSONResponse(status_code=status.HTTP_413_CONTENT_TOO_LARGE, content={"detail": "File is too large"})


@app.get("/files", response_model=list[FileItem])
async def list_files_view():
    return await list_files()


@app.get("/alerts", response_model=list[AlertItem])
async def list_alerts_view():
    return await list_alerts()


@app.post("/files", response_model=FileItem, status_code=201)
async def create_file_view(
    title: str = Form(...),
    file: UploadFile = File(...),
):
    file_item = await create_file(title=title, upload_file=file)
    scan_file_for_threats.delay(file_item.id)
    return file_item


@app.get("/files/{file_id}", response_model=FileItem)
async def get_file_view(file_id: str):
    return await get_file(file_id)


@app.patch("/files/{file_id}", response_model=FileItem)
async def update_file_view(
    file_id: str,
    payload: FileUpdate,
):
    return await update_file(file_id=file_id, title=payload.title)


@app.get("/files/{file_id}/download")
async def download_file(file_id: str):
    file_item, stored_path = await get_file_path(file_id)
    return FileResponse(
        path=stored_path,
        media_type=file_item.mime_type,
        filename=file_item.original_name,
    )


@app.delete("/files/{file_id}", status_code=204)
async def delete_file_view(file_id: str):
    await delete_file(file_id)
