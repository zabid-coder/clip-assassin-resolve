import logging
import os
import sys

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Ensure resolve_core is accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from resolve_core import ResolveConnection
import db

# Import new template engine modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.template_engine import template_engine
from services.jobs import JobManager, native_lock
from services import library, workflows, integrations
from services.folder_presets import capture
from services.builtin_templates import get_builtin_templates, get_builtin_template_by_id
from models.ingest_template import IngestTemplate, FolderNode, TemplateParameter
from config import config
from pathlib import Path
import asyncio
from starlette.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("clip_assassin")

app = FastAPI(title="Clip Assassin API", version="2.1.1")

# CORS: only the local dev vite server and the packaged desktop app origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize Resolve engine
engine = ResolveConnection()
jobs = JobManager()
job_runner = workflows.runner(engine)

# --- Pydantic Models ---

class ConnectResponse(BaseModel):
    success: bool
    message: str

class CutRequest(BaseModel):
    timecodes: str
    reverse: bool = False
    clip_name: Optional[str] = ""

class ClipPickRequest(BaseModel):
    names: str

class MarkerRequest(BaseModel):
    color: str = "All"

class FlagRequest(BaseModel):
    color: str = "Green"

class MergeRequest(BaseModel):
    timeline_names: str

class WatermarkRequest(BaseModel):
    image_path: str

class BatchRenderRequest(BaseModel):
    timelines: List[str]
    target_dir: str
    preset_name: str

class ThumbnailRequest(BaseModel):
    mode: str
    target_dir: str

class ShotlistRequest(BaseModel):
    format: str
    target_path: str
    template_path: Optional[str] = ""

class MasterIngestRequest(BaseModel):
    master_folder_path: str

class CreateMasterFolderRequest(BaseModel):
    parent_dir: str
    project_name: str
    client_name: Optional[str] = ""
    project_type: Optional[str] = "Standard Video"
    custom_date: Optional[str] = ""

class CreateMasterFolderResponse(BaseModel):
    success: bool
    message: str
    folder_path: str

class TemplateImportRequest(BaseModel):
    template_name: str

# New Post Haste-style template API models
class TemplateParameterInput(BaseModel):
    name: str
    value: Any

class TemplateCreateRequest(BaseModel):
    name: str
    description: str
    category: str = "Custom"
    parameters: List[TemplateParameter] = Field(default_factory=list)
    structure: List[FolderNode] = Field(default_factory=list)

class TemplatePreviewRequest(BaseModel):
    template_id: str
    parameters: Dict[str, Any]
    base_path: str = "/preview"

class TemplateGenerateRequest(BaseModel):
    template_id: str
    parameters: Dict[str, Any]
    base_path: str
    dry_run: bool = False

class TemplateListResponse(BaseModel):
    success: bool
    templates: List[Dict[str, Any]]

class TemplatePreviewResponse(BaseModel):
    success: bool
    preview_tree: str
    item_count: int

class TemplateGenerateResponse(BaseModel):
    success: bool
    message: str
    created_items: List[Dict[str, Any]]
    total_items: int
    base_path: str

class SetTimelineRequest(BaseModel):
    timeline_name: str

class SettingRequest(BaseModel):
    key: str
    value: str

class StandardResponse(BaseModel):
    success: bool
    message: str

# --- API Endpoints ---

# Resolve's native connection and the active project are shared across requests.
# Serialize calls, including polling, so a job cannot switch context under another job.
RESOLVE_PATHS = {
    "status", "connect", "stats", "context", "set_context", "cut", "pick_clips",
    "markers_to_timeline", "filter_by_flag", "merge_timelines", "apply_watermark",
    "batch_render", "extract_thumbnails", "youtube_chapters", "organize_bins", "auto_sync",
    "social_reframe", "add_title", "add_adjustment_layer", "export_shotlist", "master_ingest",
    "subtitles", "upload_youtube", "import_template", "snapshot", "batch_rename", "project_stats",
    "jl_cut", "render_status", "render_presets", "silence_remove", "badwords/scan", "badwords/clean",
}

