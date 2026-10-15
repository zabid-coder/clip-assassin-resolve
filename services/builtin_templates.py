"""
Built-in Professional Templates - Post Haste Style
Pre-configured templates for Social Media, Commercial, and Film Production
"""
from models.ingest_template import (
    IngestTemplate, TemplateParameter, FolderNode, ParameterType
)


def create_social_media_template() -> IngestTemplate:
    """Social Media Content Template"""
    return IngestTemplate(
        id="social-media-v1",
        name="Social Media Content",
        description="Optimized for Instagram, TikTok, YouTube Shorts production",
        version="1.0",
        author="Clip Assassin",
        category="Social Media",
        tags=["social", "instagram", "tiktok", "youtube", "shorts"],
        
        parameters=[
            TemplateParameter(
                name="platform",
                label="Target Platform",
                type=ParameterType.SELECT,
                options=["Instagram Reels", "TikTok", "YouTube Shorts", "All Platforms"],
                default="All Platforms",
                required=True
            ),
            TemplateParameter(
                name="content_type",
                label="Content Type",
                type=ParameterType.SELECT,
                options=["Tutorial", "Behind Scenes", "Promo", "Vlog", "Challenge"],
                default="Tutorial",
                required=True
            ),
            TemplateParameter(
                name="shoot_days",
                label="Number of Shoot Days",
                type=ParameterType.NUMBER,
                min_value=1,
                max_value=30,
                default="1",
                required=False
            )
        ],
        
        structure=[
            FolderNode(
                name="{project}",
                type="folder",
                children=[
                    FolderNode(
                        name="01_Pre_Production",
                        type="folder",
                        children=[
                            FolderNode(name="Scripts", type="folder"),
                            FolderNode(name="Storyboards", type="folder"),
                            FolderNode(
                                name="Shot_List_{content_type}.csv",
                                type="file",
                                placeholder_content="Shot Number,Description,Duration,Notes\n1,Opening hook,5s,\n2,Main content,30s,\n3,Call to action,5s,"
                            ),
                            FolderNode(name="References", type="folder")
                        ]
                    ),
                    FolderNode(
                        name="02_Footage",
                        type="folder",
                        children=[
                            FolderNode(
                                name="Day_{day}",
                                type="folder",
                                loop_variable="shoot_days",
                                loop_index="day",
                                loop_start=1,
                                children=[
                                    FolderNode(name="A_Cam", type="folder"),
                                    FolderNode(name="B_Cam", type="folder"),
                                    FolderNode(name="Audio", type="folder"),
                                    FolderNode(name="Selects", type="folder")
                                ]
                            )
                        ]
                    ),
                    FolderNode(
                        name="03_Audio",
                        type="folder",
                        children=[
                            FolderNode(name="Music", type="folder"),
                            FolderNode(name="SFX", type="folder"),
                            FolderNode(name="Voiceover", type="folder")
                        ]
                    ),
                    FolderNode(
                        name="04_Graphics",
                        type="folder",
                        children=[
                            FolderNode(name="Logos", type="folder"),
                            FolderNode(name="Lower_Thirds", type="folder"),
                            FolderNode(name="Templates", type="folder")
                        ]
                    ),
                    FolderNode(
                        name="05_Edits",
                        type="folder",
                        children=[
                            FolderNode(name="Rough_Cuts", type="folder"),
                            FolderNode(name="Fine_Cuts", type="folder"),
                            FolderNode(name="Exports", type="folder"),
                            FolderNode(
                                name="Platform_Deliverables",
                                type="folder",
                                children=[
                                    FolderNode(name="Instagram", type="folder"),
                                    FolderNode(name="TikTok", type="folder"),
                                    FolderNode(name="YouTube", type="folder")
                                ]
                            )
                        ]
                    ),
                    FolderNode(
                        name="06_Thumbnails",
                        type="folder"
                    ),
                    FolderNode(
                        name="README.txt",
                        type="file",
                        placeholder_content="Project: {project}\nClient: {client}\nDate: {date}\nPlatform: {platform}\nContent Type: {content_type}\n\nFolder structure generated by Clip Assassin"
                    )
                ]
            )
        ]
    )


