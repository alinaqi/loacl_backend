from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.core.config import get_settings


class AssistantCommunicationService:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI client"""
        self.settings = get_settings()
        self.api_key = api_key or self.settings.OPENAI_API_KEY
        print(
            f"Initializing OpenAI client with API key: {self.api_key[:10]}..."
        )  # Debug print
        self.client = OpenAI(api_key=self.api_key)

    @classmethod
    def create_for_assistant(
        cls, assistant_data: Dict
    ) -> "AssistantCommunicationService":
        """Create service instance for a specific assistant"""
        return cls(api_key=assistant_data.get("api_key"))

    async def create_thread(self, messages: Optional[List[Dict]] = None) -> Dict:
        """Create a new thread"""
        try:
            thread = self.client.beta.threads.create(messages=messages)
            print(f"Thread created: {thread}")  # Debug print
            return thread.model_dump()
        except Exception as e:
            print(f"Error creating thread: {str(e)}")  # Debug print
            raise

    async def add_message(
        self, thread_id: str, content: str, file_ids: Optional[List[str]] = None
    ) -> Dict:
        """Add a message to a thread"""
        message_params = {"thread_id": thread_id, "role": "user", "content": content}
        if file_ids:
            message_params["file_ids"] = file_ids

        message = self.client.beta.threads.messages.create(**message_params)
        return message.model_dump()

    async def run_assistant(
        self,
        thread_id: str,
        assistant_id: str,
        instructions: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Dict:
        """Run the assistant on a thread"""
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            instructions=instructions,
            tools=tools,
        )
        return run.model_dump()

    async def get_messages(self, thread_id: str, limit: int = 100) -> List[Dict]:
        """Get messages from a thread"""
        messages = self.client.beta.threads.messages.list(
            thread_id=thread_id, limit=limit
        )
        return [msg.model_dump() for msg in messages.data]

    async def get_run(self, thread_id: str, run_id: str) -> Dict:
        """Get a run's status"""
        run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        return run.model_dump()

    async def submit_tool_outputs(
        self, thread_id: str, run_id: str, tool_outputs: List[Dict[str, str]]
    ) -> Dict:
        """Submit tool outputs for a run"""
        run = self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id, run_id=run_id, tool_outputs=tool_outputs
        )
        return run.model_dump()

    async def cancel_run(self, thread_id: str, run_id: str) -> Dict:
        """Cancel a run"""
        run = self.client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run_id)
        return run.model_dump()


# Don't create a global instance as we need different instances for different API keys
