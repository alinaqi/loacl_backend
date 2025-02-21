from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.api import deps
from app.schemas.user import User
from app.schemas.assistant_communication import (
    ThreadCreate,
    Thread,
    MessageCreate,
    Message,
    RunCreate,
    Run,
    ToolOutput
)
from app.services.assistant_communication import assistant_communication_service

router = APIRouter()

@router.post("/threads", response_model=Thread)
async def create_thread(
    thread_data: ThreadCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Thread:
    """Create a new thread"""
    messages = [msg.dict() for msg in thread_data.messages] if thread_data.messages else None
    thread = await assistant_communication_service.create_thread(messages=messages)
    return Thread(**thread)

@router.post("/threads/{thread_id}/messages", response_model=Message)
async def add_message(
    thread_id: str,
    message: MessageCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Message:
    """Add a message to a thread"""
    result = await assistant_communication_service.add_message(
        thread_id=thread_id,
        content=message.content,
        file_ids=message.file_ids
    )
    return Message(**result)

@router.get("/threads/{thread_id}/messages", response_model=List[Message])
async def list_messages(
    thread_id: str,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user)
) -> List[Message]:
    """List messages in a thread"""
    messages = await assistant_communication_service.get_messages(thread_id=thread_id, limit=limit)
    return [Message(**msg) for msg in messages]

@router.post("/threads/{thread_id}/runs", response_model=Run)
async def create_run(
    thread_id: str,
    run_data: RunCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Run:
    """Create a run for a thread"""
    run = await assistant_communication_service.run_assistant(
        thread_id=thread_id,
        assistant_id=run_data.assistant_id,
        instructions=run_data.instructions,
        tools=run_data.tools
    )
    return Run(**run)

@router.get("/threads/{thread_id}/runs/{run_id}", response_model=Run)
async def get_run_status(
    thread_id: str,
    run_id: str,
    current_user: User = Depends(deps.get_current_user)
) -> Run:
    """Get the status of a run"""
    run = await assistant_communication_service.get_run(thread_id=thread_id, run_id=run_id)
    return Run(**run)

@router.post("/threads/{thread_id}/runs/{run_id}/submit", response_model=Run)
async def submit_tool_outputs(
    thread_id: str,
    run_id: str,
    tool_outputs: List[ToolOutput],
    current_user: User = Depends(deps.get_current_user)
) -> Run:
    """Submit tool outputs for a run"""
    outputs = [output.dict() for output in tool_outputs]
    run = await assistant_communication_service.submit_tool_outputs(
        thread_id=thread_id,
        run_id=run_id,
        tool_outputs=outputs
    )
    return Run(**run)

@router.post("/threads/{thread_id}/runs/{run_id}/cancel", response_model=Run)
async def cancel_run(
    thread_id: str,
    run_id: str,
    current_user: User = Depends(deps.get_current_user)
) -> Run:
    """Cancel a run"""
    run = await assistant_communication_service.cancel_run(thread_id=thread_id, run_id=run_id)
    return Run(**run) 