def create_commercial_template() -> IngestTemplate:
    """Commercial/Advertisement Production Template"""
    return IngestTemplate(
        id="commercial-v1",
        name="Commercial Production",
        description="Full-service commercial and advertisement workflow",
        version="1.0",
        author="Clip Assassin",
        category="Commercial",
        tags=["commercial", "advertising", "brand", "corporate"],
        
        parameters=[
            TemplateParameter(
                name="campaign_name",
                label="Campaign Name",
                type=ParameterType.TEXT,
                required=True
            ),
            TemplateParameter(
                name="agency",
                label="Advertising Agency",
                type=ParameterType.TEXT,
                required=False
            ),
            TemplateParameter(
                name="camera_count",
                label="Number of Cameras",
                type=ParameterType.NUMBER,
                min_value=1,
                max_value=10,
                default="3",
                required=True
            ),
            TemplateParameter(
                name="deliverable_format",
                label="Deliverable Formats",
                type=ParameterType.SELECT,
                options=["Broadcast TV", "Web Only", "Social + Web", "All Formats"],
                default="All Formats",
                required=True
            ),
            TemplateParameter(
                name="shoot_locations",
                label="Number of Locations",
                type=ParameterType.NUMBER,
                min_value=1,
                max_value=20,
                default="1",
                required=False
            )
        ],
        
        structure=[
            FolderNode(
                name="{project}",
                type="folder",
                children=[
                    FolderNode(
                        name="ADMIN",
                        type="folder",
                        children=[
                            FolderNode(name="Contracts", type="folder"),
                            FolderNode(name="Invoices", type="folder"),
                            FolderNode(name="Call_Sheets", type="folder"),
                            FolderNode(name="Releases", type="folder"),
                            FolderNode(
                                name="Production_Schedule.xlsx",
                                type="file",
                                placeholder_content="Date,Location,Scenes,Cast,Crew,Equipment\n{date},Location 1,1-5,TBD,TBD,TBD"
                            )
                        ]
                    ),
                    FolderNode(
                        name="PRE_PRODUCTION",
                        type="folder",
                        children=[
                            FolderNode(name="Creative_Brief", type="folder"),
                            FolderNode(name="Mood_Boards", type="folder"),
                            FolderNode(name="Scripts", type="folder"),
                            FolderNode(name="Storyboards", type="folder"),
                            FolderNode(name="Animatics", type="folder"),
                            FolderNode(
                                name="Treatment_{campaign_name}.pdf",
                                type="file",
                                placeholder_content=""
                            )
                        ]
                    ),
                    FolderNode(
                        name="PRODUCTION",
                        type="folder",
                        children=[
                            FolderNode(
                                name="Location_{loc}",
                                type="folder",
                                loop_variable="shoot_locations",
                                loop_index="loc",
                                loop_start=1,
                                children=[
                                    FolderNode(
                                        name="Camera_{cam}",
                                        type="folder",
                                        loop_variable="camera_count",
                                loop_index="cam",
                                        loop_start=1,
                                        children=[
                                            FolderNode(name="A_CAM", type="folder"),
                                            FolderNode(name="B_CAM", type="folder"),
                                            FolderNode(name="C_CAM", type="folder")
                                        ]
                                    ),
                                    FolderNode(name="Sound", type="folder"),
                                    FolderNode(name="Lighting", type="folder"),
                                    FolderNode(name="BTS_Photos", type="folder")
                                ]
                            )
                        ]
                    ),
                    FolderNode(
                        name="POST_PRODUCTION",
                        type="folder",
                        children=[
                            FolderNode(name="Dailies", type="folder"),
                            FolderNode(name="Proxies", type="folder"),
                            FolderNode(
                                name="Edit_Versions",
                                type="folder",
                                children=[
                                    FolderNode(name="V1_Rough", type="folder"),
                                    FolderNode(name="V2_Fine", type="folder"),
                                    FolderNode(name="V3_Picture_Lock", type="folder")
                                ]
                            ),
                            FolderNode(name="Color_Grades", type="folder"),
                            FolderNode(name="Sound_Mix", type="folder"),
                            FolderNode(name="VFX", type="folder"),
                            FolderNode(name="Titles_Graphics", type="folder")
                        ]
                    ),
                    FolderNode(
                        name="DELIVERABLES",
                        type="folder",
                        children=[
                            FolderNode(
                                name="TV_Broadcast",
                                type="folder",
                                condition="deliverable_format in ['Broadcast TV', 'All Formats']"
                            ),
                            FolderNode(
                                name="Web_Versions",
                                type="folder",
                                condition="deliverable_format in ['Web Only', 'Social + Web', 'All Formats']"
                            ),
                            FolderNode(
                                name="Social_Media",
                                type="folder",
                                condition="deliverable_format in ['Social + Web', 'All Formats']"
                            ),
                            FolderNode(name="Archival_Masters", type="folder")
                        ]
                    ),
                    FolderNode(
                        name="ARCHIVE",
                        type="folder",
                        children=[
                            FolderNode(name="Project_Files", type="folder"),
                            FolderNode(name="Assets", type="folder"),
                            FolderNode(
                                name="Project_Notes.txt",
                                type="file",
                                placeholder_content="Campaign: {campaign_name}\nAgency: {agency}\nClient: {client}\nDate: {date}\nOperator: {operator}"
                            )
                        ]
                    )
                ]
            )
        ]
    )


