from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.database.db import ProjectDB

router = APIRouter(prefix="/api/projects", tags=["Projects"])

class CreateProjectRequest(BaseModel):
    name: str = "New Project"
    settings: Optional[Dict[str, Any]] = None

class SaveProjectRequest(BaseModel):
    name: str
    settings: Dict[str, Any] = {}
    clips: List[Dict[str, Any]] = []
    subtitles: List[Dict[str, Any]] = []

@router.get("")
async def list_all_projects():
    """Lists all saved projects with timestamps."""
    return ProjectDB.list_projects()

@router.post("")
async def create_new_project(req: CreateProjectRequest):
    """Creates a new project record."""
    return ProjectDB.create_project(name=req.name, settings=req.settings)

@router.get("/{project_id}")
async def get_project_state(project_id: str):
    """Loads complete project state including timeline clips, subtitles, and history."""
    proj = ProjectDB.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj

@router.post("/{project_id}/save")
async def save_project_state(project_id: str, req: SaveProjectRequest):
    """Persists project changes, clips, and subtitles to SQLite."""
    ProjectDB.save_project(
        proj_id=project_id,
        name=req.name,
        settings=req.settings,
        clips=req.clips,
        subtitles=req.subtitles
    )
    return {"success": True, "message": f"Project '{req.name}' saved successfully."}

@router.post("/{project_id}/autosave")
async def autosave_project(project_id: str, req: SaveProjectRequest):
    """Performs background autosave."""
    ProjectDB.save_project(
        proj_id=project_id,
        name=req.name,
        settings=req.settings,
        clips=req.clips,
        subtitles=req.subtitles
    )
    return {"success": True, "autosaved": True}
