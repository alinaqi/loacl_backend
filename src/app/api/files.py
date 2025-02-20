"""
File routes module.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.models.file import FileResponse
from app.services.files import FileService

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    thread_id: UUID = None,
    message_id: UUID = None,
    file_service: FileService = Depends(),
) -> FileResponse:
    """
    Upload a file.

    Args:
        file: File to upload
        thread_id: Optional thread ID to associate with
        message_id: Optional message ID to associate with
        file_service: Injected file service

    Returns:
        FileResponse: Uploaded file details

    Raises:
        HTTPException: If file upload fails
    """
    try:
        uploaded_file = await file_service.upload_file(
            file=file,
            thread_id=thread_id,
            message_id=message_id,
        )
        return FileResponse(**uploaded_file.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
        )


@router.get("/{file_id}", response_model=FileResponse)
async def get_file_metadata(
    file_id: UUID,
    file_service: FileService = Depends(),
) -> FileResponse:
    """
    Get file metadata.

    Args:
        file_id: File ID
        file_service: Injected file service

    Returns:
        FileResponse: File metadata

    Raises:
        HTTPException: If file not found
    """
    try:
        file_data = await file_service.file_repository.get(file_id)
        if not file_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )
        return FileResponse(**file_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file metadata: {str(e)}",
        )


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: UUID,
    file_service: FileService = Depends(),
) -> StreamingResponse:
    """
    Get file content.

    Args:
        file_id: File ID
        file_service: Injected file service

    Returns:
        StreamingResponse: File content stream

    Raises:
        HTTPException: If file not found or download fails
    """
    try:
        # Get file metadata first
        file_data = await file_service.file_repository.get(file_id)
        if not file_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        # Download file content
        content = await file_service.download_file(file_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File content not found",
            )

        return StreamingResponse(
            content,
            media_type=file_data["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{file_data["filename"]}"'
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file content: {str(e)}",
        )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    file_service: FileService = Depends(),
) -> None:
    """
    Delete a file.

    Args:
        file_id: File ID
        file_service: Injected file service

    Raises:
        HTTPException: If file not found or deletion fails
    """
    try:
        deleted = await file_service.delete_file(file_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}",
        )
