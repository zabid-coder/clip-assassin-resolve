"""Previewable operations, source-pinned Resolve execution, and job dispatch."""
import base64
import hashlib
import hmac
import importlib.util
import json
from pathlib import Path
import secrets
import shutil
import time
from pydantic import BaseModel,Field,ValidationError
from services.jobs import native_lock,checkpoint,JobCancelled
from services import library,integrations
from services.folder_presets import find
from services.template_engine import template_engine

_secret=secrets.token_bytes(32)

class Cut(BaseModel):
    timecodes:str
    reverse:bool=False
    clip_name:str=''
class Names(BaseModel): names:str
class Color(BaseModel):color:str='All'
class Merge(BaseModel):timeline_names:str
class Watermark(BaseModel):image_path:str
class Render(BaseModel):timelines:list[str];target_dir:str;preset_name:str=''
class RenderSelection(BaseModel):job_ids:list[str]
class Thumbnails(BaseModel):mode:str;target_dir:str
class Shotlist(BaseModel):format:str;target_path:str;template_path:str=''
class Ingest(BaseModel):master_folder_path:str
class Reframe(BaseModel):format:str=Field(default='9:16',pattern='^(9:16|1:1|4:5)$')
class Rename(BaseModel):prefix:str;start_number:int=Field(default=1,ge=1);scope:str=Field(default='timeline',pattern='^(timeline|selected)$')
class JL(BaseModel):cut_type:str=Field(default='j',pattern='^[jl]$');overlap_frames:int=Field(default=10,ge=1,le=1000)
class Silence(BaseModel):threshold_db:int=Field(default=-40,ge=-100,le=0);min_silence_ms:int=Field(default=500,ge=1,le=60000);padding_ms:int=Field(default=100,ge=0,le=10000)
class Colors(BaseModel):colors:list[str]
class Package(BaseModel):package_id:str;replace:bool=False
class FolderGenerate(BaseModel):template_id:str;parameters:dict;base_path:str
class Transcription(BaseModel):audio_path:str;target_dir:str;provider:str=Field(default='local',pattern='^(local|openai)$');language:str='';allow_cloud:bool=False
class Upload(BaseModel):video_path:str;title:str=Field(min_length=1,max_length=100);description:str=Field(default='',max_length=5000);privacy:str=Field(default='private',pattern='^(private|unlisted|public)$');allow_cloud:bool=False
class Empty(BaseModel):pass
MODELS={'cut':Cut,'pick_clips':Names,'markers_to_timeline':Color,'filter_by_flag':Color,'merge_timelines':Merge,
 'apply_watermark':Watermark,'batch_render':Render,'start_render':RenderSelection,'extract_thumbnails':Thumbnails,'export_shotlist':Shotlist,
 'master_ingest':Ingest,'social_reframe':Reframe,'batch_rename':Rename,'jl_cut':JL,'silence_remove':Silence,
 'badwords/clean':Colors,'library_install':Package,'library_remove':Package,'folder_generate':FolderGenerate,
 'transcribe':Transcription,'youtube_upload':Upload,**{k:Empty for k in ('snapshot','organize_bins','auto_sync','add_title','add_adjustment_layer','youtube_chapters','subtitles')}}
LOCAL={'library_install','library_remove','folder_generate','transcribe','youtube_upload'}
LABELS={'cut':'Timecode Cutter','pick_clips':'Clip Picker','markers_to_timeline':'Extract Marked Clips','filter_by_flag':'Extract Flagged Clips',
 'merge_timelines':'Merge Timelines','apply_watermark':'Watermark','batch_render':'Queue Renders','start_render':'Render Selected Videos','extract_thumbnails':'Export Still Frames',
 'export_shotlist':'Export Shotlist','master_ingest':'Auto Ingest','social_reframe':'Social Reframe','batch_rename':'Rename Clips',
 'jl_cut':'J/L Cuts','silence_remove':'Remove Silence','badwords/clean':'Clean Marked Ranges','library_install':'Install Template Package',
 'library_remove':'Remove Managed Installation','folder_generate':'Create Project Folders','transcribe':'Transcribe Media','youtube_upload':'Upload to YouTube',
 'snapshot':'Timeline Snapshot','organize_bins':'Organize Media Pool','auto_sync':'Waveform Audio Sync','add_title':'Quick Title',
 'add_adjustment_layer':'Adjustment Layer','youtube_chapters':'Generate Chapters','subtitles':'Generate Resolve Subtitles'}


