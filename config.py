"""
Clip Assassin Configuration Management
Supports environment variables, .env files, and default values
"""
import os
from pathlib import Path
from typing import Optional
import platform

class Config:
    """Application configuration with environment variable support"""
    
    # Base directories
    BASE_DIR = Path(getattr(__import__("sys"), "_MEIPASS", Path(__file__).parent))
    FRONTEND_DIR = BASE_DIR / "frontend" / "dist"
    TEMPLATES_DIR = BASE_DIR / "templates"
    PRESETS_DIR = BASE_DIR / "presets"
    
    # Database
    DB_PATH = os.getenv("CLIP_ASSASSIN_DB_PATH")
    if not DB_PATH:
        app_name = "ClipAssassin"
        if platform.system() == "Windows":
            base = os.environ.get('APPDATA', Path.home())
            data_dir = Path(base) / app_name
        elif platform.system() == "Darwin":
            data_dir = Path.home() / 'Library' / 'Application Support' / app_name
        else:
            data_dir = Path.home() / f".{app_name.lower()}"
        data_dir.mkdir(parents=True, exist_ok=True)
        DB_PATH = str(data_dir / "settings.db")
    
    # API Settings
    API_HOST = os.getenv("CLIP_ASSASSIN_HOST", "127.0.0.1")
    API_PORT = int(os.getenv("CLIP_ASSASSIN_PORT", "8000"))
    DEBUG = os.getenv("CLIP_ASSASSIN_DEBUG", "false").lower() == "true"
    
    # CORS Origins
    CORS_ORIGINS = os.getenv(
        "CLIP_ASSASSIN_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000"
    ).split(",")
    
    # Async Task Queue (Celery/Redis)
    REDIS_URL = os.getenv("CLIP_ASSASSIN_REDIS_URL", "redis://localhost:6379/0")
    TASK_QUEUE_ENABLED = os.getenv("CLIP_ASSASSIN_TASK_QUEUE", "false").lower() == "true"
    
    # AI Integration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # tiny, base, small, medium, large
    AI_ENABLED = bool(OPENAI_API_KEY) or os.getenv("WHISPER_MODEL")
    
    # Logging
    LOG_LEVEL = os.getenv("CLIP_ASSASSIN_LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv(
        "CLIP_ASSASSIN_LOG_FORMAT",
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    LOG_FILE = os.getenv("CLIP_ASSASSIN_LOG_FILE")
    
    # Plugin System
    PLUGIN_DIR = os.getenv("CLIP_ASSASSIN_PLUGIN_DIR", str(BASE_DIR / "plugins"))
    PLUGINS_ENABLED = os.getenv("CLIP_ASSASSIN_PLUGINS", "false").lower() == "true"
    
    # WebSocket
    WEBSOCKET_ENABLED = os.getenv("CLIP_ASSASSIN_WEBSOCKET", "true").lower() == "true"
    
    # Render Settings
    MAX_CONCURRENT_RENDERS = int(os.getenv("CLIP_ASSASSIN_MAX_RENDERS", "3"))
    RENDER_TIMEOUT = int(os.getenv("CLIP_ASSASSIN_RENDER_TIMEOUT", "3600"))  # 1 hour
    
    # Security
    SECRET_KEY = os.getenv("CLIP_ASSASSIN_SECRET_KEY", "dev-secret-key-change-in-production")
    ALLOWED_PATHS = os.getenv(
        "CLIP_ASSASSIN_ALLOWED_PATHS",
        "/Users,/home,/Volumes,/mnt"
    ).split(",")
    
    @classmethod
    def get_allowed_paths(cls):
        """Get list of allowed base paths for file operations"""
        return [Path(p.strip()) for p in cls.ALLOWED_PATHS if p.strip()]
    
    @classmethod
    def is_path_allowed(cls, path: str) -> bool:
        """Check if a path is within allowed directories"""
        try:
            full_path = Path(path).resolve()
            return any(full_path.is_relative_to(allowed.resolve()) for allowed in cls.get_allowed_paths())
        except Exception:
            return False
    
    @classmethod
    def validate_path(cls, path: str) -> tuple[bool, str]:
        """Validate a path for security"""
        if ".." in path:
            return False, "Path traversal detected"
        
        if not cls.is_path_allowed(path):
            return False, f"Path must be within allowed directories: {cls.ALLOWED_PATHS}"
        
        return True, "OK"
    
    def __repr__(self):
        return f"Config(API_HOST={self.API_HOST}, API_PORT={self.API_PORT}, DEBUG={self.DEBUG})"


# Global config instance
config = Config()
