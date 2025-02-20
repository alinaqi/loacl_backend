"""
Tests for the file service.
"""

import io
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import UploadFile

from app.models.file import File, FileCreate, FileStatus
from app.repositories.file import FileRepository
from app.services.files import FileService


@pytest.fixture
def file_repository():
    """Create a mock file repository."""
    return AsyncMock(spec=FileRepository)


@pytest.fixture
def supabase_client():
    """Create a mock Supabase client."""
    mock_client = MagicMock()
    mock_client.storage.from_.return_value = mock_client
    mock_client.upload.return_value = None
    mock_client.download.return_value = io.BytesIO(b"test content")
    mock_client.remove.return_value = None
    return mock_client


@pytest.fixture
def file_service(file_repository, supabase_client):
    """Create a file service instance."""
    return FileService(file_repository=file_repository, supabase_client=supabase_client)


@pytest.fixture
def sample_file():
    """Create a sample file."""
    return File(
        id=uuid4(),
        filename="test.txt",
        content_type="text/plain",
        size=123,
        storage_path="test-path.txt",
        status=FileStatus.READY,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def upload_file():
    """Create a mock UploadFile."""
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "test.txt"
    mock_file.content_type = "text/plain"
    mock_file.read.return_value = b"test content"
    return mock_file


async def test_upload_file(file_service, file_repository, upload_file, supabase_client):
    """Test uploading a file."""
    # Setup
    thread_id = uuid4()
    message_id = uuid4()
    metadata = {"key": "value"}
    file_repository.create.return_value.data = [
        {
            "id": str(uuid4()),
            "filename": "test.txt",
            "content_type": "text/plain",
            "size": 11,
            "storage_path": "test-path.txt",
            "status": "ready",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
    ]

    # Execute
    result = await file_service.upload_file(
        file=upload_file,
        thread_id=thread_id,
        message_id=message_id,
        metadata=metadata,
    )

    # Verify
    assert isinstance(result, File)
    assert result.filename == "test.txt"
    assert result.content_type == "text/plain"
    assert result.size == 11
    assert result.status == FileStatus.READY
    supabase_client.storage.from_.assert_called_once_with("files")
    file_repository.create.assert_called_once()


async def test_download_file(
    file_service, file_repository, sample_file, supabase_client
):
    """Test downloading a file."""
    # Setup
    file_repository.get.return_value = sample_file.model_dump()

    # Execute
    result = await file_service.download_file(sample_file.id)

    # Verify
    assert isinstance(result, io.BytesIO)
    assert result.read() == b"test content"
    supabase_client.storage.from_.assert_called_once_with("files")
    file_repository.get.assert_called_once_with(sample_file.id)


async def test_delete_file(file_service, file_repository, sample_file, supabase_client):
    """Test deleting a file."""
    # Setup
    file_repository.get.return_value = sample_file.model_dump()

    # Execute
    result = await file_service.delete_file(sample_file.id)

    # Verify
    assert result is True
    supabase_client.storage.from_.assert_called_once_with("files")
    file_repository.get.assert_called_once_with(sample_file.id)
    file_repository.delete.assert_called_once_with(sample_file.id)


async def test_get_thread_files(file_service, file_repository, sample_file):
    """Test getting thread files."""
    # Setup
    thread_id = uuid4()
    file_repository.get_thread_files.return_value.data = [sample_file.model_dump()]

    # Execute
    result = await file_service.get_thread_files(thread_id)

    # Verify
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], File)
    assert result[0].id == sample_file.id
    file_repository.get_thread_files.assert_called_once_with(
        thread_id=thread_id,
        limit=100,
        offset=0,
    )


async def test_attach_to_thread(file_service, file_repository):
    """Test attaching a file to a thread."""
    # Setup
    file_id = uuid4()
    thread_id = uuid4()

    # Execute
    await file_service.attach_to_thread(file_id, thread_id)

    # Verify
    file_repository.attach_to_thread.assert_called_once_with(file_id, thread_id)


async def test_detach_from_thread(file_service, file_repository):
    """Test detaching a file from a thread."""
    # Setup
    file_id = uuid4()
    thread_id = uuid4()

    # Execute
    await file_service.detach_from_thread(file_id, thread_id)

    # Verify
    file_repository.detach_from_thread.assert_called_once_with(file_id, thread_id)
