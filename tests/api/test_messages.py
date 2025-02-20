"""
Test messages endpoints.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.models.response import ResponseMode
from app.models.thread import Message, MessageCreate

pytestmark = pytest.mark.asyncio


async def test_create_message_success(
    test_app: FastAPI,
    test_client: AsyncClient,
    mock_openai_service: AsyncMock,
    mock_conversation_service: AsyncMock,
) -> None:
    """Test successful message creation."""
    # Arrange
    thread_id = uuid.uuid4()
    message_id = uuid.uuid4()
    content = "Test message"

    mock_response = MagicMock()
    mock_response.id = str(message_id)
    mock_response.content = [MagicMock(text=MagicMock(value=content))]
    mock_response.metadata = {}

    mock_openai_service.create_message.return_value = mock_response
    mock_conversation_service.get_conversation_context.return_value = []

    # Act
    response = await test_client.post(
        f"/threads/{thread_id}/messages",
        json={
            "content": content,
            "response_config": {"mode": ResponseMode.NORMAL},
        },
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["thread_id"] == str(thread_id)
    assert data["message_id"] == str(message_id)
    assert data["content"] == content

    # Verify service calls
    mock_conversation_service.get_conversation_context.assert_called_once_with(
        thread_id
    )
    mock_openai_service.create_message.assert_called_once_with(
        thread_id=str(thread_id),
        content=content,
        file_ids=[],
        metadata={},
    )


async def test_create_message_not_found(
    test_app: FastAPI,
    test_client: AsyncClient,
    mock_openai_service: AsyncMock,
    mock_conversation_service: AsyncMock,
) -> None:
    """Test message creation with non-existent thread."""
    # Arrange
    thread_id = uuid.uuid4()
    mock_conversation_service.get_conversation_context.side_effect = ValueError(
        "Thread not found"
    )

    # Act
    response = await test_client.post(
        f"/threads/{thread_id}/messages",
        json={"content": "Test message"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Thread not found"


async def test_create_message_with_files(
    test_app: FastAPI,
    test_client: AsyncClient,
    mock_openai_service: AsyncMock,
    mock_conversation_service: AsyncMock,
) -> None:
    """Test message creation with file attachments."""
    # Arrange
    thread_id = uuid.uuid4()
    message_id = uuid.uuid4()
    content = "Test message with files"
    file_ids = ["file1", "file2"]

    mock_response = MagicMock()
    mock_response.id = str(message_id)
    mock_response.content = [MagicMock(text=MagicMock(value=content))]
    mock_response.metadata = {}

    mock_openai_service.create_message.return_value = mock_response
    mock_conversation_service.get_conversation_context.return_value = []

    # Act
    response = await test_client.post(
        f"/threads/{thread_id}/messages",
        json={
            "content": content,
            "file_ids": file_ids,
        },
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["thread_id"] == str(thread_id)
    assert data["message_id"] == str(message_id)
    assert data["content"] == content

    # Verify service calls with file IDs
    mock_openai_service.create_message.assert_called_once_with(
        thread_id=str(thread_id),
        content=content,
        file_ids=file_ids,
        metadata={},
    )
