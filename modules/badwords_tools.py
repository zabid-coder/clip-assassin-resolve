"""
BadWords Integration — Marker Scanner & Timeline Cleaner
Scans color-coded markers from BadWords-generated timelines
and creates clean timelines by removing marked segments.
"""


def scan_markers(core):
    """
    Scan the current timeline for all markers and return a summary
    grouped by color with counts and total duration.
    
    Returns:
        dict with keys: success, markers (list), summary (dict of color -> count),
        total_marked_seconds, timeline_name
    """
    try:
        timeline = core.project.GetCurrentTimeline()
        if not timeline:
            return {"success": False, "message": "No active timeline found."}

        fps = float(timeline.GetSetting("timelineFrameRate") or 30)
        timeline_name = timeline.GetName()
        markers = timeline.GetMarkers()

        if not markers:
            return {
                "success": False,
                "message": f"No markers found on timeline '{timeline_name}'. "
                           "Make sure you have run BadWords analysis first."
            }

        # Build marker list and color summary
        marker_list = []
        color_summary = {}
        total_marked_frames = 0

        for frame_id, marker_data in markers.items():
            color = marker_data.get("color", "Unknown")
            duration = int(marker_data.get("duration", 1))
            name = marker_data.get("name", "")
            note = marker_data.get("note", "")

            marker_list.append({
                "frame": int(frame_id),
                "color": color,
                "duration": duration,
                "name": name,
                "note": note,
                "time_seconds": round(int(frame_id) / fps, 2)
            })

            if color not in color_summary:
                color_summary[color] = {"count": 0, "total_frames": 0}
            color_summary[color]["count"] += 1
            color_summary[color]["total_frames"] += duration
            total_marked_frames += duration

        # Convert frames to seconds in summary
        for color in color_summary:
            color_summary[color]["total_seconds"] = round(
                color_summary[color]["total_frames"] / fps, 1
            )

        return {
            "success": True,
            "timeline_name": timeline_name,
            "fps": fps,
            "total_markers": len(marker_list),
            "total_marked_seconds": round(total_marked_frames / fps, 1),
            "summary": color_summary,
            "markers": marker_list
        }

    except Exception as e:
        return {"success": False, "message": f"Error scanning markers: {str(e)}"}


def clean_timeline(core, colors_to_remove):
    from modules.ranges import assemble_ranges, normalize_ranges, invert_ranges
    if not core.project: return False, "Connect to a Resolve project first."
    timeline = core.project.GetCurrentTimeline()
    if not timeline: return False, "No active timeline found."
    if not colors_to_remove: return False, "Select marker colors to remove."
    duration = timeline.GetEndFrame() - timeline.GetStartFrame()
    remove = [(int(frame), int(frame)+max(1, int(data.get("duration", 1))))
              for frame,data in (timeline.GetMarkers() or {}).items() if data.get("color") in colors_to_remove]
    remove = normalize_ranges(remove, duration)
    if not remove: return False, "No matching markers inside the timeline."
    return assemble_ranges(core, timeline, invert_ranges(remove, duration), "Cleaned - " + timeline.GetName())
