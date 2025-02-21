from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api import deps
from app.schemas.assistant_communication import (
    Message,
    MessageCreate,
    Run,
    RunCreate,
    Thread,
    ThreadCreate,
    ToolOutput,
)
from app.schemas.user import User
from app.services.assistant import AssistantService
from app.services.assistant_communication import AssistantCommunicationService

router = APIRouter()


async def get_assistant_service(
    assistant_id: str, current_user: User
) -> AssistantCommunicationService:
    """Get AssistantCommunicationService instance for a specific assistant"""
    assistant_service = AssistantService()
    assistant = await assistant_service.get_assistant(assistant_id, current_user.id)
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
        )
    return AssistantCommunicationService.create_for_assistant(assistant)


@router.post("/threads", response_model=Thread)
async def create_thread(
    thread_data: ThreadCreate,
    assistant_id: str,
    current_user: User = Depends(deps.get_current_user),
) -> Thread:
    """Create a new thread"""
    try:
        # Get service with assistant-specific API key
        service = await get_assistant_service(assistant_id, current_user)

        # First create an empty thread
        thread = await service.create_thread()

        # If messages were provided, add them to the thread
        if thread_data.messages:
            for message in thread_data.messages:
                await service.add_message(
                    thread_id=thread["id"],
                    content=message.content,
                    file_ids=message.file_ids,
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
    """Add a message to a thread"""
    # Get service with assistant-specific API key
    service = await get_assistant_service(assistant_id, current_user)
    result = await service.add_message(
        thread_id=thread_id, content=message.content, file_ids=message.file_ids
    )
    return Message(**result)


@router.get("/threads/{thread_id}/messages", response_model=List[Message])
async def list_messages(
    thread_id: str,
    assistant_id: str,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> List[Message]:
    """List messages in a thread"""
    # Get service with assistant-specific API key
    service = await get_assistant_service(assistant_id, current_user)
    messages = await service.get_messages(thread_id=thread_id, limit=limit)
    return [Message(**msg) for msg in messages]


@router.post("/threads/{thread_id}/runs", response_model=Run)
async def create_run(
    thread_id: str,
    run_data: RunCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Run:
    """Create a run for a thread"""
    # Get service with assistant-specific API key
    service = await get_assistant_service(run_data.assistant_id, current_user)
    run = await service.run_assistant(
        thread_id=thread_id,
        assistant_id=run_data.assistant_id,
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
    """Get the status of a run"""
    # Get service with assistant-specific API key
    service = await get_assistant_service(assistant_id, current_user)
    run = await service.get_run(thread_id=thread_id, run_id=run_id)
    return Run(**run)


@router.post("/threads/{thread_id}/runs/{run_id}/submit", response_model=Run)
async def submit_tool_outputs(
    thread_id: str,
    run_id: str,
    tool_outputs: List[ToolOutput],
    assistant_id: str,
    current_user: User = Depends(deps.get_current_user),
) -> Run:
    """Submit tool outputs for a run"""
    # Get service with assistant-specific API key
    service = await get_assistant_service(assistant_id, current_user)
    outputs = [output.dict() for output in tool_outputs]
    run = await service.submit_tool_outputs(
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
    """Cancel a run"""
    # Get service with assistant-specific API key
    service = await get_assistant_service(assistant_id, current_user)
    run = await service.cancel_run(thread_id=thread_id, run_id=run_id)
    return Run(**run)