def source_context(engine):
    project=engine.project
    if not project:return {}
    timeline=project.GetCurrentTimeline()
    return {'project':project.GetName(),'project_id':project.GetUniqueId(),'timeline':timeline.GetName() if timeline else '',
            'timeline_id':timeline.GetUniqueId() if timeline else ''}


def validate(operation,payload):
    if operation not in MODELS:raise ValueError('Unsupported operation')
    return MODELS[operation].model_validate(payload).model_dump()


def preview(engine,operation,payload):
    payload=validate(operation,payload);warnings=[];errors=[];details=[];source={}
    if operation not in LOCAL:
        with native_lock:
            engine.refresh();source=source_context(engine)
            if not engine.project and operation!='master_ingest':errors.append('Open a Resolve project and connect first.')
            needs_timeline=operation not in ('master_ingest','organize_bins','auto_sync','batch_rename','batch_render','merge_timelines','start_render')
            if needs_timeline and not source.get('timeline'):errors.append('Select a timeline in Resolve.')
            if engine.project and source.get('timeline') and operation!='master_ingest':
                timeline=engine.project.GetCurrentTimeline()
                duration=timeline.GetEndFrame()-timeline.GetStartFrame()
                details.append(f"Timeline: {duration} frames at {timeline.GetSetting('timelineFrameRate')} fps")
                if operation=='cut':
                    from time_parser import parse_timecodes
                    ranges,parse_errors=parse_timecodes(payload['timecodes'],float(timeline.GetSetting('timelineFrameRate') or 30))
                    errors.extend(parse_errors)
                    if not ranges:errors.append('Enter at least one valid time range.')
                    details.extend(f"{'Keep' if payload['reverse'] else 'Remove'} {a:g}–{b:g} seconds" for a,b in ranges)
                if operation in ('cut','pick_clips','markers_to_timeline','filter_by_flag','badwords/clean','merge_timelines','silence_remove'):
                    warnings.append('Creates a new timeline with nested source sections. Later source edits can affect the result.')
                if operation in ('apply_watermark','add_title','add_adjustment_layer','batch_rename','organize_bins','auto_sync','subtitles'):
                    warnings.append('Changes the selected project or timeline. Create a snapshot first if you need a backup.')
                if operation=='add_adjustment_layer' and not engine.get_clip_by_name('Adjustment Clip'):errors.append("Add an 'Adjustment Clip' to the Media Pool first.")
                if operation=='jl_cut':warnings.append('Requires aligned V1/A1 clips and source handles. Review clip FX and channel routing in the duplicate.')
            if operation=='auto_sync' and engine.media_pool:
                clips=engine.media_pool.GetSelectedClips() or []
                if isinstance(clips,dict):clips=list(clips.values())
                details.append(f'{len(clips)} Media Pool clips selected')
                if len(clips)<2:errors.append('Select a video and matching separate audio in the Media Pool.')
                source['selected_media_ids']=[c.GetMediaId() for c in clips]
    if operation=='master_ingest':
        from services.ingest_plan import plan_ingest
        try:
            plan=plan_ingest(payload['master_folder_path'])
            source['ingest_fingerprint']=plan['fingerprint']
            if not plan['groups']:errors.append('No supported footage found. No project will be created.')
            details.append(f"{len(plan['groups'])} individual timelines · {plan['file_count']} footage files · {plan['audio_count']} separate audio files")
            details.extend(f"{g['folder']} → {g['timeline']} ({len(g['files'])} files)" for g in plan['groups'])
            warnings.append('Creates a new Resolve project and switches to it. Media stays in its existing location. Camera storage folders stay together; review every grouping before running.')
        except (ValueError,OSError) as exc:errors.append(str(exc))
    if operation=='library_install':
        plan=library.install_plan(payload['package_id']);details.extend([plan['name'],f"{plan['files']} files → {plan['target']}"])
        if plan['existing_files'] and not payload['replace']:errors.append('Existing template files found. Enable repair/replace to back up and replace conflicts.')
        if any(f['status']!='installed' for f in plan['fonts']):warnings.append('Some fonts are missing or need checking. Install the fonts before using these templates.')
        warnings.append('Restart Resolve after installation. Package fonts are provided as download links.')
    if operation=='library_remove':warnings.append('Only files tracked by this app are removed. Backed-up originals are restored.')
    if operation=='folder_generate':
        template=find(payload['template_id'])
        if not template:errors.append('Preset no longer exists.')
        else:
            result=template_engine.generate_structure(template,payload['parameters'],payload['base_path'],True)
            errors.extend(result['errors']);details.append(f"{result['total_items']} folders/files → {payload['base_path']}")
    for key in ('target_dir','target_path','base_path','master_folder_path'):
        if key in payload and not payload[key].strip():errors.append(f"Choose {key.replace('_',' ')}.")
    for key in ('image_path','audio_path','video_path','master_folder_path'):
        if key in payload and not Path(payload[key]).expanduser().exists():errors.append(f"Selected {key.replace('_',' ')} does not exist.")
    if operation=='transcribe':
        provider=payload['provider']
        if provider=='local' and not integrations.available('whisper'):errors.append('Install local Whisper or choose a configured cloud provider.')
        if provider=='openai':
            if not integrations.available('openai') or not integrations.credential('openai_key'):errors.append('Configure OpenAI in Connections first.')
            if not payload['allow_cloud']:errors.append('Confirm sending this media to OpenAI.')
            warnings.append('The selected file is sent to OpenAI and API usage can incur charges.')
    if operation=='youtube_upload':
        if not integrations.credential('youtube_token'):errors.append('Connect YouTube in Connections first.')
        if not payload['allow_cloud']:errors.append('Confirm uploading the selected video to YouTube.')
        warnings.append('Video will be uploaded with '+payload['privacy']+' visibility.')
    if operation=='start_render':
        details.append(f"Render {len(payload['job_ids'])} selected queued jobs")
        warnings.append('Rendering occupies Resolve until completion. Cancel stops the render started by this job.')
    if operation=='batch_render' and not payload['timelines']:errors.append('Select timelines to render.')
    if operation=='pick_clips' and not payload['names'].strip():errors.append('Enter clip names or numbers.')
    if operation=='merge_timelines' and not payload['timeline_names'].strip():errors.append('Select timelines to merge.')
    if operation=='batch_rename' and not payload['prefix'].strip():errors.append('Enter a clip name prefix.')
    if operation=='badwords/clean' and not payload['colors']:errors.append('Select at least one marker color.')
    body={'operation':operation,'payload':payload,'source':source,'expires':time.time()+600}
    raw=json.dumps(body,sort_keys=True,separators=(',',':')).encode()
    token=base64.urlsafe_b64encode(raw).decode()+'.'+hmac.new(_secret,raw,hashlib.sha256).hexdigest()
    return {'success':True,'ready':not errors,'title':LABELS[operation],'source':source,'details':details,'settings':payload,
            'warnings':warnings,'errors':errors,'preview_token':token}