@app.middleware("http")
async def resolve_context_middleware(request: Request, call_next):
    route = request.url.path.removeprefix("/api/")
    if route not in RESOLVE_PATHS or request.method == "OPTIONS":
        return await call_next(request)
    await run_in_threadpool(native_lock.acquire)
    try:
        if route not in {"connect", "master_ingest"}:
            await run_in_threadpool(engine.refresh)
        if route not in {"status", "connect", "master_ingest", "import_template"} and not engine.project:
            return JSONResponse(content={"success": False, "message": "Open a Resolve project and connect first."})
        return await call_next(request)
    except Exception:
        logger.exception("Resolve operation failed: %s", route)
        return JSONResponse(status_code=500, content={"success": False, "message": "Resolve operation failed. Reconnect and try again."})
    finally:
        native_lock.release()

@app.get("/api/health")
def health():
    return {"success": True, "version": app.version}

@app.get("/api/status", response_model=ConnectResponse)
def get_status():
    return ConnectResponse(success=bool(engine.resolve), message=engine.connection_message)

@app.post("/api/connect", response_model=ConnectResponse)
def connect_resolve():
    success, msg = engine.connect()
    engine.connection_message = msg
    return ConnectResponse(success=success, message=msg)

@app.get("/api/stats")
def get_stats():
    """Get live timeline stats"""
    return engine.get_timeline_stats()

@app.post("/api/cut", response_model=StandardResponse)
def execute_cut(req: CutRequest):
    success, msg = engine.cut_video(req.timecodes, req.reverse, req.clip_name)
    return StandardResponse(success=success, message=msg)

@app.post("/api/pick_clips", response_model=StandardResponse)
def execute_pick_clips(req: ClipPickRequest):
    success, msg = engine.pick_clips_from_timeline(req.names)
    return StandardResponse(success=success, message=msg)

@app.post("/api/markers_to_timeline", response_model=StandardResponse)
def execute_markers(req: MarkerRequest):
    success, msg = engine.markers_to_timeline(req.color)
    return StandardResponse(success=success, message=msg)

@app.post("/api/filter_by_flag", response_model=StandardResponse)
def execute_flags(req: FlagRequest):
    success, msg = engine.filter_by_flag(req.color)
    return StandardResponse(success=success, message=msg)

@app.post("/api/merge_timelines", response_model=StandardResponse)
def execute_merge(req: MergeRequest):
    success, msg = engine.merge_timelines(req.timeline_names)
    return StandardResponse(success=success, message=msg)

@app.post("/api/apply_watermark", response_model=StandardResponse)
def execute_watermark(req: WatermarkRequest):
    success, msg = engine.apply_watermark_track(req.image_path)
    return StandardResponse(success=success, message=msg)

@app.post("/api/batch_render", response_model=StandardResponse)
def execute_batch_render(req: BatchRenderRequest):
    success, msg = engine.batch_render(req.timelines, req.preset_name, req.target_dir)
    return StandardResponse(success=success, message=msg)

@app.post("/api/extract_thumbnails", response_model=StandardResponse)
def execute_thumbnails(req: ThumbnailRequest):
    success, msg = engine.extract_thumbnails(req.mode, req.target_dir)
    return StandardResponse(success=success, message=msg)



@app.post("/api/youtube_chapters", response_model=StandardResponse)
def execute_yt_chapters():
    success, msg = engine.generate_youtube_chapters()
    return StandardResponse(success=success, message=msg)

@app.post("/api/organize_bins", response_model=StandardResponse)
def execute_organize_bins():
    success, msg = engine.organize_media_pool()
    return StandardResponse(success=success, message=msg)

@app.post("/api/auto_sync", response_model=StandardResponse)
def execute_auto_sync():
    success, msg = engine.auto_sync_audio()
    return StandardResponse(success=success, message=msg)

class SocialReframeRequest(BaseModel):
    format: str = "9:16"

