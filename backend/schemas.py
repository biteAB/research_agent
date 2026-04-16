"""Pydantic schemas for data validation."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class TodoTask(BaseModel):
    """Schema for a single TODO task."""
    id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Subtask title")
    intent: str = Field(..., description="Research intent/purpose of this task")
    search_queries: List[str] = Field(..., description="List of search queries for this task")


class TodoPlan(BaseModel):
    """Schema for the complete TODO plan."""
    todos: List[TodoTask] = Field(..., description="List of TODO tasks")


class TaskSearchResult(BaseModel):
    """Schema for search results of a single query."""
    query: str
    content: str
    source: Optional[str] = None


class TaskSummary(BaseModel):
    """Schema for a summarized task."""
    task_id: str = Field(..., description="ID of the original task")
    summary: str = Field(..., description="Detailed summary (300-500 words)")
    key_points: List[str] = Field(..., description="List of key points")
    sources: List[str] = Field(..., description="List of source URLs")


class ResearchTask(BaseModel):
    """Schema for a complete research task."""
    task_id: str
    topic: str
    status: str = "pending"  # pending, planning, searching, summarizing, reporting, done, error
    plan: Optional[TodoPlan] = None
    summaries: List[TaskSummary] = Field(default_factory=list)
    report: Optional[str] = None
    indexed: bool = False
    knowledge_path: Optional[str] = None
    indexed_chunks: int = 0
    error: Optional[str] = None


class StartResearchRequest(BaseModel):
    """Request schema for starting research."""
    topic: str = Field(..., description="Research topic provided by user")


class StartResearchResponse(BaseModel):
    """Response schema for starting research."""
    task_id: str = Field(..., description="Unique research task identifier")


class SSEEvent(BaseModel):
    """Schema for SSE event."""
    event: str
    data: Dict[str, Any]

    def to_sse_format(self) -> str:
        """Convert to SSE format."""
        import json
        return f"data: {json.dumps(self.model_dump_json())}\n\n"
