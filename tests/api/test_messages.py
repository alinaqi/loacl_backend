"""
Test messages endpoints.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.models.response import ResponseMode
from app.models.thread import Message, MessageCreate, MessageStatus

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


async def test_list_messages_success(
    test_app: FastAPI,
    test_client: AsyncClient,
    mock_conversation_service: AsyncMock,
) -> None:
    """Test successful message listing."""
    # Arrange
    thread_id = uuid.uuid4()
    message_id = uuid.uuid4()
    content = "Test message"

    mock_message = Message(
        id=message_id,
        thread_id=thread_id,
        content=content,
        role="assistant",
        status=MessageStatus.COMPLETED,
        created_at="2024-01-01T00:00:00Z",
        metadata={},
    )

    mock_conversation_service.get_thread_messages.return_value = [mock_message]

    # Act
    response = await test_client.get(
        f"/threads/{thread_id}/messages",
        params={"limit": 50, "offset": 0},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == str(thread_id)
    assert len(data["messages"]) == 1
    assert data["total"] == 1
    assert not data["has_more"]

    # Verify service call
    mock_conversation_service.get_thread_messages.assert_called_once_with(
        thread_id=thread_id,
        limit=51,  # limit + 1 to check for more
        offset=0,
        ascending=False,
        status=None,
    )


async def test_list_messages_with_filters(
    test_app: FastAPI,
    test_client: AsyncClient,
    mock_conversation_service: AsyncMock,
) -> None:
    """Test message listing with filters."""
    # Arrange
    thread_id = uuid.uuid4()
    mock_conversation_service.get_thread_messages.return_value = []

    # Act
    response = await test_client.get(
        f"/threads/{thread_id}/messages",
        params={
            "limit": 20,
            "offset": 10,
            "ascending": True,
            "status": MessageStatus.COMPLETED,
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == str(thread_id)
    assert len(data["messages"]) == 0
    assert data["total"] == 0
    assert not data["has_more"]

    # Verify service call with filters
    mock_conversation_service.get_thread_messages.assert_called_once_with(
        thread_id=thread_id,
        limit=21,  # limit + 1
        offset=10,
        ascending=True,
        status=MessageStatus.COMPLETED,
    )


async def test_list_messages_not_found(
    test_app: FastAPI,
    test_client: AsyncClient,
    mock_conversation_service: AsyncMock,
) -> None:
    """Test message listing with non-existent thread."""
    # Arrange
    thread_id = uuid.uuid4()
    mock_conversation_service.get_thread_messages.side_effect = ValueError(
        "Thread not found"
    )

    # Act
    response = await test_client.get(f"/threads/{thread_id}/messages")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Thread not found"


async def test_list_messages_pagination(
    test_app: FastAPI,
    test_client: AsyncClient,
    mock_conversation_service: AsyncMock,
) -> None:
    """Test message listing pagination."""
    # Arrange
    thread_id = uuid.uuid4()
    messages = [
        Message(
            id=uuid.uuid4(),
            thread_id=thread_id,
            content=f"Message {i}",
            role="assistant",
            status=MessageStatus.COMPLETED,
            created_at="2024-01-01T00:00:00Z",
            metadata={},
        )
        for i in range(51)  # Create 51 messages to test has_more
    ]

    mock_conversation_service.get_thread_messages.return_value = messages

    # Act
    response = await test_client.get(
        f"/threads/{thread_id}/messages",
        params={"limit": 50, "offset": 0},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == str(thread_id)
    assert len(data["messages"]) == 50  # Should only return 50 messages
    assert data["total"] == 50
    assert data["has_more"]  # Should be true since we have 51 messages
