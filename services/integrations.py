"""Optional local transcription, OpenAI transcription, and user-initiated YouTube OAuth/upload."""
import importlib.util
import json
import os
from pathlib import Path
import secrets
import threading
import time
import db
from services.jobs import checkpoint

SERVICE='com.clipassassin.integrations'
_scope=['https://www.googleapis.com/auth/youtube.upload']
_oauth={'state':'disconnected','message':'Connect your YouTube account to upload.'}
_oauth_lock=threading.Lock()


def available(module): return importlib.util.find_spec(module) is not None


def credential(name, value=None, delete=False):
    if not available('keyring'):
        if value is not None: raise ValueError('Install keyring to save credentials securely: python -m pip install keyring')
        return os.environ.get('OPENAI_API_KEY','') if name=='openai_key' else ''
    import keyring
    if value is not None:
        if value: keyring.set_password(SERVICE,name,value)
        else:
            try: keyring.delete_password(SERVICE,name)
            except keyring.errors.PasswordDeleteError: pass
    try: return keyring.get_password(SERVICE,name) or (os.environ.get('OPENAI_API_KEY','') if name=='openai_key' else '')
    except Exception:
        if value is not None: raise
        return ''


def status():
    return {'success':True,'local_whisper':available('whisper'),'openai_sdk':available('openai'),
        'secure_storage':available('keyring'),'openai_configured':bool(db.get_setting('openai_key_saved')) or bool(os.environ.get('OPENAI_API_KEY')),
        'google_sdk':available('google_auth_oauthlib'),'youtube_configured':bool(db.get_setting('youtube_client_id')),
        'youtube_connected':bool(db.get_setting('youtube_token_saved')),'oauth':dict(_oauth),
        'whisper_model':db.get_setting('whisper_model','base')}


def configure(values):
    if 'whisper_model' in values:
        if values['whisper_model'] not in ('tiny','base','small','medium','large'): raise ValueError('Unsupported local Whisper model')
        db.set_setting('whisper_model',values['whisper_model'])
    for name in ('openai_key','youtube_client_secret'):
        if values.get(name):
            credential(name,values[name]); db.set_setting(name+'_saved','true')
    if 'youtube_client_id' in values: db.set_setting('youtube_client_id',values['youtube_client_id'].strip())
    return {'success':True,'message':'Connection settings saved. Secrets use the operating system credential store.'}


def start_youtube_oauth():
    if not available('google_auth_oauthlib') or not available('keyring'): raise ValueError('Install the optional cloud dependencies first: python -m pip install -r requirements-integrations.txt')
    client_id=db.get_setting('youtube_client_id');client_secret=credential('youtube_client_secret')
    if not client_id or not client_secret: raise ValueError('Enter a Google Desktop OAuth client ID and client secret first')
    with _oauth_lock:
        if _oauth['state']=='connecting': raise ValueError('A sign-in window is already open. Finish sign-in or wait for its timeout.')
        _oauth.update(state='connecting',message='Complete Google sign-in in your system browser. This request expires after 180 seconds.')
    def connect():
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow=InstalledAppFlow.from_client_config({'installed':{'client_id':client_id,'client_secret':client_secret,
                'auth_uri':'https://accounts.google.com/o/oauth2/auth','token_uri':'https://oauth2.googleapis.com/token',
                'redirect_uris':['http://127.0.0.1']}},scopes=_scope)
            auth=flow.run_local_server(host='127.0.0.1',port=0,open_browser=True,timeout_seconds=180,
                                      success_message='YouTube is connected. Return to Clip Assassin.')
            credential('youtube_token',auth.to_json());db.set_setting('youtube_token_saved','true')
            _oauth.update(state='connected',message='YouTube connected. Uploads start only when you choose Upload.')
        except Exception:
            _oauth.update(state='failed',message='YouTube sign-in did not finish. Check the Desktop OAuth client and try again.')
    threading.Thread(target=connect,daemon=True).start()
    return {'success':True,'message':_oauth['message']}


