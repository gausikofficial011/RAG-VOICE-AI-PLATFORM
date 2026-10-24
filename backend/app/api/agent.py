"""
Autonomous PC Agent API Router
Provides endpoints for executing desktop agent commands, retrieving hardware telemetry,
running system workflows, and controlling PC automation.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.agent.pc_agent import pc_agent
from backend.app.auth.dependencies import get_optional_user
from backend.app.models.user import User
from backend.app.voice.tts import tts_provider

router = APIRouter(prefix="/agent", tags=["PC Agent Automation"])


class AgentCommandRequest(BaseModel):
    command: str = Field(..., description="Natural language prompt or workflow command")
    audio_requested: bool = Field(default=True, description="Whether to synthesize voice output")
    language: str = Field(default="en")


class WorkflowRequest(BaseModel):
    workflow_name: str = Field(..., description="Name of pre-configured system workflow")


@router.post("/command")
async def execute_agent_command(
    req: AgentCommandRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Execute an autonomous PC agent action from a prompt."""
    res = await pc_agent.execute(req.command)
    audio_b64 = None
    if req.audio_requested and res.get("answer"):
        audio_b64 = await tts_provider.synthesize_base64(res["answer"], req.language)

    user_identifier = current_user.email if current_user else "local_desktop_operator"

    return {
        **res,
        "audio_base64": audio_b64,
        "executed_by": user_identifier,
    }


@router.get("/telemetry")
async def get_system_telemetry(current_user: Optional[User] = Depends(get_optional_user)):
    """Fetch live CPU, RAM, Disk, and Battery diagnostics from the laptop."""
    return pc_agent.get_system_telemetry()


@router.get("/processes")
async def get_running_processes(
    limit: int = 10,
    sort_by: str = "memory",
    current_user: Optional[User] = Depends(get_optional_user),
):
    """List running processes and resource consumption."""
    return pc_agent.get_top_processes(limit=limit, sort_by=sort_by)


@router.post("/workflow")
async def execute_workflow(
    req: WorkflowRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Execute pre-defined desktop agent workflows."""
    workflows = {
        "system_health": "Check laptop CPU, memory, disk, and battery status",
        "clean_temp": "Clean temporary cache and free disk space",
        "workspace_scan": "Search and index all workspace files",
        "generate_audit_report": "Generate an automated system audit report",
    }
    prompt = workflows.get(req.workflow_name, req.workflow_name)
    res = await pc_agent.execute(prompt)
    audio_b64 = await tts_provider.synthesize_base64(res["answer"], "en")

    user_identifier = current_user.email if current_user else "local_desktop_operator"

    return {
        **res,
        "workflow": req.workflow_name,
        "audio_base64": audio_b64,
        "executed_by": user_identifier,
    }
