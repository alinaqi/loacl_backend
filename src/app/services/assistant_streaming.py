"""Service for handling streaming communication with OpenAI assistants."""

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, Optional

from openai import OpenAI
from sse_starlette.sse import ServerSentEvent

from app.core.logger import logger
from app.services.assistant import AssistantService


class AssistantStreamingService:
    """Service for handling streaming communication with OpenAI assistants."""

    def __init__(
        self, api_key: str, openai_assistant_id: str, client: Optional[OpenAI] = None
    ) -> None:
        """Initialize the streaming service.

        Args:
            api_key: OpenAI API key
            openai_assistant_id: OpenAI assistant ID
            client: Optional pre-configured OpenAI client
        """
        self.api_key = api_key
        self.openai_assistant_id = openai_assistant_id
        self.client = client or OpenAI(api_key=api_key)

    @classmethod
    async def create_for_assistant(
        cls, assistant_id: str, user_id: int, api_key: Optional[str] = None
    ) -> "AssistantStreamingService":
        """Create a service instance for a specific assistant.

        Args:
            assistant_id: Local assistant ID
            user_id: User ID
            api_key: Optional OpenAI API key

        Returns:
            AssistantStreamingService instance
        """
        logger.debug(f"Creating streaming service for assistant {assistant_id}")
        assistant_service = AssistantService()
        assistant = await assistant_service.get_assistant(assistant_id, str(user_id))

        if not assistant:
            raise ValueError(f"Assistant {assistant_id} not found")

        if not assistant.get("assistant_id"):
            raise ValueError(
                f"OpenAI Assistant ID not found for assistant {assistant_id}"
            )

        return cls(
            api_key=api_key or assistant.get("api_key"),
            openai_assistant_id=assistant["assistant_id"],
        )

    async def stream_create_thread_and_run(
        self,
        messages: list,
        instructions: Optional[str] = None,
        tools: Optional[list] = None,
    ) -> AsyncGenerator[ServerSentEvent, None]:
        """Create a thread and run with streaming.

        Args:
            messages: Initial messages
            instructions: Optional override instructions
            tools: Optional tools to use

        Yields:
            Server-sent events for the thread creation and run
        """
        try:
            # Format messages for OpenAI
            formatted_messages = []
            for msg in messages:
                # Ensure required fields are present
                if "role" not in msg or "content" not in msg:
                    raise ValueError(
                        "Each message must have 'role' and 'content' fields"
                    )

                formatted_msg = {
                    "role": msg["role"],  # Required field
                    "content": msg["content"],  # Required field
                }
                # Optional field
                if "file_ids" in msg:
                    formatted_msg["file_ids"] = msg["file_ids"]
                formatted_messages.append(formatted_msg)

            if not formatted_messages:
                raise ValueError("At least one message is required")

            # Create thread
            thread = self.client.beta.threads.create(messages=formatted_messages)
            yield self._create_sse_event("thread.created", thread.model_dump())

            # Create and stream run
            async for event in self.stream_run(
                thread.id, instructions=instructions, tools=tools
            ):
                yield event

        except Exception as e:
            logger.error(f"Error in stream_create_thread_and_run: {str(e)}")
            yield self._create_sse_event("error", {"error": str(e)})

    async def stream_run(
        self,
        thread_id: str,
        instructions: Optional[str] = None,
        tools: Optional[list] = None,
    ) -> AsyncGenerator[ServerSentEvent, None]:
        """Stream a run.

        Args:
            thread_id: Thread ID
            instructions: Optional override instructions
            tools: Optional tools to use

        Yields:
            Server-sent events for the run
        """
        try:
            if not thread_id:
                raise ValueError("thread_id is required")

            if not self.openai_assistant_id:
                raise ValueError("OpenAI Assistant ID is required")

            # Check for active runs
            runs = self.client.beta.threads.runs.list(thread_id=thread_id)
            active_run = next(
                (run for run in runs.data if run.status in ["queued", "in_progress"]),
                None,
            )

            if active_run:
                # Wait for the active run to complete
                while active_run.status in ["queued", "in_progress"]:
                    yield self._create_sse_event(
                        f"thread.run.{active_run.status}", active_run.model_dump()
                    )
                    await asyncio.sleep(
                        1
                    )  # Add small delay to prevent too frequent polling
                    active_run = self.client.beta.threads.runs.retrieve(
                        thread_id=thread_id, run_id=active_run.id
                    )

            # Create new run with streaming enabled
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.openai_assistant_id,
                instructions=instructions,
                tools=tools or [],
                stream=True,  # Enable streaming
            )
            yield self._create_sse_event("thread.run.created", run.model_dump())

            # Stream run status
            while True:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id, run_id=run.id
                )

                # Emit run status events
                yield self._create_sse_event(
                    f"thread.run.{run_status.status}", run_status.model_dump()
                )

                if run_status.status in ["completed", "failed", "cancelled", "expired"]:
                    break

                # Get and stream messages
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread_id, order="desc", limit=1
                )

                for message in messages.data:
                    # Stream message content
                    yield self._create_sse_event(
                        "thread.message.created", message.model_dump()
                    )

                    if message.content:
                        for content_part in message.content:
                            yield self._create_sse_event(
                                "thread.message.delta",
                                {
                                    "id": message.id,
                                    "object": "thread.message.delta",
                                    "delta": {"content": [content_part.model_dump()]},
                                },
                            )

                    yield self._create_sse_event(
                        "thread.message.completed", message.model_dump()
                    )

                await asyncio.sleep(
                    1
                )  # Add small delay to prevent too frequent polling

        except Exception as e:
            logger.error(f"Error in stream_run: {str(e)}")
            yield self._create_sse_event("error", {"error": str(e)})

    async def stream_submit_tool_outputs(
        self,
        thread_id: str,
        run_id: str,
        tool_outputs: list,
    ) -> AsyncGenerator[ServerSentEvent, None]:
        """Submit tool outputs with streaming.

        Args:
            thread_id: Thread ID
            run_id: Run ID
            tool_outputs: Tool outputs to submit

        Yields:
            Server-sent events for the tool output submission
        """
        try:
            # Submit tool outputs
            run = self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs,
                stream=True,
            )
            yield self._create_sse_event("thread.run.created", run.model_dump())

            # Stream run status and messages
            async for event in self.stream_run(thread_id, run_id=run_id):
                yield event

        except Exception as e:
            logger.error(f"Error in stream_submit_tool_outputs: {str(e)}")
            yield self._create_sse_event("error", {"error": str(e)})

    def _create_sse_event(self, event_type: str, data: Any) -> ServerSentEvent:
        """Create a server-sent event.

        Args:
            event_type: Event type
            data: Event data

        Returns:
            Server-sent event
        """
        return ServerSentEvent(
            data=json.dumps(data),  # Ensure proper JSON serialization
            event=event_type,
            retry=None,
        )
