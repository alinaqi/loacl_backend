"""
Session repository module.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel
from supabase import Client

from app.core.logger import get_logger
from app.models.auth import GuestSessionRequest
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class SessionCreate(BaseModel):
    """Session creation model."""

    session_type: str
    assistant_id: Optional[str] = None
    fingerprint: Optional[str] = None
    expires_at: str
    metadata: Dict = {}
    status: str = "active"


class SessionRepository(BaseRepository[Dict, SessionCreate, Dict]):
    """Repository for session operations."""

    def __init__(self, client: Client):
        """Initialize repository."""
        super().__init__(client)
        self.table_name = "lacl_sessions"

    async def create_guest_session(
        self, request: GuestSessionRequest, assistant_id: Optional[UUID] = None
    ) -> dict:
        """
        Create a new guest session.

        Args:
            request: Guest session request
            assistant_id: Optional assistant ID

        Returns:
            dict: Created session data
        """
        try:
            # Set expiration time (24 hours from now)
            expires_at = datetime.utcnow() + timedelta(hours=24)

            session_data = SessionCreate(
                session_type="guest",
                assistant_id=str(assistant_id) if assistant_id else None,
                fingerprint=request.device_id,
                expires_at=expires_at.isoformat(),
                metadata=request.metadata or {},
                status="active",
            )

            response = await self.create(session_data)
            return response.data[0] if response and response.data else None

        except Exception as e:
            logger.error("Failed to create guest session", exc_info=str(e))
            raise ValueError(f"Failed to create guest session: {str(e)}")
