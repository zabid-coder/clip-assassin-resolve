export const toolHelp = [
  {
    "id": "snapshot",
    "title": "Timeline Snapshot",
    "help": "Creates a backup copy of the active timeline. Keep this copy before editing; switch back to it when you need the original sequence."
  },
  {
    "id": "magic_bin_organizer",
    "title": "Magic Bin Organizer",
    "help": "Scans the root Media Pool and automatically moves loose Video, Audio, and Image files into standard organized Bins."
  },
  {
    "id": "batch_clip_renamer",
    "title": "Batch Clip Renamer",
    "help": "Rename all clips on Video Track 1 with a sequential pattern. Enter a prefix like 'Interview' and clips become Interview_001, Interview_002, etc."
  },
  {
    "id": "social_media_reframe",
    "title": "Social Media Reframe",
    "help": "Duplicates your current timeline and automatically sets the resolution to 9:16 or 1:1 with scale-to-crop settings."
  },
  {
    "id": "quick_title",
    "title": "Quick Title",
    "help": "Instantly adds a standard Text+ title at your current playhead position."
  },
  {
    "id": "adjustment_layer",
    "title": "Quick Adjustment Layer",
    "help": "Instantly adds an Adjustment Layer to Video Track 5 at your current playhead position without shifting clips. Requires an 'Adjustment Clip' in your Media Pool."
  },
  {
    "id": "multicam_auto_sync",
    "title": "Multi-Cam Auto Sync",
    "help": "Select at least one video and one audio clip in the Media Pool, then click this to auto-sync them by waveform."
  },
  {
    "id": "badwords",
    "title": "BadWords Cleaner",
    "help": "Scans BadWords-generated color markers from the current timeline. Select which marker colors to remove, then create a clean timeline without those segments."
  },
  {
    "id": "merge_timelines",
    "title": "Merge Timelines",
    "help": "Click to select multiple timelines. They will be copied into a single Master Timeline."
  },
  {
    "id": "watermark_track",
    "title": "Watermark Track",
    "help": "Provide the path to an image to place it on a top video track."
  },
  {
    "id": "auto_jcut__lcut",
    "title": "Auto J-Cut / L-Cut",
    "help": "Requires aligned V1/A1 clips and available source handles. Clip FX and automation need manual review in the copy. J-Cut starts next audio early; L-Cut extends current audio."
  },
  {
    "id": "silence_remover",
    "title": "Silence Remover",
    "help": "Detects silent sections in the audio and creates a new timeline without them. Perfect for jump-cut style content. Requires pydub + ffmpeg."
  },
  {
    "id": "create_master_folder",
    "title": "Master Folder Setup",
    "help": "1. Select a preset or create one. 2. Enter project details and choose a parent directory. 3. Preview the complete structure before creating folders."
  },
  {
    "id": "master_ingest",
    "title": "Auto Ingest",
    "help": "Choose your project root. Camera, day and card folders can be nested in any order. Review the folder-to-timeline mapping before confirming. This creates a new Resolve project and references supported media in its existing location."
  },
  {
    "id": "timecode_cutter",
    "title": "Timecode Cutter",
    "help": "Enter ranges like 00:01:30-00:02:00 or 1:30-2:00 and the app will create an edited copy with frame-accurate boundaries. Numeric values are seconds."
  },
  {
    "id": "clip_picker",
    "title": "Clip Picker",
    "help": "List clip names or number ranges (e.g. '1-5, Interview, 10-15') to copy them to a new timeline."
  },
  {
    "id": "markers_to_timeline",
    "title": "Markers to Timeline",
    "help": "Select a marker color to extract all marked clips into a new timeline."
  },
  {
    "id": "flag_filter",
    "title": "Flag Filter",
    "help": "Select a flag color to copy flagged clips to a new timeline."
  },
  {
    "id": "native_subtitles",
    "title": "Resolve Subtitles",
    "help": "Select a timeline containing speech in Resolve. This uses Resolve's native transcription feature and does not require a cloud account."
  },
  {
    "id": "transcribe",
    "title": "Transcribe Media",
    "help": "Choose a provider, media file, language and output folder. Local Whisper may download its model on first use."
  },
  {
    "id": "youtube_upload",
    "title": "Upload to YouTube",
    "help": "Select your finished video and review the title, description and visibility. Uploads use resumable chunks; cancellation stops before the next chunk."
  },
  {
    "id": "multiplatform_render",
    "title": "Batch Timeline Render",
    "help": "Adds render jobs to the Render Queue for selected timelines using a Resolve Preset."
  },
  {
    "id": "extract_thumbnails",
    "title": "Extract Thumbnails",
    "help": "'Markers' mode exports a still frame at every timeline marker."
  },
  {
    "id": "auto_youtube_chapters",
    "title": "Auto YouTube Chapters",
    "help": "Generates a YouTube timestamp list from timeline markers."
  },
  {
    "id": "shotlist_generator",
    "title": "Client Shotlist / Document Exporter",
    "help": "Exports a professional shotlist of Video Track 1. Choose CSV or Word (.docx) template."
  }
]
