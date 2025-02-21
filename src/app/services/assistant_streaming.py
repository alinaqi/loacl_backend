"""Service for handling streaming communication with OpenAI assistants."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Dict, Optional

import jwt
from openai import OpenAI
from sse_starlette.sse import ServerSentEvent
from supabase.lib.client_options import ClientOptions

from app.core.config import get_settings
from app.core.logger import logger
from app.services.assistant import AssistantService
from supabase import create_client


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
        
        # Initialize Supabase with service role
        settings = get_settings()
        
        # Create service role JWT
        service_role_jwt = jwt.encode(
            {
                "role": "service_role",
                "iss": "supabase",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(days=1),
            },
            settings.SUPABASE_JWT_SECRET,
            algorithm="HS256",
        )

        # Use service role key with proper JWT
        options = ClientOptions(
            headers={
                "apiKey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {service_role_jwt}",
            }
        )
        
        self.supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
            options=options
        )

    def _get_or_create_chat_session(
        self,
        thread_id: str,
        assistant_id: str,
        fingerprint: str = "default"
    ) -> Dict[str, Any]:
        """Get or create a chat session for the thread.

        Args:
            thread_id: OpenAI thread ID
            assistant_id: Assistant ID
            fingerprint: User fingerprint

        Returns:
            Chat session data
        """
        # Try to find existing session
        result = (
            self.supabase.table("lacl_chat_sessions")
            .select("*")
            .eq("metadata->>thread_id", thread_id)
            .execute()
        )
        
        if result.data:
            return result.data[0]
            
        # Create new session
        session_data = {
            "assistant_id": assistant_id,
            "fingerprint": fingerprint,
            "metadata": {"thread_id": thread_id}
        }
        
        result = self.supabase.table("lacl_chat_sessions").insert(session_data).execute()
        return result.data[0]

    def _save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tokens_used: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Save a message to the database.

        Args:
            session_id: Chat session ID
            role: Message role (user/assistant)
            content: Message content
            tokens_used: Number of tokens used
            metadata: Optional metadata

        Returns:
            Saved message data
        """
        message_data = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "tokens_used": tokens_used,
            "metadata": metadata or {}
        }
        
        result = self.supabase.table("lacl_chat_messages").insert(message_data).execute()
        return result.data[0]

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
        assistant_id: str = None,
        fingerprint: str = "default",
        instructions: Optional[str] = None,
        tools: Optional[list] = None,
    ) -> AsyncGenerator[ServerSentEvent, None]:
        """Create a thread and run with streaming.

        Args:
            messages: Initial messages
            assistant_id: Assistant ID for database
            fingerprint: User fingerprint for database
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
            thread_data = thread.model_dump()
            yield self._create_sse_event("thread.created", thread_data)

            # Save to database if assistant_id is provided
            if assistant_id:
                session = self._get_or_create_chat_session(
                    thread_id=thread_data["id"],
                    assistant_id=assistant_id,
                    fingerprint=fingerprint
                )
                # Save initial messages
                for msg in formatted_messages:
                    self._save_message(
                        session_id=session["id"],
                        role=msg["role"],
                        content=msg["content"],
                        metadata={"message_id": msg.get("id")}
                    )

            # Create and stream run
            async for event in self.stream_run(
                thread.id,
                assistant_id=assistant_id,
                fingerprint=fingerprint,
                instructions=instructions,
                tools=tools
            ):
                yield event

        except Exception as e:
            logger.error(f"Error in stream_create_thread_and_run: {str(e)}")
            yield self._create_sse_event("error", {"error": str(e)})

    async def stream_run(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None,
        fingerprint: str = "default",
        instructions: Optional[str] = None,
        tools: Optional[list] = None,
    ) -> AsyncGenerator[ServerSentEvent, None]:
        """Stream a run.

        Args:
            thread_id: Thread ID
            assistant_id: Assistant ID for database
            fingerprint: User fingerprint for database
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

            # Get or create session if assistant_id is provided
            session = None
            if assistant_id:
                session = self._get_or_create_chat_session(
                    thread_id=thread_id,
                    assistant_id=assistant_id,
                    fingerprint=fingerprint
                )

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
                    await asyncio.sleep(1)
                    active_run = self.client.beta.threads.runs.retrieve(
                        thread_id=thread_id, run_id=active_run.id
                    )

            # Create new run with streaming enabled
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.openai_assistant_id,
                instructions=instructions,
                tools=tools or [],
                stream=True,
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
                    message_data = message.model_dump()
                    # Stream message content
                    yield self._create_sse_event(
                        "thread.message.created", message_data
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

                            # Save message to database if we have session
                            if session and content_part.get("type") == "text":
                                self._save_message(
                                    session_id=session["id"],
                                    role=message_data["role"],
                                    content=content_part["text"]["value"],
                                    metadata={"message_id": message_data["id"]}
                                )

                    yield self._create_sse_event(
                        "thread.message.completed", message_data
                    )

                await asyncio.sleep(1)

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

    async def delete_chat_session(
        self,
        session_id: str,
        fingerprint: str,
    ) -> bool:
        """Delete a chat session and all its messages.

        Args:
            session_id: Chat session ID
            fingerprint: User fingerprint

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If session not found or doesn't belong to user
        """
        # Verify session belongs to user
        session = (
            self.supabase.table("lacl_chat_sessions")
            .select("*")
            .eq("id", session_id)
            .eq("fingerprint", fingerprint)
            .execute()
        )
        
        if not session.data:
            raise ValueError(f"Chat session {session_id} not found")
            
        try:
            # Delete usage metrics first
            self.supabase.table("lacl_usage_metrics").delete().eq("session_id", session_id).execute()
            
            # Delete all messages
            self.supabase.table("lacl_chat_messages").delete().eq("session_id", session_id).execute()
            
            # Then delete the session
            self.supabase.table("lacl_chat_sessions").delete().eq("id", session_id).execute()
            
            # Delete the OpenAI thread if it exists
            if session.data[0].get("metadata", {}).get("thread_id"):
                thread_id = session.data[0]["metadata"]["thread_id"]
                try:
                    self.client.beta.threads.delete(thread_id=thread_id)
                except Exception as e:
                    logger.error(f"Error deleting OpenAI thread {thread_id}: {str(e)}")
                    # Continue even if OpenAI thread deletion fails
                    pass
            
            return True
        except Exception as e:
            logger.error(f"Error deleting chat session {session_id}: {str(e)}")
            raise
