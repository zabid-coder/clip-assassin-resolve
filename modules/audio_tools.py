"""Audio tools use verified Resolve operations and preserve the source timeline."""
import os
import tempfile
import time
from uuid import uuid4
from services.jobs import checkpoint, JobCancelled


def apply_jl_cuts(core, cut_type='j', overlap_frames=10):
    """Rebuild A1 in a duplicate, alternating new tracks to allow overlap."""
    if not core.project: return False, 'Connect to a Resolve project first.'
    source = core.project.GetCurrentTimeline()
    if not source: return False, 'No active timeline.'
    if cut_type not in ('j', 'l') or overlap_frames < 1: return False, 'Choose J or L and a positive overlap.'
    audio = sorted(source.GetItemListInTrack('audio', 1) or [], key=lambda i: i.GetStart())
    video = sorted(source.GetItemListInTrack('video', 1) or [], key=lambda i: i.GetStart())
    if len(audio) < 2 or len(audio) != len(video):
        return False, 'J/L cuts require one matching A1 audio clip per V1 video clip (at least two).'
    fps = float(source.GetSetting('timelineFrameRate') or 30)
    plans, applied = [], 0
    for index, item in enumerate(audio):
        mpi = item.GetMediaPoolItem()
        if not mpi: return False, 'A1 contains an unsupported audio generator.'
        # Reconstruction only supports normal speed, aligned source clips.
        if abs(item.GetStart()-video[index].GetStart()) > 1 or abs(item.GetEnd()-video[index].GetEnd()) > 1:
            return False, 'J/L cuts require aligned V1/A1 clips. Use a copy with aligned dialogue clips.'
        source_start = item.GetSourceStartFrame()
        source_end = item.GetSourceEndFrame()
        duration = item.GetDuration()
        if abs((source_end-source_start)-duration) > 1:
            return False, 'Retimed audio is not supported by automatic J/L cuts.'
        start, end, record = source_start, source_start+duration, item.GetStart()
        amount = 0
        if cut_type == 'j' and index > 0:
            amount = min(overlap_frames, int(item.GetLeftOffset()), int(record-source.GetStartFrame()))
            start -= amount
            record -= amount
        elif cut_type == 'l' and index < len(audio)-1:
            amount = min(overlap_frames, int(item.GetRightOffset()))
            end += amount
        if amount > 0: applied += 1
        plans.append((mpi, start, end, record, item, index))
    if not applied: return False, 'No source audio handles are available for the requested overlap.'
    duplicate = source.DuplicateTimeline(core.unique_timeline_name(f'{cut_type.upper()}-Cut - {source.GetName()}'))
    if not duplicate: return False, 'Could not duplicate the source timeline.'
    try:
        core.project.SetCurrentTimeline(duplicate)
        old = duplicate.GetItemListInTrack('audio', 1) or []
        # Deletion must not ripple or remove linked video.
        linked = []
        for item in old: linked.extend(item.GetLinkedItems() or [])
        if linked and not duplicate.SetClipsLinked(old+linked, False):
            raise RuntimeError('Could not unlink copied audio')
        if not duplicate.DeleteClips(old, False): raise RuntimeError('Could not replace copied A1 audio')
        first_new = duplicate.GetTrackCount('audio') + 1
        for _ in range(2):
            if not duplicate.AddTrack('audio', 'stereo'): raise RuntimeError('Could not create overlap audio tracks')
        for mpi, start, end, record, original, index in plans:
            checkpoint(20+index/max(1,len(plans))*70, 'Building audio overlap tracks')
            appended = core.media_pool.AppendToTimeline([{'mediaPoolItem': mpi, 'mediaType': 2,
                'startFrame': start, 'endFrame': end, 'recordFrame': record, 'trackIndex': first_new+index%2}])
            if not appended: raise RuntimeError('Resolve rejected an audio segment')
            if int(appended[0].GetDuration()) != int(end-start): raise RuntimeError('Unexpected audio duration')
            props = original.GetProperty() or {}
            audio_props = {k:v for k,v in props.items() if k in ('Volume', 'Pan', 'Pitch')}
            for key,value in audio_props.items(): appended[0].SetProperty(key,value)
        return True, f"Created '{duplicate.GetName()}' with {applied} {cut_type.upper()}-Cuts. Review the new audio tracks; clip FX and automation require manual review."
    except Exception as exc:
        core.project.SetCurrentTimeline(source)
        core.media_pool.DeleteTimelines([duplicate])
        return False, str(exc)


