from typing import List, Optional, Dict, Any
from openai import OpenAI
from app.core.config import get_settings

class AssistantCommunicationService:
    def __init__(self):
        """Initialize OpenAI client"""
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.OPENAI_API_KEY)

    async def create_thread(self, messages: Optional[List[Dict]] = None) -> Dict:
        """Create a new thread"""
        thread = self.client.beta.threads.create(messages=messages)
        return thread

    async def add_message(self, thread_id: str, content: str, file_ids: Optional[List[str]] = None) -> Dict:
        """Add a message to a thread"""
        message = self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=content,
            file_ids=file_ids or []
        )
        return message

    async def run_assistant(
        self,
        thread_id: str,
        assistant_id: str,
        instructions: Optional[str] = None,
        tools: Optional[List[Dict]] = None
    ) -> Dict:
        """Run the assistant on a thread"""
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            instructions=instructions,
            tools=tools
        )
        return run

    async def get_messages(self, thread_id: str, limit: int = 100) -> List[Dict]:
        """Get messages from a thread"""
        messages = self.client.beta.threads.messages.list(
            thread_id=thread_id,
            limit=limit
        )
        return messages.data

    async def get_run(self, thread_id: str, run_id: str) -> Dict:
        """Get a run's status"""
        run = self.client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        return run

    async def submit_tool_outputs(
        self,
        thread_id: str,
        run_id: str,
        tool_outputs: List[Dict[str, str]]
    ) -> Dict:
        """Submit tool outputs for a run"""
        run = self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )
        return run

    async def cancel_run(self, thread_id: str, run_id: str) -> Dict:
        """Cancel a run"""
        run = self.client.beta.threads.runs.cancel(
            thread_id=thread_id,
            run_id=run_id
        )
        return run

# Create a global instance
assistant_communication_service = AssistantCommunicationService() 