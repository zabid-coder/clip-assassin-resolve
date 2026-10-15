"""Frame-range assembly through nested timelines; preserves all source edits and audio."""

def normalize_ranges(ranges, duration):
    merged = []
    for start, end in sorted(ranges):
        start, end = max(0, round(start)), min(round(duration), round(end))
        if end <= start: continue
        if merged and start <= merged[-1][1]: merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else: merged.append((start, end))
    return merged


def invert_ranges(ranges, duration):
    result, cursor = [], 0
    for start, end in normalize_ranges(ranges, duration):
        if start > cursor: result.append((cursor, start))
        cursor = end
    if cursor < duration: result.append((cursor, duration))
    return result


def assemble_ranges(core, source, ranges, name):
    """Ranges use source-relative [start, end); validated against actual appended duration."""
    duration = source.GetEndFrame() - source.GetStartFrame()
    ranges = normalize_ranges(ranges, duration)
    if not ranges: return False, 'No frames remain in the requested selection.'
    mpi = source.GetMediaPoolItem()
    if not mpi: return False, 'Could not access the source timeline in the Media Pool.'
    name = core.unique_timeline_name(name)
    new = core.media_pool.CreateEmptyTimeline(name)
    if not new: return False, 'Could not create output timeline.'
    try:
        if not core.project.SetCurrentTimeline(new): raise RuntimeError('Could not activate output timeline')
        for key in ('timelineFrameRate', 'timelineResolutionWidth', 'timelineResolutionHeight'):
            new.SetSetting('useCustomSettings', '1')
            new.SetSetting(key, source.GetSetting(key))
        new.SetStartTimecode(source.GetStartTimecode())
        for index, (start, end) in enumerate(ranges):
            from services.jobs import checkpoint
            checkpoint(75 + index/max(1,len(ranges))*20, 'Assembling selected timeline sections')
            appended = core.media_pool.AppendToTimeline([{'mediaPoolItem': mpi, 'startFrame': start, 'endFrame': end}])
            if not appended: raise RuntimeError('Resolve rejected a source segment')
            if int(appended[0].GetDuration()) != end-start:
                raise RuntimeError('Resolve returned an unexpected segment duration; output removed')
        return True, f"Created '{name}' with {len(ranges)} segments ({sum(e-s for s,e in ranges)} frames). Source timeline preserved."
    except Exception as exc:
        core.project.SetCurrentTimeline(source)
        core.media_pool.DeleteTimelines([new])
        return False, str(exc)