def read_token(token):
    try:
        encoded,signature=token.rsplit('.',1);raw=base64.urlsafe_b64decode(encoded)
        if not hmac.compare_digest(signature,hmac.new(_secret,raw,hashlib.sha256).hexdigest()):raise ValueError()
        body=json.loads(raw)
        if body['expires']<time.time():raise ValueError()
        validate(body['operation'],body['payload'])
        return body
    except Exception:raise ValueError('Preview expired or changed. Review the operation again.')


def runner(engine):
    def execute(operation,payload,context,source):
        context.update(2,'Checking prerequisites')
        if operation=='library_install':return library.install(payload['package_id'],payload['replace'])
        if operation=='library_remove':return library.uninstall(payload['package_id'])
        if operation=='folder_generate':
            template=find(payload['template_id'])
            if not template:raise ValueError('Preset no longer exists')
            result=template_engine.generate_structure(template,payload['parameters'],payload['base_path'])
            return {**result,'message':f"Created {result['total_items']} folders/files" if result['success'] else '; '.join(result['errors']),
                    'target':result['created'][0]['path'] if result.get('created') and result['created'][0]['type']=='folder' else result['base_path']}
        if operation=='transcribe':return integrations.transcribe(payload)
        if operation=='youtube_upload':return integrations.youtube_upload(payload)
        with native_lock:
            context.update(5,'Connecting to Resolve')
            engine.refresh();current=source_context(engine)
            if source.get('project') and (source.get('project')!=current.get('project') or source.get('project_id')!=current.get('project_id') or source.get('timeline_id')!=current.get('timeline_id')):
                raise ValueError('The active Resolve project or timeline changed after preview. Review the operation again.')
            if operation=='auto_sync' and source.get('selected_media_ids'):
                clips=engine.media_pool.GetSelectedClips() or []
                if isinstance(clips,dict):clips=list(clips.values())
                if sorted(source['selected_media_ids'])!=sorted(c.GetMediaId() for c in clips):raise ValueError('Media Pool selection changed after preview. Review again.')
            if operation=='master_ingest':
                from services.ingest_plan import plan_ingest
                if source.get('ingest_fingerprint')!=plan_ingest(payload['master_folder_path'])['fingerprint']:
                    raise ValueError('Footage folders changed after review. Review Auto Ingest again.')
            context.update(10,'Running '+LABELS[operation])
            functions={
                'cut':lambda:engine.cut_video(payload['timecodes'],payload['reverse'],payload['clip_name']),
                'pick_clips':lambda:engine.pick_clips_from_timeline(payload['names']),
                'markers_to_timeline':lambda:engine.markers_to_timeline(payload['color']),
                'filter_by_flag':lambda:engine.filter_by_flag(payload['color']),
                'merge_timelines':lambda:engine.merge_timelines(payload['timeline_names']),
                'apply_watermark':lambda:engine.apply_watermark_track(payload['image_path']),
                'batch_render':lambda:engine.batch_render(payload['timelines'],payload['preset_name'],payload['target_dir']),
                'extract_thumbnails':lambda:engine.extract_thumbnails(payload['mode'],payload['target_dir']),
                'export_shotlist':lambda:engine.export_shotlist_doc(payload['format'],payload['target_path'],payload['template_path']),
                'master_ingest':lambda:engine.run_master_ingest(payload['master_folder_path']),
                'social_reframe':lambda:engine.create_social_timeline(payload['format']),
                'batch_rename':lambda:engine.batch_rename_clips(payload['prefix'],payload['start_number'],payload['scope']),
                'jl_cut':lambda:engine.apply_jl_cuts(payload['cut_type'],payload['overlap_frames']),
                'silence_remove':lambda:engine.detect_silence(payload['threshold_db'],payload['min_silence_ms'],payload['padding_ms']),
                'badwords/clean':lambda:engine.clean_badwords_timeline(payload['colors']),
                'snapshot':engine.create_snapshot,'organize_bins':engine.organize_media_pool,'auto_sync':engine.auto_sync_audio,
                'add_title':engine.add_quick_title,'add_adjustment_layer':engine.add_adjustment_layer,
                'youtube_chapters':engine.generate_youtube_chapters,'subtitles':engine.generate_subtitles}
            if operation=='start_render':
                from services.render_jobs import render
                return render(engine.project,payload['job_ids'])
            before={job['JobId'] for job in engine.project.GetRenderJobList() or []} if operation=='batch_render' else set()
            success,message=functions[operation]()
            if not success and context.manager.events[context.id].is_set():raise JobCancelled(message)
            result={'success':bool(success),'message':message,'source':source_context(engine)}
            if operation=='batch_render' and success:
                result['render_job_ids']=[job['JobId'] for job in engine.project.GetRenderJobList() or [] if job['JobId'] not in before]
            for key in ('target_dir','target_path'):
                if payload.get(key):result['target']=payload[key]
            return result
    return execute


def capabilities(engine):
    checks=[{'name':'FFmpeg','ready':bool(shutil.which('ffmpeg')),'detail':shutil.which('ffmpeg') or 'Install FFmpeg for media analysis.'},
        {'name':'Audio analysis','ready':integrations.available('pydub'),'detail':'pydub + audioop-lts on Python 3.13+'},
        {'name':'Local transcription','ready':integrations.available('whisper'),'detail':'Optional: install openai-whisper.'}]
    with native_lock:
        engine.refresh()
        connected=bool(engine.resolve)
        checks.insert(0,{'name':'DaVinci Resolve','ready':connected,'detail':engine.connection_message,
                         'version':engine.resolve.GetVersionString() if connected else ''})
        adjustment=bool(engine.get_clip_by_name('Adjustment Clip')) if engine.media_pool else False
        checks.append({'name':'Adjustment Clip','ready':adjustment,'detail':'Add an Adjustment Clip to the Media Pool to enable this tool.'})
    return {'success':True,'checks':checks,'fonts':sorted({f['family'] for p in library.packages() for f in p.get('fonts',[])})}
