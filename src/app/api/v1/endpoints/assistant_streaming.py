"""Streaming endpoints for assistant communication."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from app.api import deps
from app.schemas.assistant_communication import MessageCreate, RunCreate, ToolOutput
from app.schemas.user import User
from app.services.assistant_streaming import AssistantStreamingService

router = APIRouter()


async def get_streaming_service(
    assistant_id: str, current_user: User
) -> AssistantStreamingService:
    """Get AssistantStreamingService instance.

    Args:
        assistant_id: Assistant ID
        current_user: Current user

    Returns:
        AssistantStreamingService instance
    """
    try:
        return await AssistantStreamingService.create_for_assistant(
            assistant_id=assistant_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/threads/stream")
async def create_thread_and_run_stream(
    messages: List[MessageCreate],
    assistant_id: str,
    instructions: Optional[str] = None,
    tools: Optional[List[dict]] = None,
    current_user: User = Depends(deps.get_current_user),
) -> EventSourceResponse:
    """Create a thread and run with streaming.

    Args:
        messages: Initial messages
        assistant_id: Assistant ID
        instructions: Optional override instructions
        tools: Optional tools to use
        current_user: Current user

    Returns:
        Streaming response
    """
    service = await get_streaming_service(assistant_id, current_user)

    # Convert messages to the expected format
    formatted_messages = []
    for msg in messages:
        formatted_msg = {
            "role": msg.role,  # Use the role from the message
            "content": msg.content,
        }
        if msg.file_ids:
            formatted_msg["file_ids"] = msg.file_ids
        formatted_messages.append(formatted_msg)

    return EventSourceResponse(
        service.stream_create_thread_and_run(
            messages=formatted_messages,
            assistant_id=assistant_id,  # Pass assistant_id
            fingerprint=str(current_user.id),  # Use user ID as fingerprint
            instructions=instructions,
            tools=tools,
        )
    )


@router.post("/threads/{thread_id}/runs/stream")
async def create_run_stream(
    thread_id: str,
    run_data: RunCreate,
    current_user: User = Depends(deps.get_current_user),
) -> EventSourceResponse:
    """Create a run with streaming.

    Args:
        thread_id: Thread ID
        run_data: Run creation data
        current_user: Current user

    Returns:
        Streaming response
    """
    service = await get_streaming_service(run_data.assistant_id, current_user)
    return EventSourceResponse(
        service.stream_run(
            thread_id=thread_id,
            assistant_id=run_data.assistant_id,  # Pass assistant_id
            fingerprint=str(current_user.id),  # Use user ID as fingerprint
            instructions=run_data.instructions,
            tools=run_data.tools,
        )
    )


@router.post("/threads/{thread_id}/runs/{run_id}/submit/stream")
async def submit_tool_outputs_stream(
    thread_id: str,
    run_id: str,
    tool_outputs: List[ToolOutput],
    assistant_id: str,
    current_user: User = Depends(deps.get_current_user),
) -> EventSourceResponse:
    """Submit tool outputs with streaming.

    Args:
        thread_id: Thread ID
        run_id: Run ID
        tool_outputs: Tool outputs to submit
        assistant_id: Assistant ID
        current_user: Current user

    Returns:
        Streaming response
    """
    service = await get_streaming_service(assistant_id, current_user)
    return EventSourceResponse(
        service.stream_submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=[output.model_dump() for output in tool_outputs],
        )
    )
