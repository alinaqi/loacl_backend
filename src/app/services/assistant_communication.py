"""Service for handling assistant communication with OpenAI API.

This module provides functionality for managing assistant communication,
including thread and message management, run execution, and response handling.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timedelta

import jwt
from openai import OpenAI
from supabase.lib.client_options import ClientOptions

from app.core.config import get_settings
from app.core.logger import logger
from app.services.assistant import AssistantService
from supabase import create_client


class AssistantCommunicationService:
    """Service for managing communication with OpenAI assistants."""

    def __init__(
        self,
        api_key: str,
        openai_assistant_id: str,
        client: Optional[OpenAI] = None
    ) -> None:
        """Initialize the assistant communication service.

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

    @classmethod
    async def create_for_assistant(
        cls, assistant_id: str, user_id: int, api_key: Optional[str] = None
    ) -> "AssistantCommunicationService":
        """Create a service instance for a specific assistant.

        Args:
            assistant_id: Local assistant ID
            user_id: User ID
            api_key: Optional OpenAI API key

        Returns:
            AssistantCommunicationService instance

        Raises:
            ValueError: If assistant is not found
        """
        logger.debug(f"Creating communication service for assistant {assistant_id}")
        assistant_service = AssistantService()
        # Convert string IDs to UUID objects
        assistant = await assistant_service.get_assistant(
            UUID(assistant_id), UUID(str(user_id))
        )

        if not assistant:
            raise ValueError(f"Assistant {assistant_id} not found")

        if not assistant.get("assistant_id"):
            raise ValueError(
                f"OpenAI Assistant ID not found for assistant {assistant_id}"
            )

        settings = get_settings()
        return cls(
            api_key=api_key or settings.OPENAI_API_KEY,
            openai_assistant_id=assistant["assistant_id"],
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
        tokens_used: int = 0
    ) -> Dict[str, Any]:
        """Save a message to the database.

        Args:
            session_id: Chat session ID
            role: Message role (user/assistant)
            content: Message content
            tokens_used: Number of tokens used

        Returns:
            Saved message data
        """
        message_data = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "tokens_used": tokens_used
        }
        
        result = self.supabase.table("lacl_chat_messages").insert(message_data).execute()
        return result.data[0]

    def create_thread(
        self, messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a new thread with optional initial messages.

        Args:
            messages: List of initial messages

        Returns:
            Created thread data
        """
        thread = self.client.beta.threads.create(messages=messages)
        return thread.model_dump()

    def add_message_to_thread(
        self,
        thread_id: str,
        content: str,
        file_ids: Optional[List[str]] = None,
        assistant_id: Optional[str] = None,
        fingerprint: str = "default"
    ) -> Dict[str, Any]:
        """Add a message to an existing thread.

        Args:
            thread_id: Thread ID
            content: Message content
            file_ids: Optional list of file IDs
            assistant_id: Optional assistant ID for database
            fingerprint: User fingerprint for database

        Returns:
            Created message data
        """
        params = {
            "thread_id": thread_id,
            "role": "user",
            "content": content,
        }
        
        if file_ids is not None:
            params["file_ids"] = file_ids
            
        message = self.client.beta.threads.messages.create(**params)
        
        # Save to database if assistant_id is provided
        if assistant_id:
            session = self._get_or_create_chat_session(thread_id, assistant_id, fingerprint)
            self._save_message(
                session_id=session["id"],
                role="user",
                content=content
            )
            
        return message.model_dump()

    def run_assistant(
        self,
        thread_id: str,
        instructions: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Run the assistant on a thread.

        Args:
            thread_id: Thread ID
            instructions: Optional override instructions
            tools: Optional list of tools to use

        Returns:
            Created run data

        Raises:
            ValueError: If OpenAI assistant ID is not found
        """
        if not self.openai_assistant_id:
            raise ValueError("OpenAI Assistant ID not found")

        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.openai_assistant_id,
            instructions=instructions,
            tools=tools or [],
        )
        return run.model_dump()

    def get_run(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Get the status of a run.

        Args:
            thread_id: Thread ID
            run_id: Run ID

        Returns:
            Run status data
        """
        run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        return run.model_dump()

    def get_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a thread.

        Args:
            thread_id: Thread ID

        Returns:
            List of messages
        """
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        
        # For each message from OpenAI, ensure it's saved in our database
        for message in messages.data:
            msg_data = message.model_dump()
            # Find the session for this thread
            session_result = (
                self.supabase.table("lacl_chat_sessions")
                .select("*")
                .eq("metadata->>thread_id", thread_id)
                .execute()
            )
            
            if session_result.data:
                session = session_result.data[0]
                # Check if message exists
                msg_result = (
                    self.supabase.table("lacl_chat_messages")
                    .select("*")
                    .eq("session_id", session["id"])
                    .eq("metadata->>message_id", msg_data["id"])
                    .execute()
                )
                
                if not msg_result.data:
                    # Save message if it doesn't exist
                    content = msg_data["content"][0]["text"]["value"] if msg_data["content"] else ""
                    self._save_message(
                        session_id=session["id"],
                        role=msg_data["role"],
                        content=content,
                        tokens_used=0  # We could calculate this if needed
                    )
        
        return [message.model_dump() for message in messages.data]

    def submit_tool_outputs(
        self, thread_id: str, run_id: str, tool_outputs: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Submit tool outputs for a run.

        Args:
            thread_id: Thread ID
            run_id: Run ID
            tool_outputs: List of tool outputs

        Returns:
            Updated run data
        """
        run = self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id, run_id=run_id, tool_outputs=tool_outputs
        )
        return run.model_dump()

    def cancel_run(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Cancel a run.

        Args:
            thread_id: Thread ID
            run_id: Run ID

        Returns:
            Cancelled run data
        """
        run = self.client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run_id)
        return run.model_dump()

    def get_session_messages(
        self,
        session_id: str,
        fingerprint: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages from a specific chat session.

        Args:
            session_id: Chat session ID
            fingerprint: User fingerprint
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of chat messages
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
            
        # Get messages
        result = (
            self.supabase.table("lacl_chat_messages")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        
        return result.data

    def get_messages_from_sessions(
        self,
        fingerprint: str,
        session_ids: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages from multiple chat sessions.

        Args:
            fingerprint: User fingerprint
            session_ids: Optional list of session IDs to filter by
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of chat messages
        """
        # First get all sessions for this fingerprint
        sessions_query = (
            self.supabase.table("lacl_chat_sessions")
            .select("id")
            .eq("fingerprint", fingerprint)
        )
        
        if session_ids:
            sessions_query = sessions_query.in_("id", session_ids)
            
        sessions = sessions_query.execute()
        
        if not sessions.data:
            return []
            
        # Get all session IDs
        session_ids = [session["id"] for session in sessions.data]
        
        # Now get messages for these sessions
        result = (
            self.supabase.table("lacl_chat_messages")
            .select("*")
            .in_("session_id", session_ids)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        
        return result.data

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


# Don't create a global instance as we need different instances for different API keys
