from time_parser import parse_timecodes


def _seconds_to_frames(seconds, fps):
    return int(round(seconds * fps))


def cut_video(core, timecodes_text, reverse_mode=False, target_clip_name=""):
    from modules.ranges import assemble_ranges, normalize_ranges, invert_ranges
    if not core.project: return False, "Connect to a Resolve project first."
    timeline = core.project.GetCurrentTimeline()
    if not timeline: return False, "No active timeline found."
    fps = float(timeline.GetSetting("timelineFrameRate") or 30)
    ranges, errors = parse_timecodes(timecodes_text, fps)
    if errors: return False, "; ".join(errors)
    if not ranges: return False, "Enter at least one valid time range."
    duration = timeline.GetEndFrame() - timeline.GetStartFrame()
    ranges = normalize_ranges([(_seconds_to_frames(a, fps), _seconds_to_frames(b, fps)) for a,b in ranges], duration)
    if not ranges: return False, "Time ranges are outside this timeline."
    if target_clip_name:
        origin = timeline.GetStartFrame()
        matches = [(item.GetStart()-origin, item.GetEnd()-origin) for item in timeline.GetItemListInTrack("video", 1) or []
                   if target_clip_name.lower() in item.GetName().lower()]
        ranges = normalize_ranges([(max(a,c), min(b,d)) for a,b in ranges for c,d in matches if max(a,c)<min(b,d)], duration)
        if not ranges: return False, "No matching clips overlap these time ranges."
    keep = ranges if reverse_mode else invert_ranges(ranges, duration)
    return assemble_ranges(core, timeline, keep, ("Selected - " if reverse_mode else "Cut - ") + timeline.GetName())


def _extract_items(core, timeline, items, name):
    from modules.ranges import assemble_ranges
    origin = timeline.GetStartFrame()
    return assemble_ranges(core, timeline, [(i.GetStart()-origin, i.GetEnd()-origin) for i in items], name)


def pick_clips_from_timeline(core, names_text):
    if not core.project: return False, "Connect to a Resolve project first."
    timeline = core.project.GetCurrentTimeline()
    if not timeline: return False, "No active timeline found."
    import re
    terms = [term.strip().lower() for term in names_text.split(",") if term.strip()]
    if not terms: return False, "Enter clip names or number ranges."
    matched = []
    for index, item in enumerate(timeline.GetItemListInTrack("video", 1) or [], 1):
        name = item.GetName().lower()
        for term in terms:
            number_range = re.fullmatch(r"(\d+)\s*-\s*(\d+)", term)
            if number_range:
                first, last = map(int, number_range.groups())
                found = first <= index <= last
            elif term.isdigit(): found = index == int(term)
            else: found = term in name
            if found:
                matched.append(item)
                break
    if not matched: return False, "No matching clips found."
    return _extract_items(core, timeline, matched, "Picked Clips - " + timeline.GetName())


def merge_timelines(core, names_text):
    if not core.project: return False, "Connect to a Resolve project first."
    names = list(dict.fromkeys(n.strip() for n in names_text.split(',') if n.strip()))
    timelines = {t.GetName(): t for t in [core.project.GetTimelineByIndex(i) for i in range(1, core.project.GetTimelineCount()+1)] if t}
    if not names or any(n not in timelines for n in names): return False, "Select existing timelines to merge."
    original = core.project.GetCurrentTimeline()
    sources = [timelines[n] for n in names]
    fps = sources[0].GetSetting("timelineFrameRate")
    if any(t.GetSetting("timelineFrameRate") != fps for t in sources): return False, "Merge requires timelines with the same frame rate."
    clips = []
    for t in sources:
        duration = int(t.GetEndFrame()-t.GetStartFrame())
        if duration > 0:
            clips.append({"mediaPoolItem": t.GetMediaPoolItem(), "startFrame": 0, "endFrame": duration})
    if not clips or any(not c["mediaPoolItem"] for c in clips): return False, "Selected timelines are empty or unavailable."
    new = core.media_pool.CreateEmptyTimeline(core.unique_timeline_name("Master Merged Timeline"))
    if not new: return False, "Could not create merged timeline."
    core.project.SetCurrentTimeline(new)
    new.SetSetting("useCustomSettings", "1")
    new.SetSetting("timelineFrameRate", fps)
    for key in ("timelineResolutionWidth", "timelineResolutionHeight"):
        new.SetSetting(key, sources[0].GetSetting(key))
    for info in clips:
        if not core.media_pool.AppendToTimeline([info]):
            if original: core.project.SetCurrentTimeline(original)
            core.media_pool.DeleteTimelines([new])
            return False, "Could not append a timeline; output removed."
    return True, f"Merged {len(clips)} timelines in selected order into '{new.GetName()}'."