def disconnect_youtube():
    credential('youtube_token','')
    db.set_setting('youtube_token_saved','')
    _oauth.update(state='disconnected',message='YouTube disconnected from Clip Assassin.')
    return {'success':True,'message':'Saved YouTube tokens removed from this device.'}


def transcribe(payload):
    path=Path(payload.get('audio_path','')).expanduser()
    if not path.is_file(): raise ValueError('Choose an existing audio or video file')
    provider=payload.get('provider','local')
    language=payload.get('language','').strip()
    checkpoint(10,'Loading transcription provider')
    if provider=='local':
        if not available('whisper'): raise ValueError('Install local Whisper first: python -m pip install openai-whisper')
        import whisper
        model=whisper.load_model(db.get_setting('whisper_model','base'))
        checkpoint(25,'Transcribing locally; the current inference call must finish before cancellation')
        data=model.transcribe(str(path),**({'language':language} if language else {}))
    elif provider=='openai':
        if not payload.get('allow_cloud'): raise ValueError('Confirm that the selected file may be sent to OpenAI for transcription')
        if not available('openai'): raise ValueError('Install the OpenAI SDK first: python -m pip install openai')
        key=credential('openai_key')
        if not key: raise ValueError('Add an OpenAI API key in Connections')
        if path.stat().st_size>25*1024*1024: raise ValueError('Choose an audio file up to 25 MB for this transcription workflow')
        from openai import OpenAI
        checkpoint(25,'Sending the selected file to OpenAI for transcription')
        with path.open('rb') as handle:
            data=OpenAI(api_key=key,timeout=120).audio.transcriptions.create(model='whisper-1',file=handle,
                response_format='verbose_json',timestamp_granularities=['segment'],**({'language':language} if language else {})).model_dump()
    else: raise ValueError('Choose Local Whisper or OpenAI')
    checkpoint(90,'Writing transcript files')
    target=Path(payload.get('target_dir','')).expanduser()
    if not str(payload.get('target_dir','')).strip(): raise ValueError('Choose an output directory')
    target.mkdir(parents=True,exist_ok=True)
    safe=path.stem+'-transcript-'+time.strftime('%Y%m%d-%H%M%S')+'-'+secrets.token_hex(2)
    txt=target/(safe+'.txt');out=target/(safe+'.json')
    txt.write_text(data.get('text',''),encoding='utf-8');out.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    return {'success':True,'message':f'Transcript saved to {txt.name}','target':str(target),'files':[str(txt),str(out)],'text':data.get('text','')}


def youtube_upload(payload):
    if not payload.get('allow_cloud'): raise ValueError('Confirm uploading this video to your connected YouTube account')
    if not available('googleapiclient'): raise ValueError('Install optional integration dependencies first')
    path=Path(payload.get('video_path','')).expanduser()
    if not path.is_file(): raise ValueError('Choose an existing video file')
    if not payload.get('title','').strip(): raise ValueError('Enter a video title')
    privacy=payload.get('privacy','private')
    if privacy not in ('private','unlisted','public'): raise ValueError('Invalid privacy setting')
    stored=credential('youtube_token')
    if not stored: raise ValueError('Connect your YouTube account first')
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    auth=Credentials.from_authorized_user_info(json.loads(stored),scopes=_scope)
    if auth.expired and auth.refresh_token:
        auth.refresh(Request());credential('youtube_token',auth.to_json());db.set_setting('youtube_token_saved','true')
    service=build('youtube','v3',credentials=auth,cache_discovery=False)
    request=service.videos().insert(part='snippet,status',body={'snippet':{'title':payload['title'],
        'description':payload.get('description',''),'categoryId':'22'},'status':{'privacyStatus':privacy}},
        media_body=MediaFileUpload(str(path),chunksize=4*1024*1024,resumable=True))
    response=None
    while response is None:
        checkpoint(None,'Uploading video to YouTube; cancel stops before the next chunk')
        progress,response=request.next_chunk(num_retries=3)
        if progress:checkpoint(round(progress.progress()*95),'Uploading video to YouTube')
    return {'success':True,'message':'YouTube upload completed','url':'https://www.youtube.com/watch?v='+response['id'],
            'privacy':privacy}
