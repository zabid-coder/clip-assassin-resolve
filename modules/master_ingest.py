import os
import sys
import time
import subprocess
import logging
from services.jobs import checkpoint
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("clip_assassin.master_ingest")

# Import template engine
try:
    from modules.template_engine import template_db
except ImportError:
    from template_engine import template_db

from services.ingest_plan import SUPPORTED_EXTENSIONS, IGNORED_FOLDERS, plan_ingest

def get_versioned_project_name(base_name: str, existing_projects: list[str]) -> str:
    has_match = any(p == base_name or p.startswith(f"{base_name}_v") for p in existing_projects)
    if not has_match:
        return base_name
    
    version = 2
    while f"{base_name}_v{version}" in existing_projects or (version == 1 and base_name in existing_projects):
        version += 1
    return f"{base_name}_v{version}"

def ensure_resolve_running(core) -> tuple[bool, str]:
    success, msg = core.connect()
    if success:
        return True, "Connected to DaVinci Resolve."
    
    # Attempt OS launch using AppleScript to bypass macOS LaunchServices error -54
    try:
        if sys.platform == "darwin":
            res = subprocess.run(["osascript", "-e", 'tell application "DaVinci Resolve" to activate'], capture_output=True)
            if res.returncode != 0:
                res2 = subprocess.run(["osascript", "-e", 'tell application "DaVinci Resolve Studio" to activate'], capture_output=True)
                if res2.returncode != 0:
                    subprocess.Popen(["open", "-a", "DaVinci Resolve"])
        elif sys.platform == "win32":
            win_paths = [
                r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe"
            ]
            launched = False
            for p in win_paths:
                if os.path.exists(p):
                    subprocess.Popen([p])
                    launched = True
                    break
            if not launched:
                os.system('start "" "DaVinci Resolve"')
        else:
            subprocess.Popen(["resolve"])
    except Exception as e:
        return False, f"Failed to launch Resolve: {str(e)}"
    
    # Poll for connection up to 35s
    for _ in range(35):
        time.sleep(1)
        success, msg = core.connect()
        if success:
            return True, "Resolve started and connected successfully."
            
    return False, "Could not connect to DaVinci Resolve. Please ensure DaVinci Resolve is open, and close any open dialogs/modal windows (like 'Add Project Library' or 'Preferences') inside Resolve."

def create_master_folder_structure(parent_dir: str, project_name: str, client_name: str = "", project_type: str = "Standard Video", custom_date: str = "") -> tuple[bool, str, str]:
    """
    Creates a Post Haste-style standardized Master Folder structure on disk.
    Returns (success, message, folder_path).
    """
    if not parent_dir or not os.path.exists(parent_dir):
        return False, f"Invalid parent folder path: '{parent_dir}'", ""
    
    clean_proj = project_name.strip() if project_name else ""
    if not clean_proj:
        return False, "Project name is required", ""
    clean_client = client_name.strip() if client_name else ""
    date_str = custom_date.strip() if custom_date and custom_date.strip() else time.strftime("%Y-%m-%d")
    
    for part in (clean_proj, clean_client, date_str):
        if part in (".", "..") or any(c in part for c in '/\\\0'):
            return False, "Project, client and date must not contain path separators", ""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return False, "Date must use YYYY-MM-DD", ""
    if clean_client:
        folder_name = f"{date_str}_{clean_client}_{clean_proj}"
    else:
        folder_name = f"{date_str}_{clean_proj}"
        
    master_path = os.path.join(parent_dir, folder_name)
    
    # Preset folder hierarchies (All presets include 'Logos & Branding')
    if "Social" in project_type:
        subfolders = [
            os.path.join("Raw Footages", "Card 01"),
            "Davinci Resolve Database",
            "Logos & Branding",
            "Audio & Music",
            "Graphics & Assets",
            "Exports"
        ]
    elif "Commercial" in project_type:
        subfolders = [
            os.path.join("Raw Footages", "Camera A"),
            os.path.join("Raw Footages", "Camera B"),
            "Davinci Resolve Database",
            "Logos & Branding",
            "Audio & Voiceover",
            "Motion Graphics",
            "Photoshop",
            "Client Approvals & Exports",
            "Documents"
        ]
    else: # Standard Video & Film
        subfolders = [
            os.path.join("Raw Footages", "Card 01"),
            os.path.join("Raw Footages", "Card 02"),
            "Davinci Resolve Database",
            "Logos & Branding",
            "BG Music",
            "After Effects",
            "Photoshop",
            "Exports",
            "Production Documents"
        ]
        
    try:
        os.makedirs(master_path, exist_ok=True)
        for sf in subfolders:
            os.makedirs(os.path.join(master_path, sf), exist_ok=True)
        return True, f"✓ Master Folder structure successfully created at: {master_path}", master_path
    except Exception as e:
        return False, f"Failed to create Master Folder: {str(e)}", ""