def get_render_status(core):
    if not core.project: return {'success': False, 'message': 'No project connected'}
    try:
        jobs = []
        for job in core.project.GetRenderJobList() or []:
            status = core.project.GetRenderJobStatus(job.get('JobId', '')) or {}
            jobs.append({'id': job.get('JobId', ''), 'name': job.get('TimelineName', 'Unknown'),
                'status': status.get('JobStatus', status.get('RenderStatus', job.get('RenderStatus', 'Ready'))),
                'progress': status.get('CompletionPercentage', 0), 'output_dir': job.get('TargetDir', ''),
                'format': f"{job.get('FormatWidth', '?')}x{job.get('FormatHeight', '?')}"})
        return {'success': True, 'jobs': jobs, 'total': len(jobs),
                **{key: sum(j['status'] == label for j in jobs) for key,label in
                   [('completed','Complete'),('rendering','Rendering'),('queued','Ready'),('failed','Failed')]}}
    except Exception as exc:
        return {'success': False, 'message': str(exc)}


def detect_silence(core, threshold_db=-40, min_silence_ms=500, padding_ms=100):
    from modules.ranges import assemble_ranges, normalize_ranges
    if not core.project: return False, 'Connect to a Resolve project first.'
    source = core.project.GetCurrentTimeline()
    if not source: return False, 'No active timeline.'
    if core.project.IsRenderingInProgress(): return False, 'Wait for the current render to finish.'
    duration = source.GetEndFrame() - source.GetStartFrame()
    if duration <= 0: return False, 'Timeline is empty.'
    if not -100 <= threshold_db <= 0 or min_silence_ms < 1 or padding_ms < 0:
        return False, 'Invalid silence detection settings.'
    try:
        from pydub import AudioSegment
        from pydub.silence import detect_nonsilent
    except ImportError:
        return False, 'Install pydub to enable silence detection.'
    project = core.project
    backup = 'ClipAssassin temporary ' + uuid4().hex
    saved, job, rendering = False, None, False
    try:
        saved = project.SaveAsNewRenderPreset(backup)
        if not saved: return False, 'Could not preserve current render settings.'
        with tempfile.TemporaryDirectory(prefix='clip-assassin-audio-') as directory:
            if not project.LoadRenderPreset('Audio Only'): return False, 'Resolve Audio Only preset is unavailable.'
            settings = {'SelectAllFrames': True, 'TargetDir': directory, 'CustomName': 'analysis',
                        'ExportVideo': False, 'ExportAudio': True, 'AudioFormat': 'wav',
                        'AudioCodec': 'lpcm', 'AudioBitDepth': 16, 'AudioSampleRate': 48000}
            if not project.SetRenderSettings(settings): return False, 'Resolve rejected audio-only render settings.'
            job = project.AddRenderJob()
            if not job: return False, 'Could not create the audio analysis render job.'
            if not project.StartRendering([job]): return False, 'Could not start audio export.'
            rendering = True
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                checkpoint(None, None)
                state = project.GetRenderJobStatus(job) or {}
                status = state.get('JobStatus', state.get('RenderStatus', ''))
                checkpoint(15 + float(state.get('CompletionPercentage', 0)) * .45, 'Rendering audio for silence analysis')
                if status == 'Complete':
                    rendering = False
                    break
                if status in ('Failed', 'Cancelled', 'Canceled'): raise RuntimeError(f'Audio render {status.lower()}')
                time.sleep(.25)
            else: raise RuntimeError('Audio export timed out after 120 seconds')
            files = [os.path.join(directory, name) for name in os.listdir(directory) if name.lower().endswith(('.wav','.mp3','.aac','.flac','.mov','.mp4'))]
            if not files: return False, 'Resolve did not produce an audio file.'
            checkpoint(65, 'Analyzing silence in the audio')
            audio = AudioSegment.from_file(files[0])
            ranges = detect_nonsilent(audio, min_silence_len=min_silence_ms, silence_thresh=threshold_db)
            fps = float(source.GetSetting('timelineFrameRate') or 30)
            frames = normalize_ranges([(round(max(0,a-padding_ms)*fps/1000), round(min(len(audio),b+padding_ms)*fps/1000)) for a,b in ranges], duration)
            if not frames: return False, 'No non-silent audio detected at this threshold.'
            if frames == [(0, duration)]: return False, 'No silence matched the current settings.'
            return assemble_ranges(core, source, frames, 'No Silence - ' + source.GetName())
    except Exception as exc:
        return False, f'Silence removal failed: {exc}'
    finally:
        if rendering: project.StopRendering()
        if job: project.DeleteRenderJob(job)
        if saved:
            project.LoadRenderPreset(backup)
            project.DeleteRenderPreset(backup)
