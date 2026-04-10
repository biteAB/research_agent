"""FastAPI entry point for the deep research agent."""
import sys
import os

# Add the project root directory to Python path
# This allows running from any directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
import uuid
import json
from typing import Dict, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.config import settings
from backend.schemas import (
    StartResearchRequest,
    StartResearchResponse,
    ResearchTask,
    TodoPlan,
    SSEEvent
)
from backend.services.planning_service import get_planning_service
from backend.services.search_service import get_search_service
from backend.services.summarization_service import get_summarization_service
from backend.services.reporting_service import get_reporting_service

# Initialize FastAPI app
app = FastAPI(title="Deep Research Agent", version="1.0.0")

# Add CORS middleware
origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for research tasks (for demo purposes)
# In production, use Redis or a database
research_tasks: Dict[str, ResearchTask] = {}

# Get services
planning_service = get_planning_service()
search_service = get_search_service()
summarization_service = get_summarization_service()
reporting_service = get_reporting_service()


class StartResearchRequest(BaseModel):
    topic: str


@app.post("/api/research/start", response_model=StartResearchResponse)
async def start_research(request: StartResearchRequest) -> StartResearchResponse:
    """Start a new research task.

    Args:
        request: Contains the research topic

    Returns:
        Task ID for the new research
    """
    task_id = str(uuid.uuid4())
    task = ResearchTask(
        task_id=task_id,
        topic=request.topic,
        status="planning"
    )
    research_tasks[task_id] = task
    return StartResearchResponse(task_id=task_id)


def _format_sse_event(event_type: str, data: dict) -> str:
    """Format a SSE event."""
    import json
    return f"data: {json.dumps({'event': event_type, 'data': data})}\n\n"


@app.get("/api/research/stream/{task_id}")
async def stream_research(task_id: str):
    """SSE endpoint for streaming research progress.

    Args:
        task_id: The research task ID

    Returns:
        StreamingResponse with SSE events
    """
    if task_id not in research_tasks:
        def error_stream():
            yield _format_sse_event("error", {"message": "Task not found"})
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    task = research_tasks[task_id]

    async def event_generator():
        try:
            # Step 1: Planning
            yield _format_sse_event("status", {"message": "正在制定研究计划..."})

            plan, error = await planning_service.create_plan(task.topic)
            if error is not None:
                task.status = "error"
                task.error = error
                yield _format_sse_event("error", {"message": error})
                return

            task.plan = plan
            yield _format_sse_event("planning", {"todos": [t.model_dump() for t in plan.todos]})

            # Step 2: Search and summarize all tasks in parallel
            # Create a queue for passing events from parallel tasks
            event_queue: asyncio.Queue[str] = asyncio.Queue()

            async def process_single_task(todo):
                # Search
                await event_queue.put(_format_sse_event("searching", {
                    "task_id": todo.id,
                    "task_title": todo.title
                }))
                task.status = f"searching:{todo.id}"

                search_results = await search_service.search_task(todo)

                # Summarize
                await event_queue.put(_format_sse_event("summarizing", {
                    "task_id": todo.id,
                    "task_title": todo.title
                }))
                task.status = f"summarizing:{todo.id}"

                summary, error = await summarization_service.summarize_task(todo, search_results)
                if error is not None:
                    await event_queue.put(_format_sse_event("error", {"message": error}))
                    return None

                await event_queue.put(_format_sse_event("summary_done", summary.model_dump()))
                await asyncio.sleep(0.1)
                return summary

            # Start all tasks concurrently
            processing_tasks = [process_single_task(todo) for todo in plan.todos]

            # Create a wrapper that puts all tasks and signals when done
            async def run_all_tasks():
                results = await asyncio.gather(*processing_tasks)
                # Signal consumer we're done by putting a sentinel
                await event_queue.put(None)  # None = done
                # Check for errors
                for result in results:
                    if result is None:
                        return False
                # Collect all summaries
                task.summaries = [r for r in results if r is not None]
                return True

            # Start processor in background
            processor_task = asyncio.create_task(run_all_tasks())

            # Consume events from queue until we get the sentinel None
            while True:
                event = await event_queue.get()
                if event is None:
                    # All done
                    event_queue.task_done()
                    break
                yield event
                event_queue.task_done()

            # Wait for processor to complete and check for success
            success = await processor_task
            if not success:
                return

            # Step 3: Generate final report with streaming
            task.status = "reporting"
            yield _format_sse_event("reporting", {})

            report_chunks = []
            async for chunk in reporting_service.generate_report_stream(task.topic, task.summaries):
                report_chunks.append(chunk)
                yield _format_sse_event("report_chunk", {"chunk": chunk})

            full_report = "".join(report_chunks)
            task.status = "done"
            yield _format_sse_event("done", {"report": full_report})

        except Exception as e:
            task.status = "error"
            task.error = str(e)
            yield _format_sse_event("error", {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/research/{task_id}")
async def get_research_status(task_id: str) -> Optional[ResearchTask]:
    """Get the current status of a research task."""
    return research_tasks.get(task_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