def process_master_ingest(core, master_folder_path: str) -> tuple[bool, str]:
    if not master_folder_path or not os.path.isdir(master_folder_path):
        return False, f"Invalid master folder path: '{master_folder_path}'"
    
    try:
        plan = plan_ingest(master_folder_path)
    except (ValueError, OSError) as exc:
        return False, str(exc)
    if not plan['groups']:
        return False, 'No supported footage found. No Resolve project was created.'
    master_folder_path = plan['root']

    connected, conn_msg = ensure_resolve_running(core)
    if not connected:
        return False, conn_msg
    
    pm = core.project_manager
    if not pm:
        return False, "Could not access Resolve Project Manager."
    
    base_project_name = os.path.basename(os.path.normpath(master_folder_path))
    
    # Keep the user's active project library; ingest must not switch databases.
    # Project Library Selection
    # 2. Project Creation & Versioning
    existing_projects = pm.GetProjectListInCurrentFolder() or []
    target_project_name = get_versioned_project_name(base_project_name, existing_projects)
    
    project = pm.CreateProject(target_project_name)
    if not project:
        return False, f"Failed to create/open project: '{target_project_name}'"
    
    core.project = project
    
    # Set Working Folders (Project media location, CacheClip, Gallery) to Master Folder
    try:
        project.SetSetting("projectMediaLocation", master_folder_path)
        cache_dir = os.path.join(master_folder_path, "CacheClip")
        gallery_dir = os.path.join(master_folder_path, ".gallery")
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(gallery_dir, exist_ok=True)
        project.SetSetting("perfCacheClipsLocation", cache_dir)
        project.SetSetting("colorGalleryStillsLocation", gallery_dir)
    except Exception as e:
        logger.info(f"Working Folders setting note: {e}")

    core.media_pool = project.GetMediaPool()
    media_pool = core.media_pool
    if not media_pool:
        return False, "Could not access Media Pool in new project."
    
    root_folder = media_pool.GetRootFolder()
    created_timelines = []
    
    # 3. Create 'Projects' Bin under Master to hold all generated Timelines
    projects_bin = media_pool.AddSubFolder(root_folder, "Projects")
    
    # Mirror the physical grouping, including camera/day levels, without flattening cards.
    bins = {(): root_folder}
    failures = []
    for group_index, group in enumerate(plan['groups']):
        checkpoint(15 + group_index / max(1, len(plan['groups'])) * 75,
                   f"Importing {group_index + 1}/{len(plan['groups'])}: {group['folder']}")
        parts = tuple(group['parts']) or ('Loose Media',)
        parent = root_folder
        for depth in range(1, len(parts) + 1):
            key = parts[:depth]
            if key not in bins:
                bins[key] = media_pool.AddSubFolder(parent, parts[depth - 1])
            parent = bins[key]
            if not parent:
                return False, f"Could not create bin for {group['folder']}. Partial project retained."
        media_pool.SetCurrentFolder(parent)
        imported_items = media_pool.ImportMedia(group['files']) or []
        if isinstance(imported_items, dict):
            imported_items = list(imported_items.values())
        if len(imported_items) != len(group['files']):
            failures.append(f"{group['folder']}: imported {len(imported_items)}/{len(group['files'])} files")
        if imported_items:
            if not projects_bin:
                return False, 'Could not create Projects bin. Partial project retained.'
            media_pool.SetCurrentFolder(projects_bin)
            timeline = media_pool.CreateTimelineFromClips(group['timeline'], imported_items)
            if timeline:
                created_timelines.append(group['timeline'])
            else:
                failures.append(f"Could not create {group['timeline']}")
    if plan['audio_files']:
        music_bin = media_pool.AddSubFolder(root_folder, 'Audio & Music')
        if not music_bin:
            failures.append('Could not create Audio & Music bin')
        else:
            media_pool.SetCurrentFolder(music_bin)
            imported_audio = media_pool.ImportMedia(plan['audio_files']) or []
            if len(imported_audio) != len(plan['audio_files']):
                failures.append(f"Audio: imported {len(imported_audio)}/{len(plan['audio_files'])} files")

    pm.SaveProject()
    if failures:
        return False, f"Project '{target_project_name}' partially completed with {len(created_timelines)} timelines. " + '; '.join(failures)
    if not created_timelines:
        return False, f"Project '{target_project_name}' was created, but no supported footage was imported. Check media folders and codecs."
    return True, f"✓ Successfully created project '{target_project_name}' with {len(created_timelines)} Card Timelines inside Projects Bin: {', '.join(created_timelines)}"


