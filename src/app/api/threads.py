"""
Thread endpoints module.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.suggestions import SuggestionsResponse
from app.models.thread import Thread, ThreadCreate
from app.services.suggestions import SuggestionsService
from app.services.thread import ThreadService

router = APIRouter(prefix="/threads", tags=["threads"])


@router.post("", response_model=Thread)
async def create_thread(
    data: ThreadCreate,
    thread_service: ThreadService = Depends(),
) -> Thread:
    """
    Create a new thread.

    Args:
        data: Thread creation data
        thread_service: Injected thread service

    Returns:
        Thread: Created thread
    """
    return await thread_service.create_thread(data)


@router.get("/{thread_id}", response_model=Thread)
async def get_thread(
    thread_id: UUID,
    thread_service: ThreadService = Depends(),
) -> Thread:
    """
    Get a thread by ID.

    Args:
        thread_id: Thread ID
        thread_service: Injected thread service

    Returns:
        Thread: Found thread

    Raises:
        HTTPException: If thread not found
    """
    thread = await thread_service.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@router.delete("/{thread_id}")
async def delete_thread(
    thread_id: UUID,
    thread_service: ThreadService = Depends(),
) -> None:
    """
    Delete a thread.

    Args:
        thread_id: Thread ID
        thread_service: Injected thread service
    """
    await thread_service.delete_thread(thread_id)


@router.get("/guest/sessions/{session_id}/threads", response_model=List[Thread])
async def get_guest_threads(
    session_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    thread_service: ThreadService = Depends(),
) -> List[Thread]:
    """
    Get threads for a guest session.

    Args:
        session_id: Guest session ID
        limit: Maximum number of threads to return
        offset: Number of threads to skip
        thread_service: Injected thread service

    Returns:
        List[Thread]: List of threads
    """
    return await thread_service.get_guest_threads(
        session_id=session_id,
        limit=limit,
        offset=offset,
    )


@router.post("/{thread_id}/suggest", response_model=SuggestionsResponse)
async def get_suggestions(
    thread_id: UUID,
    message_id: Optional[UUID] = None,
    suggestions_service: SuggestionsService = Depends(),
) -> SuggestionsResponse:
    """
    Get follow-up suggestions based on conversation.

    Args:
        thread_id: Thread ID
        message_id: Optional message ID to generate suggestions for
        suggestions_service: Injected suggestions service

    Returns:
        SuggestionsResponse: List of follow-up suggestions
    """
    try:
        suggestions = await suggestions_service.generate_suggestions(
            thread_id=thread_id,
            message_id=message_id,
        )
        return SuggestionsResponse(suggestions=suggestions)
    except Exception as e:
        logger.error("Failed to get suggestions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