@app.post("/api/social_reframe", response_model=StandardResponse)
def execute_social_reframe(req: SocialReframeRequest):
    success, msg = engine.create_social_timeline(req.format)
    return StandardResponse(success=success, message=msg)

@app.post("/api/add_title", response_model=StandardResponse)
def execute_add_title():
    success, msg = engine.add_quick_title()
    return StandardResponse(success=success, message=msg)

@app.post("/api/add_adjustment_layer", response_model=StandardResponse)
def execute_add_adjustment():
    success, msg = engine.add_adjustment_layer()
    return StandardResponse(success=success, message=msg)

@app.post("/api/export_shotlist", response_model=StandardResponse)
def execute_export_shotlist(req: ShotlistRequest):
    success, msg = engine.export_shotlist_doc(req.format, req.target_path, req.template_path)
    return StandardResponse(success=success, message=msg)

@app.post("/api/master_ingest", response_model=StandardResponse)
def execute_master_ingest(req: MasterIngestRequest):
    success, msg = engine.run_master_ingest(req.master_folder_path)
    return StandardResponse(success=success, message=msg)

@app.post("/api/create_master_folder", response_model=CreateMasterFolderResponse)
def execute_create_master_folder(req: CreateMasterFolderRequest):
    success, msg, folder_path = engine.run_create_master_folder(req.parent_dir, req.project_name, req.client_name, req.project_type, req.custom_date)
    return CreateMasterFolderResponse(success=success, message=msg, folder_path=folder_path)

@app.post("/api/subtitles", response_model=StandardResponse)
def execute_subtitles():
    success, msg = engine.generate_subtitles()
    return StandardResponse(success=success, message=msg)

@app.post("/api/upload_youtube", response_model=StandardResponse)
def execute_upload_youtube():
    success, msg = engine.upload_to_youtube()
    return StandardResponse(success=success, message=msg)

@app.get("/api/templates")
def get_templates():
    """Get all available templates (built-in + custom)"""
    builtin = [t.to_dict() for t in get_builtin_templates()] + db.get_folder_templates()
    # Could add custom templates from database here
    return {"success": True, "templates": builtin}

@app.get("/api/templates/builtin")
def get_builtin_template_list():
    """Get list of built-in Post Haste-style templates"""
    templates = []
    for t in get_builtin_templates():
        templates.append({
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "tags": t.tags,
            "parameters": [p.dict() for p in t.parameters],
            "builtin_params": t.builtin_params
        })
    return {"success": True, "templates": templates}

@app.get("/api/templates/{template_id}")
def get_template_detail(template_id: str):
    """Get detailed template by ID"""
    template = find_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"success": True, "template": template.to_dict()}

