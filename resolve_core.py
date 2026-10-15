"""
DaVinci Resolve API Integration for Clip Assassin
Handles timeline operations and clip cutting
"""

import sys
import os

# Add Resolve API to Python path
resolve_api_paths = [
    r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules",
    r"/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules",
    r"/opt/resolve/Developer/Scripting/Modules"
]

for path in resolve_api_paths:
    if os.path.exists(path) and path not in sys.path:
        sys.path.append(path)

# Set environment variables for Resolve Scripting API
if sys.platform == "darwin":
    os.environ["RESOLVE_SCRIPT_API"] = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
    so_paths = [
        "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so",
        "/Applications/DaVinci Resolve Studio/DaVinci Resolve Studio.app/Contents/Libraries/Fusion/fusionscript.so"
    ]
    for p in so_paths:
        if os.path.exists(p):
            os.environ["RESOLVE_SCRIPT_LIB"] = p
            break
elif sys.platform == "win32":
    os.environ["RESOLVE_SCRIPT_API"] = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
    os.environ["RESOLVE_SCRIPT_LIB"] = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"

from time_parser import parse_timecodes, format_seconds
from modules import magic_tools, export_tools, timeline_tools, badwords_tools, utility_tools, audio_tools

def get_executable_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

class ResolveConnection:
    """Handles connection to DaVinci Resolve"""

    def __init__(self):
        self.resolve = None
        self.project = None
        self.media_pool = None
        self.project_manager = None
        self.connection_message = "Not connected"

    def is_resolve_process_running(self):
        try:
            import subprocess
            if sys.platform == "darwin":
                output = subprocess.check_output(["pgrep", "-i", "resolve"]).decode()
                return len(output.strip()) > 0
            elif sys.platform == "win32":
                output = subprocess.check_output(["tasklist"], creationflags=0x08000000).decode()
                return "Resolve.exe" in output
        except Exception:
            return False
        return False

    def is_fuscript_running(self):
        try:
            import subprocess
            if sys.platform == "darwin":
                output = subprocess.check_output(["pgrep", "-i", "fuscript"]).decode()
                return len(output.strip()) > 0
            elif sys.platform == "win32":
                output = subprocess.check_output(["tasklist"], creationflags=0x08000000).decode()
                return "fuscript.exe" in output
        except Exception:
            return False
        return False

    def connect(self):
        """
        Establish connection to DaVinci Resolve

        Returns:
            tuple: (success: bool, message: str)
        """
        self.resolve = self.project = self.media_pool = self.project_manager = None
        try:
            # Import DaVinci Resolve script module
            try:
                import DaVinciResolveScript as dvr
            except ImportError:
                return False, "DaVinci Resolve Python API module not found. Please ensure DaVinci Resolve is installed."

            # Get Resolve instance
            self.resolve = dvr.scriptapp("Resolve")
            if not self.resolve:
                return False, ("Cannot reach DaVinci Resolve. Open Resolve Studio and enable "
                    "Preferences > System > General > External scripting using: Local. "
                    "Close open dialogs, then reconnect.")

            # Get project manager
            self.project_manager = self.resolve.GetProjectManager()
            if not self.project_manager:
                return False, "Could not access Project Manager in Resolve. Please close any open dialogs inside Resolve."

            # Get current project (if any)
            self.project = self.project_manager.GetCurrentProject()
            if self.project:
                self.media_pool = self.project.GetMediaPool()
                self.connection_message = f"Connected to project: {self.project.GetName()}"
                return True, self.connection_message
            else:
                self.media_pool = None
                self.connection_message = "Connected to DaVinci Resolve (Project Manager ready)"
                return True, self.connection_message

        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def refresh(self):
        """Refresh live project references, including after a project switch or closure."""
        if not self.resolve:
            success, self.connection_message = self.connect()
            return success
        try:
            manager = self.resolve.GetProjectManager()
            if not manager:
                raise RuntimeError("Resolve is unavailable")
            self.project_manager = manager
            self.project = manager.GetCurrentProject()
            self.media_pool = self.project.GetMediaPool() if self.project else None
            self.connection_message = (f"Connected to project: {self.project.GetName()}" if self.project
                                       else "Connected to DaVinci Resolve (Project Manager ready)")
            return True
        except Exception:
            self.resolve = self.project = self.media_pool = self.project_manager = None
            self.connection_message = "Resolve disconnected. Open Resolve and reconnect."
            return False

    def unique_timeline_name(self, base):
        name, count = base, 2
        while self._timeline_exists(name):
            name = f"{base} ({count})"
            count += 1
        return name

    def get_selected_clip(self):
        """Get the currently selected clip in Media Pool, if any"""
        if not self.media_pool:
            return None
        try:
            selected = self.media_pool.GetSelectedClips()
            if selected:
                if isinstance(selected, dict):
                    return list(selected.values())[0]
                elif isinstance(selected, list):
                    return selected[0]
        except Exception:
            pass
        return None

    def get_first_video_clip(self):
        """
        Find the first video clip in the media pool

        Returns:
            MediaPoolItem or None
        """
        if not self.media_pool:
            return None

        root_folder = self.media_pool.GetRootFolder()
        return self._find_video_clip_recursive(root_folder)

    def get_clip_framerate(self, clip):
        """
        Get framerate from a MediaPoolItem

        Args:
            clip: MediaPoolItem

        Returns:
            float: Framerate (e.g., 59.94, 29.97, 30, 24, etc.) or 30.0 as fallback
        """
        try:
            clip_property = clip.GetClipProperty()
            fps = float(clip_property.get("FPS", 30.0))
            return fps
        except Exception:
            return 30.0  # Fallback to 30fps

    def _find_video_clip_recursive(self, folder):
        """Recursively search for video clip in folders"""
        # Check clips in current folder
        clips = folder.GetClipList()
        for clip in clips:
            # Check if it's a video clip (has video track)
            clip_property = clip.GetClipProperty()
            if clip_property and clip_property.get("Video Codec"):
                return clip

        # Search subfolders
        subfolders = folder.GetSubFolderList()
        for subfolder in subfolders:
            found = self._find_video_clip_recursive(subfolder)
            if found:
                return found

        return None

    def get_clip_by_name(self, target_name):
        """Find a clip by its exact name in the media pool"""
        if not self.media_pool:
            return None
        root_folder = self.media_pool.GetRootFolder()
        return self._find_clip_by_name_recursive(root_folder, target_name)
        
    def _find_clip_by_name_recursive(self, folder, target_name):
        clips = folder.GetClipList()
        for clip in clips:
            if clip.GetName() == target_name:
                return clip
                
        for subfolder in folder.GetSubFolderList():
            found = self._find_clip_by_name_recursive(subfolder, target_name)
            if found:
                return found
        return None

    def cut_video(self, timecodes_text, reverse_mode=False, target_clip_name=""):
        return timeline_tools.cut_video(self, timecodes_text, reverse_mode, target_clip_name)

    def parse_clip_numbers(self, text):
        """
        Parse clip number input like "1, 3, 5, 7-10, 15" into a sorted list of unique integers.

        Supported formats:
        - Single numbers: 1, 3, 5
        - Ranges: 7-10 (expands to 7, 8, 9, 10)
        - Mixed: 1, 3, 7-10, 15

        Args:
            text: String with clip numbers

        Returns:
            tuple: (sorted list of clip numbers, list of error strings)
        """
        numbers = set()
        errors = []

        # Replace different dash types for ranges inside tokens only
        text = text.replace('\u2013', '-').replace('\u2014', '-')

        # Split by comma or whitespace
        tokens = [t.strip() for t in text.replace(',', ' ').split() if t.strip()]

        for token in tokens:
            if '-' in token:
                parts = token.split('-')
                if len(parts) == 2:
                    try:
                        start = int(parts[0])
                        end = int(parts[1])
                        if start < 1 or end < 1:
                            errors.append(f"'{token}' — clip numbers must be 1 or greater")
                            continue
                        if start > end:
                            errors.append(f"'{token}' — range start is greater than end")
                            continue
                        for n in range(start, end + 1):
                            numbers.add(n)
                    except ValueError:
                        errors.append(f"'{token}' — invalid range format")
                else:
                    errors.append(f"'{token}' — invalid format")
            else:
                try:
                    num = int(token)
                    if num < 1:
                        errors.append(f"'{token}' — clip number must be 1 or greater")
                        continue
                    numbers.add(num)
                except ValueError:
                    errors.append(f"'{token}' — not a valid number")

        return sorted(numbers), errors

    def pick_clips_from_timeline(self, names_text):
        return timeline_tools.pick_clips_from_timeline(self, names_text)

    def markers_to_timeline(self, target_color):
        return timeline_tools.markers_to_timeline(self, target_color)

    def batch_render(self, timelines, preset_name, target_dir):
        return export_tools.batch_render(self, timelines, preset_name, target_dir)

    def extract_thumbnails(self, mode, target_dir):
        return export_tools.extract_thumbnails(self, mode, target_dir)

    def merge_timelines(self, names_text):
        if not self.project: self.connect()
        if not self.project: return False, "DaVinci Resolve not connected."
        return timeline_tools.merge_timelines(self, names_text)

    def generate_youtube_chapters(self):
        return export_tools.generate_youtube_chapters(self)

    def filter_by_flag(self, target_color):
        return timeline_tools.filter_by_flag(self, target_color)

    def apply_watermark_track(self, image_path):
        return timeline_tools.apply_watermark_track(self, image_path)

    def scan_badwords_markers(self):
        return badwords_tools.scan_markers(self)

    def clean_badwords_timeline(self, colors_to_remove):
        return badwords_tools.clean_timeline(self, colors_to_remove)

    # --- Utility Tools ---
    def create_snapshot(self):
        return utility_tools.create_snapshot(self)

    def batch_rename_clips(self, prefix, start_number=1, scope="timeline"):
        return utility_tools.batch_rename_clips(self, prefix, start_number, scope)

    def get_project_stats_detail(self):
        return utility_tools.get_project_stats(self)

    def add_adjustment_layer(self):
        return magic_tools.add_adjustment_layer(self)

    def export_shotlist_doc(self, format, output_path, template_path=""):
        return export_tools.export_shotlist_doc(self, format, output_path, template_path)

    # --- Audio & Edit Tools ---
    def apply_jl_cuts(self, cut_type="j", overlap_frames=10):
        return audio_tools.apply_jl_cuts(self, cut_type, overlap_frames)

    def get_render_status(self):
        return audio_tools.get_render_status(self)

    def detect_silence(self, threshold_db=-40, min_silence_ms=500, padding_ms=100):
        return audio_tools.detect_silence(self, threshold_db, min_silence_ms, padding_ms)

    def export_csv_data(self, output_path):
        return export_tools.export_csv_data(self, output_path)

    def _timeline_exists(self, name):
        """Check if a timeline with given name exists"""
        timeline_count = self.project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            timeline = self.project.GetTimelineByIndex(i)
            if timeline and timeline.GetName() == name:
                return True
        return False

    def get_project_info(self):
        """Get current project information"""
        if not self.project:
            return "No project connected"

        info = f"Project: {self.project.GetName()}\n"
        info += f"Timeline Count: {self.project.GetTimelineCount()}\n"

        current_timeline = self.project.GetCurrentTimeline()
        if current_timeline:
            info += f"Current Timeline: {current_timeline.GetName()}\n"

        return info


    def get_timeline_stats(self):
        """Get live statistics for the current timeline"""
        if not self.project:
            return {"success": False, "message": "No project connected"}
            
        timeline = self.project.GetCurrentTimeline()
        if not timeline:
            return {"success": False, "message": "No active timeline"}
            
        try:
            name = timeline.GetName()
            fps = str(timeline.GetSetting("timelineFrameRate") or "30")
            
            # Count video clips on track 1
            clip_count = 0
            items = timeline.GetItemListInTrack("video", 1)
            if items:
                clip_count = len(items)
                
            start_tc = timeline.GetStartTimecode()
            
            return {
                "success": True,
                "name": name,
                "fps": fps,
                "clips": clip_count,
                "timecode": timeline.GetCurrentTimecode() or start_tc
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def organize_media_pool(self):
        return magic_tools.organize_media_pool(self)

    def create_social_timeline(self, format="9:16"):
        return magic_tools.create_social_timeline(self, format)

    def auto_sync_audio(self):
        return magic_tools.auto_sync_audio(self)
            
    def add_quick_title(self, text="New Title"):
        return magic_tools.add_quick_title(self, text)

    def generate_subtitles(self):
        if not self.project or not self.project.GetCurrentTimeline():
            return False, "Open a timeline with audio first."
        try:
            ok = self.project.GetCurrentTimeline().CreateSubtitlesFromAudio()
            return bool(ok), "Subtitles generated." if ok else "Subtitle generation failed. This requires Resolve Studio and supported audio."
        except Exception as exc:
            return False, f"Subtitle generation unavailable: {exc}"

    def upload_to_youtube(self):
        return False, "YouTube upload requires an OAuth connection, which this app does not have. Export the video and upload it in YouTube Studio."

    def asset_directory(self):
        import db
        path = os.path.join(db.data_dir, "templates")
        os.makedirs(path, exist_ok=True)
        return path

    def get_templates(self):
        """List templates from both built-in and user directories"""
        try:
            files = set()
            
            # 1. Bundled (Built-in) templates
            if getattr(sys, 'frozen', False):
                bundled_dir = os.path.join(sys._MEIPASS, "templates")
                if os.path.exists(bundled_dir):
                    for f in os.listdir(bundled_dir):
                        if not f.startswith('.'): files.add(f)
                        
            # 2. User-added templates (next to executable or script)
            user_dir = self.asset_directory()
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)
            for directory in {user_dir, os.path.join(get_executable_dir(), "templates")}:
                if os.path.isdir(directory):
                    for f in os.listdir(directory):
                        if not f.startswith('.') and os.path.isfile(os.path.join(directory, f)):
                            files.add(f)
                
            invalid = []
            for name in files:
                candidates = [os.path.join(user_dir, name), os.path.join(get_executable_dir(), "templates", name)]
                existing = next((p for p in candidates if os.path.isfile(p)), None)
                if existing and os.path.getsize(existing) == 0:
                    invalid.append(name)
            return {"success": True, "templates": sorted(files - set(invalid)), "invalid_assets": invalid}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def import_template(self, template_name):
        """Import a template file into the Media Pool"""
        if os.path.basename(template_name) != template_name or "\\" in template_name:
            return False, "Invalid template filename"
        try:
            template_path = None
            
            # Check user directory first (allows overriding built-in templates)
            user_path = os.path.join(self.asset_directory(), template_name)
            if not os.path.isfile(user_path):
                user_path = os.path.join(get_executable_dir(), "templates", template_name)
            if os.path.exists(user_path):
                template_path = user_path
            elif getattr(sys, 'frozen', False):
                bundled_path = os.path.join(sys._MEIPASS, "templates", template_name)
                if os.path.exists(bundled_path):
                    template_path = bundled_path
                    
            if not template_path:
                return False, f"Template file not found: {template_name}"
                
            if os.path.getsize(template_path) == 0:
                return False, "This bundled template file is empty. Replace it with a valid asset."
            if template_path.lower().endswith(".drfx"):
                import subprocess
                if sys.platform == "darwin":
                    subprocess.run(["open", template_path], check=True)
                elif sys.platform == "win32":
                    os.startfile(template_path)
                else:
                    subprocess.run(["xdg-open", template_path], check=True)
                return True, "Opened the Resolve template installer. Complete installation in Resolve; find it in the Effects Library."
            if not self.media_pool:
                return False, "Connect to a Resolve project before importing media."
            if template_path.lower().endswith(".setting"):
                return False, "Fusion .setting files must be loaded in a Fusion composition. Use a .drfx package for installation."
            items = self.media_pool.ImportMedia([template_path])
            
            if not items:
                return False, f"Failed to import {template_name}. Is the file format supported?"
                
            return True, f"Successfully imported '{template_name}' to Media Pool."
        except Exception as e:
            return False, f"Error importing template: {e}"

    def get_global_context(self):
        """Get the current project, list of all timelines, and active timeline"""
        if not self.project:
            return {"success": False, "message": "No project connected"}
            
        try:
            project_name = self.project.GetName()
            timelines = []
            
            count = self.project.GetTimelineCount()
            for i in range(1, count + 1):
                t = self.project.GetTimelineByIndex(i)
                if t:
                    timelines.append(t.GetName())
                    
            current = self.project.GetCurrentTimeline()
            current_name = current.GetName() if current else ""
            
            return {
                "success": True, 
                "project": project_name,
                "timelines": timelines,
                "current_timeline": current_name
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def set_active_timeline(self, timeline_name):
        """Switch to a specific timeline by name"""
        if not self.project:
            return False, "No project connected"
            
        try:
            count = self.project.GetTimelineCount()
            for i in range(1, count + 1):
                t = self.project.GetTimelineByIndex(i)
                if t and t.GetName() == timeline_name:
                    self.project.SetCurrentTimeline(t)
                    return True, f"Switched to '{timeline_name}'"
            return False, f"Timeline '{timeline_name}' not found."
        except Exception as e:
            return False, f"Error switching timeline: {e}"

    def run_master_ingest(self, master_folder_path: str):
        """Automate project creation, Media Pool bin setup, and Timeline generation from Master Folder"""
        from modules import master_ingest
        return master_ingest.process_master_ingest(self, master_folder_path)

    def run_create_master_folder(self, parent_dir: str, project_name: str, client_name: str = "", project_type: str = "Standard Video", custom_date: str = ""):
        """Create a Post Haste style standardized Master Folder template on disk"""
        from modules import master_ingest
        return master_ingest.create_master_folder_structure(parent_dir, project_name, client_name, project_type, custom_date)

# Testing
if __name__ == "__main__":
    print("Testing Resolve Connection...")
    print("-" * 50)

    rc = ResolveConnection()
    success, msg = rc.connect()

    if success:
        print(f"✓ {msg}")
        print()
        print(rc.get_project_info())
        print()

        # Try to find first clip
        clip = rc.get_first_video_clip()
        if clip:
            print(f"✓ Found video clip: {clip.GetName()}")
            props = clip.GetClipProperty()
            print(f"  Duration: {props.get('Frames')} frames")
            print(f"  FPS: {props.get('FPS')}")
            print(f"  Resolution: {props.get('Resolution')}")
        else:
            print("✗ No video clip found in Media Pool")
    else:
        print(f"✗ {msg}")
