from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    sql: str
    max_retries: int = 2

class VerificationResult(BaseModel):
    success: bool
    attempts: int
    original_orm: str
    final_orm: str
    error_message: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None

class HealthResponse(BaseModel):
    status: str
    database: str
    memory_count: int