@app.post("/api/templates/preview", response_model=TemplatePreviewResponse)
def preview_template(req: TemplatePreviewRequest):
    """Generate ASCII tree preview of template structure"""
    template = find_template(req.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    preview_tree = template_engine.get_preview_tree(template, req.parameters, req.base_path)
    result = template_engine.generate_structure(template, req.parameters, req.base_path, dry_run=True)
    
    return TemplatePreviewResponse(
        success=result["success"],
        preview_tree=preview_tree,
        item_count=result.get("total_items", 0)
    )

@app.post("/api/templates/generate", response_model=TemplateGenerateResponse)
def generate_template_structure(req: TemplateGenerateRequest):
    """Generate actual folder structure from template"""
    template = find_template(req.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    result = template_engine.generate_structure(
        template, 
        req.parameters, 
        req.base_path, 
        req.dry_run
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=", ".join(result["errors"]))
    
    return TemplateGenerateResponse(
        success=True,
        message=f"Successfully created {result['total_items']} items",
        created_items=result.get("created", []) or result.get("preview", []),
        total_items=result["total_items"],
        base_path=result["base_path"]
    )

def find_template(template_id):
    builtin = get_builtin_template_by_id(template_id)
    if builtin:
        return builtin
    for data in db.get_folder_templates():
        if data["id"] == template_id:
            return IngestTemplate(**data)
    return None

@app.post("/api/templates/create")
@app.post("/api/templates")
def create_custom_template(req: TemplateCreateRequest):
    from uuid import uuid4
    template = IngestTemplate(id=f"custom-{uuid4().hex[:12]}", **req.model_dump())
    # Validate the recursive structure before storing.
    if not template.name.strip() or not template.structure:
        raise HTTPException(400, "Template name and structure are required")
    db.save_folder_template(template)
    return {"success": True, "message": f"Template '{template.name}' saved", "template": template.to_dict()}

@app.put("/api/templates/{template_id}")
def update_custom_template(template_id: str, req: TemplateCreateRequest):
    if not find_template(template_id):
        raise HTTPException(404, "Template not found")
    if get_builtin_template_by_id(template_id):
        raise HTTPException(400, "Save a copy to customize a built-in template")
    if not req.name.strip() or not req.structure:
        raise HTTPException(400, "Template name and structure are required")
    template = IngestTemplate(id=template_id, **req.model_dump())
    db.save_folder_template(template)
    return {"success": True, "message": "Template updated", "template": template.to_dict()}

@app.delete("/api/templates/{template_id}", response_model=StandardResponse)
def delete_custom_template(template_id: str):
    if not db.delete_folder_template(template_id):
        raise HTTPException(404, "Custom template not found")
    return StandardResponse(success=True, message="Template deleted")

@app.post("/api/templates/import", response_model=StandardResponse)
def import_template_file(req: TemplateImportRequest):
    try:
        from uuid import uuid4
        template = template_engine.import_template(req.template_name)
        template.id = f"custom-{uuid4().hex[:12]}"
        db.save_folder_template(template)
        return StandardResponse(success=True, message=f"Template '{template.name}' imported")
    except Exception as exc:
        raise HTTPException(400, str(exc))

@app.post("/api/templates/export", response_model=StandardResponse)
def export_template_file(template_id: str, filepath: str):
    template = find_template(template_id)
    if not template:
        raise HTTPException(404, "Template not found")
    try:
        template_engine.export_template(template, filepath)
        return StandardResponse(success=True, message=f"Template exported to {filepath}")
    except Exception as exc:
        raise HTTPException(400, str(exc))

@app.get("/api/assets")
def get_assets():
    return engine.get_templates()

@app.post("/api/import_template", response_model=StandardResponse)
def import_resolve_asset(req: TemplateImportRequest):
    success, message = engine.import_template(req.template_name)
    return StandardResponse(success=success, message=message)

@app.post("/api/assets/upload")
async def upload_asset(request: Request, filename: str):
    if Path(filename).name != filename or "\\" in filename or filename.startswith("."):
        raise HTTPException(400, "Invalid asset filename")
    if Path(filename).suffix.lower() not in {".drfx", ".setting", ".png", ".jpg", ".jpeg", ".wav", ".mp3", ".mov", ".mp4"}:
        raise HTTPException(400, "Unsupported asset type")
    from uuid import uuid4
    directory = Path(engine.asset_directory())
    destination = directory / filename
    temporary = directory / ('.upload-' + uuid4().hex)
    if destination.exists(): raise HTTPException(409, "An asset with that filename already exists")
    size = 0
    try:
        with temporary.open('xb') as handle:
            async for chunk in request.stream():
                size += len(chunk)
                if size > 512 * 1024 * 1024:
                    raise HTTPException(413, "Asset must be 512 MB or smaller")
                handle.write(chunk)
        if not size: raise HTTPException(400, "Asset is empty")
        if destination.exists(): raise HTTPException(409, "An asset with that filename already exists")
        if destination.suffix.lower() == '.drfx':
            library.archive_entries(temporary)
        temporary.rename(destination)
        if destination.suffix.lower() == '.drfx':
            await run_in_threadpool(library.scan_folder, str(directory))
    finally:
        temporary.unlink(missing_ok=True)
    return {"success": True, "message": f"Added {filename} to the library"}

@app.get("/api/context")
def get_global_context():
    return engine.get_global_context()

@app.post("/api/set_context", response_model=StandardResponse)
def execute_set_context(req: SetTimelineRequest):
    success, msg = engine.set_active_timeline(req.timeline_name)
    return StandardResponse(success=success, message=msg)

@app.get("/api/settings")
def get_settings():
    return {"success": True, "settings": db.get_all_settings()}

import subprocess
import platform

@app.get("/api/browse")
def browse_path(type: str = "file"):
    """Open a native file/folder picker dialog and return the selected path."""
    try:
        if platform.system() == "Darwin":
            if type == "folder":
                script = 'POSIX path of (choose folder with prompt "Select Folder")'
            elif type == "save":
                script = 'POSIX path of (choose file name with prompt "Save As...")'
            else:
                script = 'POSIX path of (choose file with prompt "Select File")'
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            if result.returncode == 0:
                return {"success": True, "path": result.stdout.strip()}
            return {"success": False, "error": "Cancelled"}

        elif platform.system() == "Windows":
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            if type == "folder":
                path = filedialog.askdirectory(title="Select Folder")
            elif type == "save":
                path = filedialog.asksaveasfilename(title="Save As...")
            else:
                path = filedialog.askopenfilename(title="Select File")
            root.destroy()
            if path:
                return {"success": True, "path": path}
            return {"success": False, "error": "Cancelled"}

        else:
            return {"success": False, "error": f"File dialog not supported on {platform.system()}"}
    except Exception as e:
        logger.error(f"Browse dialog error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/open_folder")
def open_folder(path: str):
    """Open a folder in the system file manager with path validation."""
    try:
        full_path = str((Path(__file__).parent / path).resolve()) if not os.path.isabs(path) else str(Path(path).resolve())

        # Security: reject path traversal attempts
        if ".." in path:
            logger.warning(f"Path traversal attempt blocked: {path}")
            return {"success": False, "error": "Invalid path"}

        if not os.path.isdir(full_path):
            return {"success": False, "error": "Folder not found"}

        if platform.system() == "Darwin":
            subprocess.run(['open', full_path])
        elif platform.system() == "Windows":
            subprocess.run(['explorer', full_path])
        else:
            subprocess.run(['xdg-open', full_path])

        return {"success": True}
    except Exception as e:
        logger.error(f"Open folder error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/settings", response_model=StandardResponse)
def save_setting(req: SettingRequest):
    db.set_setting(req.key, req.value)
    return StandardResponse(success=True, message="Setting saved")

# --- BadWords Integration ---

class BadWordsCleanRequest(BaseModel):
    colors: List[str]

@app.get("/api/badwords/scan")
def scan_badwords_markers():
    return engine.scan_badwords_markers()

@app.post("/api/badwords/clean", response_model=StandardResponse)
def clean_badwords_timeline(req: BadWordsCleanRequest):
    success, msg = engine.clean_badwords_timeline(req.colors)
    return StandardResponse(success=success, message=msg)

# --- Utility Tools ---

class RenameRequest(BaseModel):
    prefix: str
    start_number: int = Field(default=1, ge=1)
    scope: str = Field(default="timeline", pattern="^(timeline|selected)$")

class SilenceRequest(BaseModel):
    threshold_db: int = Field(default=-40, ge=-100, le=0)
    min_silence_ms: int = Field(default=500, ge=1, le=60000)
    padding_ms: int = Field(default=100, ge=0, le=10000)

class JLCutRequest(BaseModel):
    cut_type: str = Field(default="j", pattern="^[jl]$")
    overlap_frames: int = Field(default=10, ge=1, le=1000)

@app.post("/api/snapshot", response_model=StandardResponse)
def create_snapshot():
    success, msg = engine.create_snapshot()
    return StandardResponse(success=success, message=msg)

@app.post("/api/batch_rename", response_model=StandardResponse)
def batch_rename(req: RenameRequest):
    success, msg = engine.batch_rename_clips(req.prefix, req.start_number, req.scope)
    return StandardResponse(success=success, message=msg)

@app.get("/api/project_stats")
def get_project_stats():
    return engine.get_project_stats_detail()

@app.post("/api/jl_cut", response_model=StandardResponse)
def apply_jl_cuts(req: JLCutRequest):
    success, msg = engine.apply_jl_cuts(req.cut_type, req.overlap_frames)
    return StandardResponse(success=success, message=msg)

@app.get("/api/render_presets")
def get_render_presets():
    return {"success": True, "presets": engine.project.GetRenderPresetList() or []} if engine.project else {"success": False, "message": "Connect to a project first", "presets": []}

@app.get("/api/render_status")
def get_render_status():
    return engine.get_render_status()

@app.post("/api/silence_remove", response_model=StandardResponse)
def detect_silence(req: SilenceRequest):
    success, msg = engine.detect_silence(req.threshold_db, req.min_silence_ms, req.padding_ms)
    return StandardResponse(success=success, message=msg)

class PresetRequest(BaseModel):
    name: str
    data: dict

@app.get("/api/presets")
def get_presets():
    return {"success": True, "presets": db.get_all_presets()}

@app.post("/api/presets", response_model=StandardResponse)
def save_preset(req: PresetRequest):
    db.save_preset(req.name, req.data)
    return StandardResponse(success=True, message="Preset saved")

@app.delete("/api/presets/{preset_id}", response_model=StandardResponse)
def delete_preset(preset_id: int):
    db.delete_preset(preset_id)
    return StandardResponse(success=True, message="Preset deleted")

# Guided library, folder presets, connections and background jobs.
class PathInput(BaseModel):
    path: str

class WorkflowInput(BaseModel):
    operation: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class SubmitInput(BaseModel):
    preview_token: str

class IntegrationInput(BaseModel):
    whisper_model: Optional[str] = None
    openai_key: Optional[str] = None
    youtube_client_id: Optional[str] = None
    youtube_client_secret: Optional[str] = None

@app.exception_handler(ValueError)
async def friendly_value_error(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"success": False, "message": str(exc), "detail": str(exc)})

@app.get("/api/library")
def library_catalog():
    return {"success": True, "packages": library.catalog()}

@app.get("/api/library/{package_id}/preview")
def package_preview_image(package_id: str):
    package = library.package_by_id(package_id)
    if not package.get('preview'):
        raise HTTPException(404, "No preview image available")
    path = (library.BUNDLED / package['preview']).resolve()
    if not path.is_relative_to(library.BUNDLED.resolve()) or not path.is_file():
        raise HTTPException(404, "Preview image not found")
    return FileResponse(str(path))

@app.get("/api/library/{package_id}/notes")
def package_notes(package_id: str):
    package = library.package_by_id(package_id)
    folder = library.package_path(package).parent
    notes = []
    for item in package.get('notes', []):
        path = (folder / item['path']).resolve()
        if path.is_relative_to(folder.resolve()) and path.is_file():
            notes.append({"name": item['name'], "text": path.read_text(encoding='utf-8', errors='replace')[:20000]})
    return {"success": True, "notes": notes}

@app.get("/api/library/{package_id}/verify")
def verify_package(package_id: str):
    return {"success": True, "installation": library.install_status(library.package_by_id(package_id), True)}

@app.post("/api/library/scan")
def scan_library(req: PathInput):
    return library.scan_folder(req.path)

@app.post("/api/library/fonts/refresh")
def refresh_fonts():
    library.font_families.cache_clear()
    return {"success": True, "message": "Font status refreshed", "packages": library.catalog()}

@app.post("/api/library/fonts/install")
def open_font_file(req: PathInput):
    path = Path(req.path).expanduser().resolve()
    if path.suffix.lower() not in ('.ttf', '.otf', '.ttc') or not path.is_file():
        raise HTTPException(400, "Choose a downloaded TTF, OTF or TTC font file")
    if sys.platform == 'darwin': subprocess.run(['open', str(path)], check=True)
    elif sys.platform == 'win32': os.startfile(str(path))
    else: subprocess.run(['xdg-open', str(path)], check=True)
    return {"success": True, "message": "Font installer opened. Complete installation, restart Resolve, then refresh font status."}

@app.post("/api/folder-presets/capture")
def capture_folder_preset(req: PathInput):
    return capture(req.path)

@app.post("/api/jobs/preview")
def preview_workflow(req: WorkflowInput):
    return workflows.preview(engine, req.operation, req.payload)

@app.get("/api/jobs")
def get_jobs():
    return {"success": True, "jobs": jobs.list()}

@app.post("/api/jobs")
def submit_job(req: SubmitInput):
    body = workflows.read_token(req.preview_token)
    # Recheck the preview: selections, files, prerequisites and consent can change.
    current = workflows.preview(engine, body['operation'], body['payload'])
    if not current['ready']: raise HTTPException(400, '; '.join(current['errors']))
    if body['source'] != current['source']:
        raise HTTPException(409, "Resolve selection changed after preview. Review again.")
    return {"success": True, "job": jobs.submit(body['operation'], body['payload'], job_runner, body['source'])}

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job: raise HTTPException(404, "Job not found")
    return {"success": True, "job": job}

@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    return {"success": True, "job": jobs.cancel(job_id)}

@app.post("/api/jobs/{job_id}/retry")
def retry_job(job_id: str):
    previous = jobs.get(job_id)
    if not previous: raise HTTPException(404, "Job not found")
    if previous['status'] in ('queued', 'running', 'cancelling', 'succeeded'):
        raise HTTPException(400, "Only failed, cancelled or interrupted jobs can be retried")
    # Retry always returns a fresh review instead of silently repeating changes.
    return workflows.preview(engine, previous['operation'], previous['payload'])

@app.get("/api/capabilities")
def get_capabilities():
    return workflows.capabilities(engine)

@app.get("/api/integrations")
def integration_status():
    return integrations.status()

@app.post("/api/integrations")
def save_integrations(req: IntegrationInput):
    return integrations.configure(req.model_dump(exclude_none=True))

@app.post("/api/integrations/youtube/connect")
def connect_youtube():
    return integrations.start_youtube_oauth()

@app.post("/api/integrations/youtube/disconnect")
def disconnect_youtube():
    return integrations.disconnect_youtube()

# PyInstaller compatibility for file paths
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Serve the static React frontend
frontend_dist = os.path.join(base_dir, "frontend", "dist")

if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{catchall:path}")
    def serve_frontend(catchall: str):
        # Serve static files if they exist (e.g., /logo.jpg, /favicon.ico)
        if catchall.startswith("api/"):
            raise HTTPException(404, "API endpoint not found")
        file_path = str(Path(frontend_dist, catchall).resolve())
        if not Path(file_path).is_relative_to(Path(frontend_dist).resolve()):
            raise HTTPException(404, "File not found")
        no_cache_headers = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        if os.path.isfile(file_path):
            return FileResponse(file_path, headers=no_cache_headers)
        # Fallback to index.html for client-side routing
        return FileResponse(os.path.join(frontend_dist, "index.html"), headers=no_cache_headers)
else:
    print(f"Warning: Frontend build directory not found at {frontend_dist}. Please run 'npm run build' in the frontend folder.")

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    from threading import Timer
    
    is_prod = getattr(sys, 'frozen', False)
    
    if is_prod:
        # In production (packaged), open the browser automatically
        Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:8000")).start()
        # Must pass 'app' instance, not string, when not using reload
        uvicorn.run(app, host=config.API_HOST, port=config.API_PORT, reload=False)
    else:
        # In development, use reload
        uvicorn.run("server:app", host=config.API_HOST, port=config.API_PORT, reload=False)