def markers_to_timeline(core, target_color):
    if not core.project: return False, "Connect to a Resolve project first."
    timeline = core.project.GetCurrentTimeline()
    if not timeline: return False, "No timeline open."
    markers = timeline.GetMarkers() or {}
    origin = timeline.GetStartFrame()
    matched = [item for item in timeline.GetItemListInTrack("video", 1) or []
               if any((target_color == "All" or data['color'] == target_color)
                      and item.GetStart() <= origin+int(frame) < item.GetEnd() for frame,data in markers.items())]
    if not matched: return False, f"No clips found with {target_color} markers."
    return _extract_items(core, timeline, matched, f"Extracted {target_color} Markers")


def filter_by_flag(core, target_color):
    if not core.project: return False, "Connect to a Resolve project first."
    timeline = core.project.GetCurrentTimeline()
    if not timeline: return False, "No timeline open."
    matched = [item for item in timeline.GetItemListInTrack("video", 1) or [] if target_color in (item.GetFlagList() or [])]
    if not matched: return False, f"No clips found with {target_color} flags."
    return _extract_items(core, timeline, matched, f"Extracted {target_color} Flags")

def apply_watermark_track(core, image_path):
    import os
    try:
        if not os.path.exists(image_path):
            return False, "Image file not found."
            
        timeline = core.project.GetCurrentTimeline()
        if not timeline: return False, "No timeline open."
        
        media_storage = core.resolve.GetMediaStorage()
        items = media_storage.AddItemListToMediaPool(image_path)
        if not items: return False, "Could not import image."
        
        timeline.AddTrack("video")
        top_track = timeline.GetTrackCount("video")
        
        start_frame = timeline.GetStartFrame()
        end_frame = timeline.GetEndFrame()
        current_record = start_frame
        
        all_appended_items = []
        
        while current_record < end_frame:
            remaining = end_frame - current_record
            appended = core.media_pool.AppendToTimeline([{
                "mediaPoolItem": items[0],
                "startFrame": 0,
                "endFrame": remaining,
                "trackIndex": top_track,
                "recordFrame": current_record
            }])
            
            if not appended or len(appended) == 0:
                break
                
            all_appended_items.extend(appended)
            
            clip_duration = appended[0].GetDuration()
            if clip_duration <= 0:
                break
                
            current_record += clip_duration
            
        if all_appended_items:
            compound_clip = timeline.CreateCompoundClip(all_appended_items, {"name": "Watermark Overlay"})
            
            # Apply dynamic transform based on timeline resolution
            try:
                w = float(timeline.GetSetting("timelineResolutionWidth") or 1920.0)
                h = float(timeline.GetSetting("timelineResolutionHeight") or 1080.0)
                
                zoom = 0.170
                # Scale Pan and Tilt proportionally from the 1920x1080 baseline
                pan = 725.0 * (w / 1920.0)
                tilt = 380.0 * (h / 1080.0)
                
                if compound_clip:
                    compound_clip.SetProperty("ZoomX", zoom)
                    compound_clip.SetProperty("ZoomY", zoom)
                    compound_clip.SetProperty("Pan", pan)
                    compound_clip.SetProperty("Tilt", tilt)
            except Exception:
                pass
            
        if not all_appended_items or current_record < end_frame:
            return False, "Watermark could not cover the full timeline. Inspect the new overlay track."
        return True, f"Watermark added on Track {top_track}."
    except Exception as e:
        return False, f"Error: {str(e)}"