def resolve_variables(text: str, params: Dict[str, Any]) -> str:
    """Replace {variable} placeholders with actual values"""
    result = text
    for key, value in params.items():
        result = result.replace(f"{{{key}}}", str(value))
    
    # Handle date shortcuts
    today = datetime.now()
    result = result.replace("{today}", today.strftime("%Y-%m-%d"))
    result = result.replace("{date}", today.strftime("%Y-%m-%d"))
    result = result.replace("{time}", today.strftime("%H%M%S"))
    result = result.replace("{year}", str(today.year))
    result = result.replace("{month}", today.strftime("%m"))
    result = result.replace("{day}", today.strftime("%d"))
    
    return result


def create_folder_structure(parent_dir: str, structure: List[Dict], params: Dict[str, Any], 
                           placeholders: Dict[str, str] = None) -> Tuple[bool, str, str]:
    """
    Create folder structure from template definition (Post Haste style)
    Supports: folders, files, loops, and variable substitution
    """
    if not parent_dir or not os.path.exists(parent_dir):
        return False, f"Invalid parent folder path: '{parent_dir}'", ""
    
    try:
        # Process the structure recursively
        created_path = _process_structure_element(parent_dir, structure, params, 0)
        
        # Create placeholder files
        if placeholders:
            for filename, content in placeholders.items():
                resolved_filename = resolve_variables(filename, params)
                file_path = os.path.join(created_path, resolved_filename)
                
                # Ensure parent directory exists
                if os.path.dirname(file_path):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Create file with content (resolve variables in content too)
                resolved_content = resolve_variables(content, params)
                with open(file_path, 'w') as f:
                    f.write(resolved_content)
        
        return True, f"✓ Template structure created successfully", created_path
    
    except Exception as e:
        logger.error(f"Error creating folder structure: {e}")
        return False, f"Failed to create structure: {str(e)}", ""


