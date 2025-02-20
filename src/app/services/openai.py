"""
OpenAI service module.
"""

import asyncio
from functools import lru_cache
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from fastapi import Depends
from openai import AsyncOpenAI
from openai.types.beta import Assistant, Thread
from openai.types.beta.threads import Run
from openai.types.beta.threads import ThreadMessage as Message

from app.core.config import Settings, get_settings
from app.core.logger import get_logger
from app.models.response import (
    NormalResponse,
    ResponseChunk,
    ResponseConfig,
    ResponseMode,
)

logger = get_logger(__name__)


@lru_cache()
def get_openai_client(settings: Settings = Depends(get_settings)) -> AsyncOpenAI:
    """
    Get a cached OpenAI client instance.

    Returns:
        AsyncOpenAI: OpenAI client instance
    """
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class OpenAIService:
    """OpenAI service for managing assistants and threads."""

    def __init__(self, settings: Settings = Depends(get_settings)):
        """
        Initialize the OpenAI service.

        Args:
            settings: Application settings
        """
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

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

    async def get_assistant(self, assistant_id: str) -> Optional[Assistant]:
        """
        Get assistant from OpenAI.

        Args:
            assistant_id: OpenAI assistant ID

        Returns:
            Optional[Assistant]: Assistant if found
        """
        try:
            return await self.client.beta.assistants.retrieve(assistant_id)
        except Exception as e:
            logger.error("Failed to get OpenAI assistant", error=str(e))
            return None

    async def process_response(
        self,
        thread_id: str,
        run_id: str,
        config: ResponseConfig,
    ) -> Union[AsyncGenerator[ResponseChunk, None], NormalResponse]:
        """
        Process the response from OpenAI based on the configuration mode.

        Args:
            thread_id: Thread ID
            run_id: Run ID
            config: Response configuration

        Returns:
            Union[AsyncGenerator[ResponseChunk, None], NormalResponse]: Response based on mode
        """
        try:
            # Wait for run to complete
            run = await self._wait_for_run_completion(thread_id, run_id)

            # Get messages after run completion
            messages = await self.get_messages(thread_id, limit=1)
            if not messages:
                raise ValueError("No messages found after run completion")

            message = messages[0]

            if config.mode == ResponseMode.STREAMING:
                return self._stream_response(message, config)
            else:
                return self._create_normal_response(message)

        except Exception as e:
            logger.error("Failed to process response", error=str(e))
            raise

    async def _wait_for_run_completion(self, thread_id: str, run_id: str) -> Run:
        """
        Wait for a run to complete.

        Args:
            thread_id: Thread ID
            run_id: Run ID

        Returns:
            Run: Completed run
        """
        while True:
            run = await self.get_run(thread_id, run_id)
            if run.status in ["completed", "failed"]:
                if run.status == "failed":
                    raise ValueError(f"Run failed: {run.last_error}")
                return run
            await asyncio.sleep(0.5)  # Poll every 500ms

    async def _stream_response(
        self,
        message: Message,
        config: ResponseConfig,
    ) -> AsyncGenerator[ResponseChunk, None]:
        """
        Stream a response in chunks.

        Args:
            message: OpenAI message
            config: Response configuration

        Yields:
            ResponseChunk: Response chunks
        """
        content = message.content[0].text.value
        chunk_size = config.chunk_size or 100
        chunks = [
            content[i : i + chunk_size] for i in range(0, len(content), chunk_size)
        ]

        for i, chunk in enumerate(chunks):
            is_last = i == len(chunks) - 1
            yield ResponseChunk(
                thread_id=message.thread_id,
                message_id=message.id,
                content=chunk,
                is_complete=is_last,
                metadata={
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            )

    def _create_normal_response(self, message: Message) -> NormalResponse:
        """
        Create a normal (non-streaming) response.

        Args:
            message: OpenAI message

        Returns:
            NormalResponse: Complete response
        """
        return NormalResponse(
            thread_id=message.thread_id,
            message_id=message.id,
            content=message.content[0].text.value,
            metadata={
                "role": message.role,
                "created_at": message.created_at,
            },
        )
