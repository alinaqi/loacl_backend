"""
User repository module.
"""

from typing import Optional

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Repository for user operations."""

    def __init__(self):
        super().__init__()
        self.table_name = "users"

    async def get_by_client_credentials(
        self, client_id: str, client_secret: str
    ) -> Optional[User]:
        """
        Get user by client credentials.

        Args:
            client_id: Client ID
            client_secret: Client secret

        Returns:
            Optional[User]: User if found and credentials match
        """
        try:
            response = (
                await self.client.table(self.table_name)
                .select("*")
                .match(
                    {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "is_active": True,
                    }
                )
                .execute()
            )

            return User(**response.data[0]) if response.data else None
        except Exception as e:
            logger.error("Failed to get user by client credentials", error=str(e))
            raise
