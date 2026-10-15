"""
Timeline Snapshot — Duplicate current timeline as a backup before destructive operations.
Batch Clip Renamer — Rename clips on Video Track 1 with a pattern.
"""
import time


def create_snapshot(core):
    """Duplicate the current timeline as a safety backup"""
    try:
        timeline = core.project.GetCurrentTimeline()
        if not timeline:
            return False, "No active timeline found."

        original_name = timeline.GetName()
        timestamp = time.strftime("%H%M%S")
        snapshot_name = core.unique_timeline_name(f"Backup - {original_name} - {timestamp}")

        # DaVinci Resolve API: DuplicateTimeline creates an exact copy
        new_timeline = timeline.DuplicateTimeline(snapshot_name)

        if new_timeline:
            # Switch back to original timeline
            core.project.SetCurrentTimeline(timeline)
            return True, f"✓ Snapshot saved: '{snapshot_name}'\nYou can safely continue editing. The backup is in your timeline list."
        else:
            # Fallback: try via media pool
            mpi = core.get_clip_by_name(original_name)
            if mpi:
                new_tl = core.media_pool.CreateTimelineFromClips(snapshot_name, [mpi])
                if new_tl:
                    core.project.SetCurrentTimeline(timeline)
                    return True, f"✓ Snapshot saved: '{snapshot_name}'"
            return False, "Failed to duplicate timeline. Try manually via right-click in Resolve."

    except Exception as e:
        return False, f"Error creating snapshot: {str(e)}"


def batch_rename_clips(core, prefix, start_number=1, scope="timeline"):
    """
    Rename clips with a sequential pattern.
    
    Args:
        core: ResolveConnection instance
        prefix: Name prefix (e.g. "Interview")
        start_number: Starting number for the sequence
        scope: "timeline" (Video Track 1) or "selected" (selected in media pool)
    
    Returns:
        tuple: (success, message)
    """
    try:
        if not prefix.strip():
            return False, "Please enter a name prefix."

        clips_to_rename = []

        if scope == "selected":
            # Get selected clips from media pool
            selected = core.media_pool.GetSelectedClips()
            if selected:
                if isinstance(selected, dict):
                    clips_to_rename = list(selected.values())
                elif isinstance(selected, list):
                    clips_to_rename = selected
        else:
            # Get clips from Video Track 1
            timeline = core.project.GetCurrentTimeline()
            if not timeline:
                return False, "No active timeline found."

            items = timeline.GetItemListInTrack("video", 1)
            if not items:
                return False, "No clips found on Video Track 1."

            for item in items:
                clips_to_rename.append(item)

        if not clips_to_rename:
            return False, "No clips found to rename."

        # Calculate padding width based on total count
        total = len(clips_to_rename)
        pad_width = max(3, len(str(start_number + total - 1)))

        renamed = 0
        for i, clip in enumerate(clips_to_rename):
            num = start_number + i
            new_name = f"{prefix}_{str(num).zfill(pad_width)}"
            
            old_name = clip.GetName()
            # Get file extension from original name
            ext = ""
            if "." in old_name:
                ext = "." + old_name.rsplit(".", 1)[-1]
            
            setter = getattr(clip, "SetName", None)
            ok = setter(f"{new_name}{ext}") if setter else clip.SetClipProperty("Clip Name", f"{new_name}{ext}")
            if ok: renamed += 1

        return renamed == total, f"Renamed {renamed}/{total} clips starting at {prefix}_{str(start_number).zfill(pad_width)}."

    except Exception as e:
        return False, f"Error renaming clips: {str(e)}"


def get_project_stats(core):
    """Get comprehensive project statistics"""
    try:
        if not core.project:
            return {"success": False, "message": "No project connected"}

        project_name = core.project.GetName()

        # Timeline info
        timeline_count = core.project.GetTimelineCount()
        timelines_info = []

        total_clips_used = 0
        total_duration_frames = 0

        for i in range(1, timeline_count + 1):
            t = core.project.GetTimelineByIndex(i)
            if t:
                name = t.GetName()
                fps = float(t.GetSetting("timelineFrameRate") or 30)
                start = int(t.GetStartFrame())
                end = int(t.GetEndFrame())
                duration_frames = max(0, end - start)
                duration_seconds = round(duration_frames / fps, 1)

                # Count clips on video track 1
                items = t.GetItemListInTrack("video", 1)
                clip_count = len(items) if items else 0
                total_clips_used += clip_count
                total_duration_frames += duration_frames

                # Count markers
                markers = t.GetMarkers()
                marker_count = len(markers) if markers else 0

                # Count tracks
                video_tracks = t.GetTrackCount("video")
                audio_tracks = t.GetTrackCount("audio")

                timelines_info.append({
                    "name": name,
                    "clips": clip_count,
                    "duration_seconds": duration_seconds,
                    "markers": marker_count,
                    "video_tracks": video_tracks,
                    "audio_tracks": audio_tracks,
                    "fps": fps
                })

        # Media pool info
        root = core.media_pool.GetRootFolder()
        total_pool_clips = 0
        total_bins = 0

        def count_recursive(folder):
            nonlocal total_pool_clips, total_bins
            clips = folder.GetClipList()
            if clips:
                total_pool_clips += len(clips)
            subs = folder.GetSubFolderList()
            if subs:
                total_bins += len(subs)
                for s in subs:
                    count_recursive(s)

        count_recursive(root)

        avg_fps = 30
        if timelines_info:
            avg_fps = timelines_info[0]["fps"]

        return {
            "success": True,
            "project_name": project_name,
            "timeline_count": timeline_count,
            "total_clips_used": total_clips_used,
            "total_pool_clips": total_pool_clips,
            "total_bins": total_bins,
            "total_duration_seconds": round(sum(t["duration_seconds"] for t in timelines_info), 1),
            "timelines": timelines_info
        }

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
