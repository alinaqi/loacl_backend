from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class ThemeSettings(BaseModel):
    primary_color: str = Field(default="#4F46E5")
    secondary_color: str = Field(default="#6366F1")
    text_color: str = Field(default="#111827")
    background_color: str = Field(default="#FFFFFF")

class LayoutSettings(BaseModel):
    width: str = Field(default="380px")
    height: str = Field(default="600px")
    position: str = Field(default="right")

class TypographySettings(BaseModel):
    font_family: str = Field(default="Inter, system-ui, sans-serif")
    font_size: str = Field(default="14px")

class DesignSettings(BaseModel):
    theme: ThemeSettings = Field(default_factory=ThemeSettings)
    layout: LayoutSettings = Field(default_factory=LayoutSettings)
    typography: TypographySettings = Field(default_factory=TypographySettings)

class Features(BaseModel):
    showFileUpload: bool = Field(default=True)
    showVoiceInput: bool = Field(default=True)
    showEmoji: bool = Field(default=True)
    showGuidedQuestions: bool = Field(default=True)
    showFollowUpSuggestions: bool = Field(default=True)

class ChatbotBase(BaseModel):
    name: str = Field(..., description="Name of the chatbot")
    description: Optional[str] = Field(None, description="Description of the chatbot")
    design_settings: DesignSettings = Field(default_factory=DesignSettings)
    features: Features = Field(default_factory=Features)
    is_active: bool = Field(default=True)
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key for the chatbot")
    model_name: str = Field(default="gpt-4-turbo-preview")

class ChatbotCreate(ChatbotBase):
    pass

class ChatbotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    design_settings: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    openai_api_key: Optional[str] = None
    model_name: Optional[str] = None

class ChatbotInDB(ChatbotBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    user_id: UUID

    class Config:
        from_attributes = True

class ChatbotResponse(ChatbotInDB):
    pass

class ChatbotAnalytics(BaseModel):
    total_conversations: int
    total_messages: int
    average_response_time: float
    user_satisfaction_rate: Optional[float]
    most_common_topics: list[str]
    created_at: datetime

class ChatbotStatusUpdate(BaseModel):
    is_active: bool

class ChatbotEmbedCode(BaseModel):
    code: str
    script_url: str 