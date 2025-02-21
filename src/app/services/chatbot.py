from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models.chatbot import Chatbot
from app.schemas.chatbot import ChatbotCreate, ChatbotUpdate, ChatbotAnalytics
from datetime import datetime

class ChatbotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_chatbot(self, chatbot: ChatbotCreate, user_id: UUID) -> Chatbot:
        db_chatbot = Chatbot(
            **chatbot.model_dump(),
            user_id=user_id
        )
        self.db.add(db_chatbot)
        await self.db.commit()
        await self.db.refresh(db_chatbot)
        return db_chatbot

    async def get_chatbots(self, user_id: UUID) -> List[Chatbot]:
        query = select(Chatbot).where(Chatbot.user_id == user_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_chatbot(self, chatbot_id: UUID, user_id: UUID) -> Optional[Chatbot]:
        query = select(Chatbot).where(
            Chatbot.id == chatbot_id,
            Chatbot.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_chatbot(
        self, 
        chatbot_id: UUID, 
        chatbot_update: ChatbotUpdate,
        user_id: UUID
    ) -> Optional[Chatbot]:
        update_data = chatbot_update.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_chatbot(chatbot_id, user_id)

        query = (
            update(Chatbot)
            .where(Chatbot.id == chatbot_id, Chatbot.user_id == user_id)
            .values(**update_data)
            .returning(Chatbot)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.scalar_one_or_none()

    async def delete_chatbot(self, chatbot_id: UUID, user_id: UUID) -> bool:
        query = delete(Chatbot).where(
            Chatbot.id == chatbot_id,
            Chatbot.user_id == user_id
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0

    async def update_chatbot_status(
        self, 
        chatbot_id: UUID,
        is_active: bool,
        user_id: UUID
    ) -> Optional[Chatbot]:
        query = (
            update(Chatbot)
            .where(Chatbot.id == chatbot_id, Chatbot.user_id == user_id)
            .values(is_active=is_active)
            .returning(Chatbot)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.scalar_one_or_none()

    async def get_chatbot_analytics(
        self,
        chatbot_id: UUID,
        user_id: UUID
    ) -> Optional[ChatbotAnalytics]:
        # TODO: Implement actual analytics gathering
        # This is a placeholder implementation
        return ChatbotAnalytics(
            total_conversations=0,
            total_messages=0,
            average_response_time=0.0,
            user_satisfaction_rate=None,
            most_common_topics=[],
            created_at=datetime.utcnow()
        )

    async def validate_openai_credentials(
        self,
        chatbot_id: UUID,
        user_id: UUID
    ) -> bool:
        # TODO: Implement actual OpenAI validation
        return True

    def generate_embed_code(self, chatbot_id: UUID) -> Dict[str, str]:
        script_url = f"/static/chatbot.js"
        code = f"""
        <div id="chatbot-{chatbot_id}"></div>
        <script src="{script_url}"></script>
        <script>
            initChatbot('{chatbot_id}');
        </script>
        """
        return {
            "code": code.strip(),
            "script_url": script_url
        } 