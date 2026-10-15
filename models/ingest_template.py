"""
Ingest Template Model - Post Haste Style
Supports dynamic variables, loops, custom parameters, and validation rules
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import json


class ParameterType(str):
    TEXT = "text"
    DATE = "date"
    NUMBER = "number"
    SELECT = "select"
    BOOLEAN = "boolean"


class TemplateParameter(BaseModel):
    """Defines a custom parameter for template instantiation"""
    name: str
    label: str
    type: str = "text"  # "text", "date", "number", "select", "boolean"
    default: Optional[str] = None
    required: bool = True
    validation_pattern: Optional[str] = None  # Regex pattern
    options: Optional[List[str]] = None  # For SELECT type
    min_value: Optional[float] = None  # For NUMBER type
    max_value: Optional[float] = None  # For NUMBER type
    date_format: Optional[str] = "%Y-%m-%d"  # For DATE type
    
    model_config = {"arbitrary_types_allowed": True}


class FolderNode(BaseModel):
    """Represents a folder or file in the template structure"""
    name: str
    type: str = "folder"  # "folder" or "file"
    children: Optional[List['FolderNode']] = None
    loop_variable: Optional[str] = None  # e.g., "camera" for Camera 1..N
    loop_index: Optional[str] = None  # Optional index name when loop_variable is a count parameter
    loop_start: int = 1
    loop_end: Optional[int] = None  # If None, determined by parameter
    placeholder_content: Optional[str] = None  # For files
    condition: Optional[str] = None  # Conditional creation based on parameter
    
    model_config = {"arbitrary_types_allowed": True}


class IngestTemplate(BaseModel):
    """Complete ingest template definition"""
    id: str
    name: str
    description: str
    version: str = "1.0"
    author: str = "User"
    created_at: str = ""
    updated_at: str = ""
    
    # Template structure
    parameters: List[TemplateParameter] = []
    structure: List[FolderNode] = []
    
    # Built-in variables (always available)
    builtin_params: Dict[str, Any] = {
        "project": {"type": "text", "required": True, "label": "Project Name"},
        "client": {"type": "text", "required": False, "label": "Client Name"},
        "date": {"type": "date", "required": True, "label": "Date", "default_format": "%Y-%m-%d"},
        "operator": {"type": "text", "required": False, "label": "Operator Name"}
    }
    
    # Metadata
    tags: List[str] = []
    category: str = "General"  # Social, Commercial, Film, etc.
    thumbnail: Optional[str] = None
    
    model_config = {"arbitrary_types_allowed": True}
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
    
    def to_json(self) -> str:
        return self.model_dump_json(indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'IngestTemplate':
        import json as json_module
        data = json_module.loads(json_str)
        # Handle datetime fields
        if not data.get('created_at'):
            from datetime import datetime
            data['created_at'] = datetime.now().isoformat()
        if not data.get('updated_at'):
            from datetime import datetime
            data['updated_at'] = datetime.now().isoformat()
        return cls(**data)


# Update forward references
FolderNode.model_rebuild()
