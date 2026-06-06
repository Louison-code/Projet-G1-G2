from pydantic import BaseModel
from typing import Optional


class ConversationBase(BaseModel):
    question: str
    sql_genere: Optional[str] = None
    reponse: Optional[str] = None
    resultats_count: Optional[int] = None
    temps_execution_ms: Optional[float] = None


class ConversationCreate(ConversationBase):
    pass


class Conversation(ConversationBase):
    id: int
    timestamp: Optional[str] = None
