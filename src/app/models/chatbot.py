from sqlalchemy import Column, String, Boolean, JSON, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.db.base_class import Base

class Chatbot(Base):
    __tablename__ = "chatbots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    design_settings = Column(JSON, nullable=False)
    features = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    openai_api_key = Column(String, nullable=True)
    model_name = Column(String, nullable=False, default="gpt-4-turbo-preview")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now()) 