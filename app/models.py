from typing import Literal
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=4000)
    channel: str = Field(default="web", max_length=50)
    consent_to_contact: bool | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    stage: str
    lead_created: bool = False
    handoff: bool = False


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    provider: str


class Lead(BaseModel):
    session_id: str
    name: str | None = None
    contact: str | None = None
    need: str | None = None
    channel: str = "web"
    consent: bool = False