def create_film_production_template() -> IngestTemplate:
    """Film/Documentary Production Template"""
    return IngestTemplate(
        id="film-production-v1",
        name="Film & Documentary",
        description="Professional film and documentary workflow with multi-camera support",
        version="1.0",
        author="Clip Assassin",
        category="Film",
        tags=["film", "documentary", "feature", "indie", "cinema"],
        
        parameters=[
            TemplateParameter(
                name="production_type",
                label="Production Type",
                type=ParameterType.SELECT,
                options=["Feature Film", "Short Film", "Documentary", "Web Series"],
                default="Feature Film",
                required=True
            ),
            TemplateParameter(
                name="camera_packages",
                label="Number of Camera Packages",
                type=ParameterType.NUMBER,
                min_value=1,
                max_value=6,
                default="2",
                required=True
            ),
            TemplateParameter(
                name="sound_recordist",
                label="Sound Recordist Name",
                type=ParameterType.TEXT,
                required=False
            ),
            TemplateParameter(
                name="editor",
                label="Lead Editor",
                type=ParameterType.TEXT,
                required=False
            ),
            TemplateParameter(
                name="shooting_days",
                label="Total Shooting Days",
                type=ParameterType.NUMBER,
                min_value=1,
                max_value=100,
                default="20",
                required=False
            )
        ],
        
        structure=[
            FolderNode(
                name="{project}",
                type="folder",
                children=[
                    FolderNode(
                        name="SCRIPT",
                        type="folder",
                        children=[
                            FolderNode(name="Drafts", type="folder"),
                            FolderNode(name="Breakdowns", type="folder"),
                            FolderNode(name="Sides", type="folder"),
                            FolderNode(
                                name="Final_Script.pdf",
                                type="file",
                                placeholder_content=""
                            )
                        ]
                    ),
                    FolderNode(
                        name="PRODUCING",
                        type="folder",
                        children=[
                            FolderNode(name="Budget", type="folder"),
                            FolderNode(name="Schedule", type="folder"),
                            FolderNode(name="Locations", type="folder"),
                            FolderNode(name="Casting", type="folder"),
                            FolderNode(name="Crew_Contacts", type="folder"),
                            FolderNode(name="Permits", type="folder")
                        ]
                    ),
                    FolderNode(
                        name="CAMERA",
                        type="folder",
                        children=[
                            FolderNode(
                                name="Day_{day:02d}",
                                type="folder",
                                loop_variable="shooting_days",
                                loop_index="day",
                                loop_start=1,
                                children=[
                                    FolderNode(
                                        name="CamPkg_{pkg}",
                                        type="folder",
                                        loop_variable="camera_packages",
                                loop_index="pkg",
                                        loop_start=1,
                                        children=[
                                            FolderNode(name="Card_A", type="folder"),
                                            FolderNode(name="Card_B", type="folder"),
                                            FolderNode(name="Card_C", type="folder"),
                                            FolderNode(name="Sync", type="folder")
                                        ]
                                    ),
                                    FolderNode(name="Sound", type="folder"),
                                    FolderNode(name="Script_Supervisor", type="folder"),
                                    FolderNode(name="DIT", type="folder")
                                ]
                            )
                        ]
                    ),
                    FolderNode(
                        name="SOUND",
                        type="folder",
                        children=[
                            FolderNode(name="Production_Sound", type="folder"),
                            FolderNode(name="ADR", type="folder"),
                            FolderNode(name="Foley", type="folder"),
                            FolderNode(name="Ambience", type="folder")
                        ]
                    ),
                    FolderNode(
                        name="EDIT",
                        type="folder",
                        children=[
                            FolderNode(name="Assembly", type="folder"),
                            FolderNode(name="Rough_Cut", type="folder"),
                            FolderNode(name="Fine_Cut", type="folder"),
                            FolderNode(name="Picture_Lock", type="folder"),
                            FolderNode(name="Temp_VFX", type="folder"),
                            FolderNode(name="Temp_Sound", type="folder"),
                            FolderNode(name="Temp_Music", type="folder")
                        ]
                    ),
                    FolderNode(
                        name="POST",
                        type="folder",
                        children=[
                            FolderNode(name="Online_Edit", type="folder"),
                            FolderNode(name="Color_Grading", type="folder"),
                            FolderNode(name="Sound_Design", type="folder"),
                            FolderNode(name="Mix_Stems", type="folder"),
                            FolderNode(name="VFX_Shots", type="folder"),
                            FolderNode(name="Titles", type="folder")
                        ]
                    ),
                    FolderNode(
                        name="DELIVERABLES",
                        type="folder",
                        children=[
                            FolderNode(name="DCP", type="folder"),
                            FolderNode(name="ProRes_Master", type="folder"),
                            FolderNode(name="DNxHR_Master", type="folder"),
                            FolderNode(name="Streaming", type="folder"),
                            FolderNode(name="Trailers", type="folder"),
                            FolderNode(name="EPK", type="folder")
                        ]
                    ),
                    FolderNode(
                        name="PUBLICITY",
                        type="folder",
                        children=[
                            FolderNode(name="Stills", type="folder"),
                            FolderNode(name="Press_Kit", type="folder"),
                            FolderNode(name="Posters", type="folder")
                        ]
                    ),
                    FolderNode(
                        name="LEGAL",
                        type="folder",
                        children=[
                            FolderNode(name="Rights_Clearances", type="folder"),
                            FolderNode(name="Music_Licenses", type="folder"),
                            FolderNode(name="Talent_Releases", type="folder"),
                            FolderNode(name="Location_Agreements", type="folder")
                        ]
                    )
                ]
            )
        ]
    )


# Registry of all built-in templates
BUILTIN_TEMPLATES = [
    create_social_media_template(),
    create_commercial_template(),
    create_film_production_template()
]


def get_builtin_templates() -> list:
    """Return list of all built-in templates"""
    return BUILTIN_TEMPLATES


def get_builtin_template_by_id(template_id: str) -> IngestTemplate:
    """Get a specific built-in template by ID"""
    for template in BUILTIN_TEMPLATES:
        if template.id == template_id:
            return template
    return None
