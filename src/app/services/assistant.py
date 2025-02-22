"""Service for managing assistants in the database."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import jwt
from supabase.lib.client_options import ClientOptions

from app.core.config import get_settings
from app.core.logger import logger
from supabase import Client, create_client


class AssistantService:
    """Service for managing assistants in the database."""

    def __init__(self):
        """Initialize the service with Supabase client."""
        settings = get_settings()

        # Create service role JWT
        service_role_jwt = jwt.encode(
            {
                "role": "service_role",
                "iss": "supabase",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(days=1),
                "sub": "service_role",  # Important for service role auth
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
            settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY, options=options
        )

    async def create_assistant(self, assistant_data: Dict, user_id: UUID) -> Dict:
        """Create a new assistant.

        Args:
            assistant_data: Assistant data including OpenAI assistant ID
            user_id: User ID

        Returns:
            Created assistant data
        """
        logger.debug(f"Creating assistant with data: {assistant_data}")

        # Convert assistant_data to dict if it's not already
        data = (
            assistant_data
            if isinstance(assistant_data, dict)
            else assistant_data.model_dump()
        )

        # Add user_id to the data
        data["user_id"] = str(user_id)

        # Keep the assistant_id as is since that's our column name
        logger.debug(f"Final data for insert: {data}")

        try:
            result = self.supabase.table("lacl_assistants").insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating assistant: {str(e)}")
            raise

    async def get_assistants(self, user_id: UUID) -> List[Dict]:
        """Get all assistants for a user.

        Args:
            user_id: User ID

        Returns:
            List of assistants
        """
        result = (
            self.supabase.table("lacl_assistants")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )
        return result.data

    async def get_assistant(self, assistant_id: UUID, user_id: UUID) -> Optional[Dict]:
        """Get a specific assistant.

        Args:
            assistant_id: Assistant ID
            user_id: User ID

        Returns:
            Assistant data or None if not found
        """
        result = (
            self.supabase.table("lacl_assistants")
            .select("*")
            .eq("id", str(assistant_id))
            .eq("user_id", str(user_id))
            .execute()
        )

        if not result.data:
            return None

        return result.data[0]

    async def update_assistant(
        self, assistant_id: UUID, assistant_update: Dict, user_id: UUID
    ) -> Optional[Dict]:
        """Update an assistant.

        Args:
            assistant_id: Assistant ID
            assistant_update: Update data
            user_id: User ID

        Returns:
            Updated assistant data or None if not found
        """
        update_data = assistant_update.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_assistant(assistant_id, user_id)

        result = (
            self.supabase.table("lacl_assistants")
            .update(update_data)
            .eq("id", str(assistant_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        return result.data[0] if result.data else None

    async def delete_assistant(self, assistant_id: UUID, user_id: UUID) -> bool:
        """Delete an assistant.

        Args:
            assistant_id: Assistant ID
            user_id: User ID

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If assistant not found
        """
        # First verify the assistant exists and belongs to the user
        assistant = await self.get_assistant(assistant_id, user_id)
        if not assistant:
            raise ValueError(f"Assistant {assistant_id} not found")

        try:
            # Delete chat messages from all sessions for this assistant
            sessions_result = (
                self.supabase.table("lacl_chat_sessions")
                .select("id")
                .eq("assistant_id", str(assistant_id))
                .execute()
            )
            if sessions_result.data:
                session_ids = [session["id"] for session in sessions_result.data]
                self.supabase.table("lacl_chat_messages").delete().in_(
                    "session_id", session_ids
                ).execute()

            # Delete chat sessions
            self.supabase.table("lacl_chat_sessions").delete().eq(
                "assistant_id", str(assistant_id)
            ).execute()

            # Finally delete the assistant
            self.supabase.table("lacl_assistants").delete().eq(
                "id", str(assistant_id)
            ).execute()

            return True
        except Exception as e:
            logger.error(f"Error deleting assistant {assistant_id}: {str(e)}")
            raise

    async def get_assistant_analytics(self, assistant_id: UUID, user_id: UUID) -> Dict:
        """Get analytics for an assistant.

        Args:
            assistant_id: Assistant ID
            user_id: User ID

        Returns:
            Analytics data
        """
        # Get total conversations
        conversations = (
            self.supabase.table("lacl_chat_sessions")
            .select("id", count="exact")
            .eq("assistant_id", str(assistant_id))
            .execute()
        )
        total_conversations = (
            conversations.count if conversations.count is not None else 0
        )

        # Get total messages
        messages = (
            self.supabase.table("lacl_chat_messages")
            .select("id", count="exact")
            .eq("assistant_id", str(assistant_id))
            .execute()
        )
        total_messages = messages.count if messages.count is not None else 0

        # Get average response time
        response_times = (
            self.supabase.table("lacl_chat_messages")
            .select("created_at", "parent_id")
            .eq("assistant_id", str(assistant_id))
            .execute()
        )
        total_time = 0
        response_count = 0

        if response_times.data:
            messages_by_id = {msg["id"]: msg for msg in response_times.data}
            for msg in response_times.data:
                if msg.get("parent_id") and msg["parent_id"] in messages_by_id:
                    parent = messages_by_id[msg["parent_id"]]
                    response_time = (
                        datetime.fromisoformat(msg["created_at"])
                        - datetime.fromisoformat(parent["created_at"])
                    ).total_seconds()
                    total_time += response_time
                    response_count += 1

        avg_response_time = total_time / response_count if response_count > 0 else 0

        # Get most common topics (placeholder - you might want to implement actual topic extraction)
        most_common_topics = []

        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "average_response_time": avg_response_time,
            "user_satisfaction_rate": None,  # Implement if you have user ratings
            "most_common_topics": most_common_topics,
        }

    async def validate_openai_credentials(
        self, assistant_id: UUID, user_id: UUID
    ) -> bool:
        """Validate OpenAI API key.

        Args:
            assistant_id: Assistant ID
            user_id: User ID

        Returns:
            True if valid, False otherwise
        """
        assistant = await self.get_assistant(assistant_id, user_id)
        if not assistant or not assistant.get("api_key"):
            return False

        # TODO: Implement actual OpenAI API validation
        # For now, we'll just check if the key exists
        return True

    def generate_embed_code(self, assistant_id: UUID) -> Dict[str, str]:
        """Generate embed code for the assistant widget.

        Args:
            assistant_id: Assistant ID

        Returns:
            Embed code and script URL
        """
        script_url = f"/static/assistant.js"
        code = f"""
        <div id="assistant-{assistant_id}"></div>
        <script src="{script_url}"></script>
        <script>
            initAssistant('{assistant_id}');
        </script>
        """
        return {"code": code.strip(), "script_url": script_url}

    async def update_embed_settings(
        self, assistant_id: UUID, embed_settings: Dict
    ) -> bool:
        """Update embed settings for an assistant.

        Args:
            assistant_id: Assistant ID
            embed_settings: Embed settings data

        Returns:
            True if updated, False otherwise
        """
        try:
            # First, check if embed settings exist
            result = (
                self.supabase.table("lacl_embed_settings")
                .select("*")
                .eq("assistant_id", str(assistant_id))
                .execute()
            )

            data = {
                "allowed_domains": embed_settings.get("allowed_domains", []),
                "custom_styles": embed_settings.get("custom_styles"),
                "custom_script": embed_settings.get("custom_script"),
                "auto_open": embed_settings.get("auto_open", False),
                "delay_open": embed_settings.get("delay_open"),
                "updated_at": datetime.utcnow().isoformat(),
            }

            if result.data:
                # Update existing settings
                result = (
                    self.supabase.table("lacl_embed_settings")
                    .update(data)
                    .eq("assistant_id", str(assistant_id))
                    .execute()
                )
            else:
                # Create new settings
                data["assistant_id"] = str(assistant_id)
                data["created_at"] = data["updated_at"]
                result = (
                    self.supabase.table("lacl_embed_settings").insert(data).execute()
                )

            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating embed settings: {str(e)}")
            return False