def _process_structure_element(parent_path: str, elements: List[Dict], params: Dict[str, Any], depth: int = 0) -> str:
    """Recursively process structure elements"""
    created_root = None
    
    for element in elements:
        elem_type = element.get("type", "folder")
        name = resolve_variables(element.get("name", ""), params)
        
        if elem_type == "folder":
            folder_path = os.path.join(parent_path, name)
            os.makedirs(folder_path, exist_ok=True)
            
            if not created_root:
                created_root = folder_path
            
            # Process children
            children = element.get("children", [])
            if children:
                _process_structure_element(folder_path, children, params, depth + 1)
        
        elif elem_type == "file":
            file_path = os.path.join(parent_path, name)
            if os.path.dirname(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Create empty file or with placeholder content
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    if element.get("placeholder"):
                        f.write(element.get("content", ""))
            
            if not created_root:
                created_root = parent_path
        
        elif elem_type == "loop":
            # Handle loop constructs (e.g., Camera 1, Camera 2, Camera 3)
            var_name = element.get("var", "i")
            start = int(resolve_variables(str(element.get("start", 1)), params))
            end_str = resolve_variables(str(element.get("end", 1)), params)
            
            # Try to parse end as number
            try:
                end = int(end_str)
            except ValueError:
                end = start  # Default if can't parse
            
            step = element.get("step", 1)
            template = element.get("template", {})
            
            for i in range(start, end + 1, step):
                loop_params = params.copy()
                loop_params[var_name] = i
                loop_params[f"{var_name}_padded"] = str(i).zfill(2)
                
                # Process template with loop variables
                _process_structure_element(parent_path, [template], loop_params, depth + 1)
    
    return created_root or parent_path


def create_master_folder_from_template(template_id: int, parent_dir: str, 
                                       param_values: Dict[str, Any]) -> Tuple[bool, str, str]:
    """
    Create master folder using a template from database
    Returns (success, message, folder_path)
    """
    # Get template from database
    template = template_db.get_template(template_id)
    
    if not template:
        return False, f"Template ID {template_id} not found", ""
    
    # Merge default parameter values with provided values
    all_params = {}
    for param in template["parameters"]:
        default = param.get("default", "")
        # Handle special defaults
        if default == "{today}" or default == "{date}":
            default = datetime.now().strftime("%Y-%m-%d")
        all_params[param["name"]] = default
    
    # Override with provided values
    all_params.update(param_values)
    
    # Validate required parameters
    for param in template["parameters"]:
        if param.get("required") and not all_params.get(param["name"]):
            return False, f"Required parameter '{param['name']}' is missing", ""
    
    # Create the structure
    return create_folder_structure(
        parent_dir, 
        template["structure"], 
        all_params,
        template.get("placeholders", {})
    )


def get_builtin_templates() -> List[Dict[str, Any]]:
    """Get list of built-in templates"""
    return [
        {
            "id": "social_media",
            "name": "Social Media",
            "description": "Standard social media project structure",
            "category": "Social",
            "parameters": [
                {"name": "project", "type": "text", "required": True, "default": ""},
                {"name": "client", "type": "text", "required": False, "default": ""},
                {"name": "date", "type": "date", "required": True, "default": "{today}"},
                {"name": "platform", "type": "select", "options": ["Instagram", "TikTok", "YouTube", "All"], "default": "All"}
            ],
            "structure": [
                {"type": "folder", "name": "{date}_{client}_{project}", "children": [
                    {"type": "folder", "name": "Raw Footages", "children": [
                        {"type": "folder", "name": "Card 01"},
                        {"type": "folder", "name": "Card 02"}
                    ]},
                    {"type": "folder", "name": "Davinci Resolve Database"},
                    {"type": "folder", "name": "Logos & Branding"},
                    {"type": "folder", "name": "Audio & Music"},
                    {"type": "folder", "name": "Graphics & Assets"},
                    {"type": "folder", "name": "Exports"},
                    {"type": "file", "name": "shot_list.txt", "placeholder": True, "content": "Scene\tDescription\tDuration\n1\t\t\n2\t\t\n"}
                ]}
            ],
            "placeholders": {
                "shot_list.txt": "Scene\tDescription\tDuration\n1\t\t\n2\t\t\n"
            }
        },
        {
            "id": "commercial",
            "name": "Commercial Production",
            "description": "Multi-camera commercial project structure",
            "category": "Commercial",
            "parameters": [
                {"name": "project", "type": "text", "required": True, "default": ""},
                {"name": "client", "type": "text", "required": True, "default": ""},
                {"name": "date", "type": "date", "required": True, "default": "{today}"},
                {"name": "camera_count", "type": "number", "required": False, "default": "2", "min": 1, "max": 10}
            ],
            "structure": [
                {"type": "folder", "name": "{date}_{client}_{project}", "children": [
                    {"type": "folder", "name": "Raw Footages", "children": [
                        {"type": "loop", "var": "camera", "start": 1, "end": "{camera_count}",
                         "template": {"type": "folder", "name": "Camera {camera}"}}
                    ]},
                    {"type": "folder", "name": "Davinci Resolve Database"},
                    {"type": "folder", "name": "Logos & Branding"},
                    {"type": "folder", "name": "Audio Voiceover"},
                    {"type": "folder", "name": "Motion Graphics"},
                    {"type": "folder", "name": "Photoshop"},
                    {"type": "folder", "name": "Client Approvals & Exports"},
                    {"type": "folder", "name": "Documents"}
                ]}
            ],
            "placeholders": {}
        },
        {
            "id": "film_production",
            "name": "Film Production",
            "description": "Full film production workflow structure",
            "category": "Film",
            "parameters": [
                {"name": "project", "type": "text", "required": True, "default": ""},
                {"name": "director", "type": "text", "required": False, "default": ""},
                {"name": "date", "type": "date", "required": True, "default": "{today}"},
                {"name": "card_count", "type": "number", "required": False, "default": "4", "min": 1, "max": 20}
            ],
            "structure": [
                {"type": "folder", "name": "{date}_{project}", "children": [
                    {"type": "folder", "name": "01_Raw", "children": [
                        {"type": "loop", "var": "card", "start": 1, "end": "{card_count}",
                         "template": {"type": "folder", "name": "Card {card_padded}"}}
                    ]},
                    {"type": "folder", "name": "02_Davinci"},
                    {"type": "folder", "name": "03_Audio"},
                    {"type": "folder", "name": "04_Graphics"},
                    {"type": "folder", "name": "05_Exports"},
                    {"type": "folder", "name": "06_Production_Docs", "children": [
                        {"type": "file", "name": "script.pdf", "placeholder": True},
                        {"type": "file", "name": "call_sheet.pdf", "placeholder": True},
                        {"type": "file", "name": "release_forms.pdf", "placeholder": True}
                    ]}
                ]}
            ],
            "placeholders": {
                "script.pdf": "",
                "call_sheet.pdf": "",
                "release_forms.pdf": ""
            }
        }
    ]

