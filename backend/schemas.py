from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    context_used: str

class IngestResponse(BaseModel):
    task_id: str
    status: str
    message: str