"""
OpenAI service module.
"""
from functools import lru_cache
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI
from openai.types.beta import Assistant, Thread
from openai.types.beta.threads import Message, Run

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


@lru_cache()
def get_openai_client() -> AsyncOpenAI:
    """
    Get a cached OpenAI client instance.
    
    Returns:
        AsyncOpenAI: OpenAI client instance
    """
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class OpenAIService:
    """OpenAI service for managing assistants and threads."""
    
    def __init__(self) -> None:
        """Initialize the OpenAI service."""
        self.client = get_openai_client()
    
    async def create_assistant(
        self,
        name: str,
        instructions: str,
        model: str = "gpt-4-turbo-preview",
        tools: Optional[List[Dict[str, Any]]] = None,
        file_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Assistant:
        """
        Create a new assistant.
        
        Args:
            name: Name of the assistant
            instructions: Instructions for the assistant
            model: OpenAI model to use
            tools: List of tools for the assistant
            file_ids: List of file IDs to attach
            metadata: Additional metadata
        
        Returns:
            Assistant: Created assistant
        """
        try:
            return await self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                model=model,
                tools=tools or [],
                file_ids=file_ids or [],
                metadata=metadata or {},
            )
        except Exception as e:
            logger.error("Failed to create assistant", error=str(e))
            raise
    
    async def create_thread(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Thread:
        """
        Create a new thread.
        
        Args:
            messages: Initial messages for the thread
            metadata: Additional metadata
        
        Returns:
            Thread: Created thread
        """
        try:
            return await self.client.beta.threads.create(
                messages=messages or [],
                metadata=metadata or {},
            )
        except Exception as e:
            logger.error("Failed to create thread", error=str(e))
            raise
    
    async def create_message(
        self,
        thread_id: str,
        content: str,
        role: str = "user",
        file_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """
        Create a new message in a thread.
        
        Args:
            thread_id: Thread ID
            content: Message content
            role: Message role
            file_ids: List of file IDs to attach
            metadata: Additional metadata
        
        Returns:
            Message: Created message
        """
        try:
            return await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role=role,
                content=content,
                file_ids=file_ids or [],
                metadata=metadata or {},
            )
        except Exception as e:
            logger.error("Failed to create message", error=str(e))
            raise
    
    async def run_thread(
        self,
        thread_id: str,
        assistant_id: str,
        instructions: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Run:
        """
        Run an assistant on a thread.
        
        Args:
            thread_id: Thread ID
            assistant_id: Assistant ID
            instructions: Additional instructions for this run
            tools: Additional tools for this run
            metadata: Additional metadata
        
        Returns:
            Run: Created run
        """
        try:
            return await self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                instructions=instructions,
                tools=tools or [],
                metadata=metadata or {},
            )
        except Exception as e:
            logger.error("Failed to run thread", error=str(e))
            raise
    
    async def get_run(self, thread_id: str, run_id: str) -> Run:
        """
        Get a run's status.
        
        Args:
            thread_id: Thread ID
            run_id: Run ID
        
        Returns:
            Run: Run object
        """
        try:
            return await self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id,
            )
        except Exception as e:
            logger.error("Failed to get run", error=str(e))
            raise
    
    async def get_messages(
        self,
        thread_id: str,
        limit: int = 100,
        order: str = "desc",
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> List[Message]:
        """
        Get messages from a thread.
        
        Args:
            thread_id: Thread ID
            limit: Maximum number of messages to return
            order: Sort order
            after: Get messages after this ID
            before: Get messages before this ID
        
        Returns:
            List[Message]: List of messages
        """
        try:
            response = await self.client.beta.threads.messages.list(
                thread_id=thread_id,
                limit=limit,
                order=order,
                after=after,
                before=before,
            )
            return response.data
        except Exception as e:
            logger.error("Failed to get messages", error=str(e))
            raise 