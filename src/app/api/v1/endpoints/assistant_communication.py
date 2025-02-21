"""Assistant communication endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.api import deps
from app.schemas.assistant_communication import (
    Message,
    MessageCreate,
    Run,
    RunCreate,
    Thread,
    ThreadCreate,
    ToolOutput,
    ChatSession,
    ChatMessage,
)
from app.schemas.user import User
from app.services.assistant import AssistantService
from app.services.assistant_communication import AssistantCommunicationService

router = APIRouter()


async def get_assistant_service(
    assistant_id: str, current_user: User
) -> AssistantCommunicationService:
    """Get AssistantCommunicationService instance for a specific assistant.

    Args:
        assistant_id: Assistant ID (UUID)
        current_user: Current user

    Returns:
        AssistantCommunicationService instance

    Raises:
        HTTPException: If assistant is not found
    """
    try:
        assistant_service = AssistantService()
        # Convert string ID to UUID
        assistant = await assistant_service.get_assistant(
            UUID(assistant_id), UUID(str(current_user.id))
        )

        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assistant {assistant_id} not found",
            )

        if not assistant.get("assistant_id"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OpenAI Assistant ID not found for assistant {assistant_id}",
            )

        return await AssistantCommunicationService.create_for_assistant(
            assistant_id=assistant_id,
            user_id=current_user.id,
            api_key=assistant.get("api_key"),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid assistant ID format: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/threads", response_model=Thread)
async def create_thread(
    thread_data: ThreadCreate,
    assistant_id: str,
    current_user: User = Depends(deps.get_current_user),
) -> Thread:
    """Create a new thread.

    Args:
        thread_data: Thread creation data
        assistant_id: Assistant ID
        current_user: Current user

    Returns:
        Created thread

    Raises:
        HTTPException: If thread creation fails
    """
    try:
        # Get service with assistant-specific API key
        service = await get_assistant_service(assistant_id, current_user)

        # Create thread with messages
        thread = service.create_thread(
            messages=[
                {"role": "user", "content": msg.content, "file_ids": msg.file_ids or []}
                for msg in (thread_data.messages or [])
            ]
        )
        return Thread(**thread)
    except Exception as e:
        print(f"Error creating thread: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/threads/{thread_id}/messages", response_model=Message)
async def add_message(
    thread_id: str,
    message: MessageCreate,
    assistant_id: str,
    current_user: User = Depends(deps.get_current_user),
) -> Message:
    """Add a message to a thread.

    Args:
        thread_id: Thread ID
        message: Message to add
        assistant_id: Assistant ID
        current_user: Current user

    Returns:
        Created message
    """
    # Get service with assistant-specific API key
    service = await get_assistant_service(assistant_id, current_user)
    result = service.add_message_to_thread(
        thread_id=thread_id,
        content=message.content,
        file_ids=message.file_ids,
        assistant_id=assistant_id,
        fingerprint=str(current_user.id)  # Use user ID as fingerprint for authenticated users
    )
    return Message(**result)


@router.get("/threads/{thread_id}/messages", response_model=List[Message])
async def list_messages(
    thread_id: str,
    assistant_id: str,
    current_user: User = Depends(deps.get_current_user),
) -> List[Message]:
    """List messages in a thread.

    Args:
        thread_id: Thread ID
        assistant_id: Assistant ID
        current_user: Current user

    Returns:
        List of messages
    """
    # Get service with assistant-specific API key
    service = await get_assistant_service(assistant_id, current_user)
    messages = service.get_messages(thread_id=thread_id)
    return [Message(**msg) for msg in messages]


@router.post("/threads/{thread_id}/runs", response_model=Run)
async def create_run(
    thread_id: str,
    run_data: RunCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Run:
    """Create a run for a thread.

    Args:
        thread_id: Thread ID
        run_data: Run creation data
        current_user: Current user

    Returns:
        Created run
    """
    # Get service with assistant-specific API key
    service = await get_assistant_service(run_data.assistant_id, current_user)
    run = service.run_assistant(
        thread_id=thread_id,
        instructions=run_data.instructions,
        tools=run_data.tools,
    )
    return Run(**run)


@router.get("/threads/{thread_id}/runs/{run_id}", response_model=Run)
async def get_run_status(
    thread_id: str,
    run_id: str,
    assistant_id: str,
    current_user: User = Depends(deps.get_current_user),
) -> Run:
    """Get the status of a run.

    Args:
        thread_id: Thread ID
        run_id: Run ID
        assistant_id: Assistant ID
        current_user: Current user

    Returns:
        Run status
    """
    # Get service with assistant-specific API key
    service = await get_assistant_service(assistant_id, current_user)
    run = service.get_run(thread_id=thread_id, run_id=run_id)
    return Run(**run)


@router.post("/threads/{thread_id}/runs/{run_id}/submit", response_model=Run)
async def submit_tool_outputs(
    thread_id: str,
    run_id: str,
    tool_outputs: List[ToolOutput],
    assistant_id: str,
    current_user: User = Depends(deps.get_current_user),
) -> Run:
    """Submit tool outputs for a run.

    Args:
        thread_id: Thread ID
        run_id: Run ID
        tool_outputs: Tool outputs to submit
        assistant_id: Assistant ID
        current_user: Current user

    Returns:
        Updated run
    """
    # Get service with assistant-specific API key
    service = await get_assistant_service(assistant_id, current_user)
    outputs = [output.dict() for output in tool_outputs]
    run = service.submit_tool_outputs(
        thread_id=thread_id, run_id=run_id, tool_outputs=outputs
    )
    return Run(**run)


@router.post("/threads/{thread_id}/runs/{run_id}/cancel", response_model=Run)
async def cancel_run(
    thread_id: str,
    run_id: str,
    assistant_id: str,
    current_user: User = Depends(deps.get_current_user),
) -> Run:
    """Cancel a run.

    Args:
        thread_id: Thread ID
        run_id: Run ID
        assistant_id: Assistant ID
        current_user: Current user

    Returns:
        Cancelled run
    """
    # Get service with assistant-specific API key
    service = await get_assistant_service(assistant_id, current_user)
    run = service.cancel_run(thread_id=thread_id, run_id=run_id)
    return Run(**run)


@router.get("/chat-sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_session_messages(
    session_id: str,
    assistant_id: str,
    current_user: User = Depends(deps.get_current_user),
    limit: int = Query(50, gt=0, le=100),
    offset: int = Query(0, ge=0),
) -> List[ChatMessage]:
    """Get messages from a specific chat session.

    Args:
        session_id: Chat session ID
        assistant_id: Assistant ID
        current_user: Current user
        limit: Maximum number of messages to return
        offset: Number of messages to skip

    Returns:
        List of chat messages
    """
    # Get service with assistant-specific API key
    service = await get_assistant_service(assistant_id, current_user)
    return service.get_session_messages(
        session_id=session_id,
        fingerprint=str(current_user.id),
        limit=limit,
        offset=offset
    )


@router.get("/chat-sessions/messages", response_model=List[ChatMessage])
async def get_messages_from_sessions(
    assistant_id: str,
    current_user: User = Depends(deps.get_current_user),
    session_ids: List[str] = Query(None),
    limit: int = Query(50, gt=0, le=100),
    offset: int = Query(0, ge=0),
) -> List[ChatMessage]:
    """Get messages from multiple chat sessions.

    Args:
        assistant_id: Assistant ID
        current_user: Current user
        session_ids: Optional list of session IDs to filter by
        limit: Maximum number of messages to return
        offset: Number of messages to skip

    Returns:
        List of chat messages
    """
    # Get service with assistant-specific API key
    service = await get_assistant_service(assistant_id, current_user)
    return service.get_messages_from_sessions(
        fingerprint=str(current_user.id),
        session_ids=session_ids,
        limit=limit,
        offset=offset
    )


@router.delete("/chat-sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: str,
    assistant_id: str,
    current_user: User = Depends(deps.get_current_user),
) -> None:
    """Delete a chat session and all its messages.

    Args:
        session_id: Chat session ID
        assistant_id: Assistant ID
        current_user: Current user

    Raises:
        HTTPException: If session not found or deletion fails
    """
    # Get service with assistant-specific API key
    service = await get_assistant_service(assistant_id, current_user)
    try:
        await service.delete_chat_session(
            session_id=session_id,
            fingerprint=str(current_user.id)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
