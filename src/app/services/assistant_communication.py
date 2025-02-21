"""Service for handling assistant communication with OpenAI API.

This module provides functionality for managing assistant communication,
including thread and message management, run execution, and response handling.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from openai import OpenAI

from app.core.config import get_settings
from app.core.logger import logger
from app.services.assistant import AssistantService


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

    @classmethod
    async def create_for_assistant(
        cls,
        assistant_id: str,
        user_id: int,
        api_key: Optional[str] = None
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
        logger.debug(
            f"Creating communication service for assistant {assistant_id}"
        )
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
            openai_assistant_id=assistant["assistant_id"]
        )

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
        file_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Add a message to an existing thread.

        Args:
            thread_id: Thread ID
            content: Message content
            file_ids: Optional list of file IDs

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
        return message.model_dump()

    def run_assistant(
        self,
        thread_id: str,
        instructions: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
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
            tools=tools or []
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
        run = self.client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        return run.model_dump()

    def get_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a thread.

        Args:
            thread_id: Thread ID

        Returns:
            List of messages
        """
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        return [message.model_dump() for message in messages.data]

    def submit_tool_outputs(
        self, 
        thread_id: str, 
        run_id: str, 
        tool_outputs: List[Dict[str, str]]
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
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )
        return run.model_dump()

    def cancel_run(
        self, 
        thread_id: str, 
        run_id: str
    ) -> Dict[str, Any]:
        """Cancel a run.

        Args:
            thread_id: Thread ID
            run_id: Run ID

        Returns:
            Cancelled run data
        """
        run = self.client.beta.threads.runs.cancel(
            thread_id=thread_id,
            run_id=run_id
        )
        return run.model_dump()


# Don't create a global instance as we need different instances for different API keys
