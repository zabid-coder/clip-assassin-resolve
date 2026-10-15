"""Self-contained Resolve packages and reversible, verified per-user installation."""
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
from uuid import uuid4
import zipfile
import db
from services.jobs import checkpoint

BASE = Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))
BUNDLED = BASE/'templates'/'bundled'
_lock = threading.RLock()


def sha(path):
    with Path(path).open('rb') as handle: return hashlib.file_digest(handle,'sha256').hexdigest()


def fusion_directory():
    if os.environ.get('CLIP_ASSASSIN_FUSION_DIR'): return Path(os.environ['CLIP_ASSASSIN_FUSION_DIR']).expanduser().resolve()
    if sys.platform=='darwin': return Path.home()/'Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion'
    if sys.platform=='win32': return Path(os.environ.get('APPDATA',Path.home()))/'Blackmagic Design/DaVinci Resolve/Support/Fusion'
    return Path.home()/'.local/share/DaVinciResolve/Fusion'


def state_dir():
    path=Path(db.data_dir)/'library';path.mkdir(parents=True,exist_ok=True);return path


def _read_json(path, default):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError: return default


def _save_json(path, value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8');os.chmod(temp,0o600);temp.replace(path)


def packages():
    builtin = _read_json(BUNDLED/'catalog.json',{'packages':[]})['packages']
    custom = _read_json(state_dir()/'catalog.json',{'packages':[]})['packages']
    return builtin+custom


def package_by_id(package_id):
    match=next((p for p in packages() if p['id']==package_id),None)
    if not match: raise ValueError('Package not found')
    return match


def package_path(package):
    if package.get('bundled'):
        path=(BUNDLED/package['file']).resolve()
        if not path.is_relative_to(BUNDLED.resolve()): raise ValueError('Invalid bundled path')
        return path
    return Path(package['file']).resolve()


def safe_archive_name(name):
    path=PurePosixPath(name)
    if '\\' in name or path.is_absolute() or any(p in ('..','') for p in path.parts): raise ValueError('Unsafe package path')
    return path


def archive_entries(path):
    entries=[]
    seen=set()
    with zipfile.ZipFile(path) as archive:
        total=0
        for info in archive.infolist():
            if info.is_dir() or '__MACOSX' in PurePosixPath(info.filename).parts or PurePosixPath(info.filename).name.startswith('.') or PurePosixPath(info.filename).name.lower() in ('thumbs.db','desktop.ini'): continue
            name=safe_archive_name(info.filename)
            if name.parts[0]!='Edit': continue
            if len(name.parts)<3 or name.parts[1] not in ('Titles','Effects','Generators','Transitions'): continue
            if stat.S_ISLNK(info.external_attr >> 16): raise ValueError('Package contains a symbolic link')
            if name.as_posix() in seen: raise ValueError('Package contains duplicate destination paths')
            seen.add(name.as_posix())
            total += info.file_size
            if total>2*1024**3 or info.file_size>512*1024**2 or len(entries)>10000: raise ValueError('Package exceeds installation size limits')
            entries.append((info.filename,Path('Templates')/Path(*name.parts),info.file_size,info.CRC))
    if not entries: raise ValueError('No supported Resolve templates in this package')
    return entries


@lru_cache(maxsize=1)
def font_families():
    try:
        if sys.platform=='darwin':
            try:
                import CoreText
                families=CoreText.CTFontManagerCopyAvailableFontFamilyNames()
            except ImportError:
                from AppKit import NSFontManager
                families=NSFontManager.sharedFontManager().availableFontFamilies()
            return {str(f).casefold() for f in families}
        if shutil.which('fc-list'):
            output=subprocess.run(['fc-list',':','family'],capture_output=True,text=True,timeout=15,check=True).stdout
            return {f.strip().casefold() for line in output.splitlines() for f in line.split(',')}
        if sys.platform=='win32':
            import winreg
            names=set()
            for hive in (winreg.HKEY_LOCAL_MACHINE,winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(hive,r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts') as key:
                        for i in range(winreg.QueryInfoKey(key)[1]):
                            name=winreg.EnumValue(key,i)[0]
                            names.add(re.sub(r'\s*\([^)]*\)','',name).casefold())
                except OSError: pass
            return names
    except Exception: pass
    return None


def font_status(font):
    installed=font_families()
    status='needs_checking' if installed is None else 'installed' if font['family'].casefold() in installed else 'missing'
    return {**font,'status':status}


def manifest_path(package_id): return state_dir()/'installed'/f'{package_id}.json'


def install_status(package, verify=False):
    manifest=_read_json(manifest_path(package['id']),None)
    if not manifest: return {'state':'not_installed','verified':False}
    changed=[]
    for item in manifest['files']:
        path=Path(item['target'])
        if not path.is_file() or (verify and sha(path)!=item['sha256']): changed.append(str(path))
    return {'state':'needs_repair' if changed else 'installed','verified':verify and not changed,
            'files':len(manifest['files']),'missing_or_changed':len(changed),'installed_at':manifest.get('installed_at'),
            'restart_required':True}


def catalog():
    return [{**{k:v for k,v in p.items() if k!='file'},'fonts':[font_status(f) for f in p.get('fonts',[])],
             'installation':install_status(p),'available':package_path(p).is_file()} for p in packages()]


def install_plan(package_id):
    package=package_by_id(package_id); path=package_path(package)
    if not path.is_file(): raise ValueError('Package file is missing')
    root=fusion_directory().resolve()
    entries=archive_entries(path)
    targets=[root/relative for _,relative,_,_ in entries]
    for dep in package.get('dependencies',[]): targets.append(root/'Fuses'/dep['name'])
    for target in targets:
        if not target.resolve().is_relative_to(root): raise ValueError('Installation path escapes the Resolve directory')
    existing=[str(p) for p in targets if p.exists()]
    return {'success':True,'package_id':package_id,'name':package['name'],'target':str(root),'files':len(targets),
            'existing_files':len(existing),'conflicts':existing[:30],'fonts':[font_status(f) for f in package.get('fonts',[])],
            'locations':package['locations'],'dependencies':[d['name'] for d in package.get('dependencies',[])],
            'message':'Existing different files are backed up before replacement. Restart Resolve after installation.'}


def install(package_id, replace=False):
    with _lock:
        package=package_by_id(package_id); path=package_path(package); plan=install_plan(package_id)
        if sha(path)!=package['sha256']: raise ValueError('Package checksum changed. Rescan before installing.')
        root=fusion_directory().resolve()
        previous=_read_json(manifest_path(package_id),{'files':[]})
        previous_by_path={f['target']:f for f in previous['files']}
        backup_root=state_dir()/'backups'/package_id/uuid4().hex
        staged=state_dir()/'staging'/uuid4().hex;staged.mkdir(parents=True)
        entries=archive_entries(path); records=[]; applied=[]
        try:
            with zipfile.ZipFile(path) as archive:
                for index,(entry,relative,_,_) in enumerate(entries):
                    checkpoint(index/max(1,len(entries))*45,f'Preparing {index+1}/{len(entries)} package files')
                    temporary=staged/relative;temporary.parent.mkdir(parents=True,exist_ok=True)
                    with archive.open(entry) as src, temporary.open('wb') as dst: shutil.copyfileobj(src,dst,1024*1024)
                    records.append((temporary,root/relative))
            for dep in package.get('dependencies',[]):
                temporary=staged/'Fuses'/dep['name'];temporary.parent.mkdir(parents=True,exist_ok=True)
                source=package_path(package).parent/dep['path']
                if sha(source)!=dep['sha256']: raise ValueError('Dependency checksum mismatch')
                shutil.copy2(source,temporary);records.append((temporary,root/'Fuses'/dep['name']))
            # Preflight conflicts before changing a single installed file.
            for temporary,target in records:
                if target.exists() and (not target.is_file() or (sha(target)!=sha(temporary) and not replace)):
                    raise ValueError(f'Existing file needs replacement permission: {target.name}')
            shared_records={}
            installed_dir=state_dir()/'installed'
            if installed_dir.exists():
                for manifest in installed_dir.glob('*.json'):
                    if manifest!=manifest_path(package_id):
                        for record in _read_json(manifest,{'files':[]})['files']:
                            shared_records[(record['target'],record['sha256'])]=record
            files=[]
            for index,(temporary,target) in enumerate(records):
                checkpoint(45+index/max(1,len(records))*50,f'Installing {index+1}/{len(records)} files')
                digest=sha(temporary);old=previous_by_path.get(str(target),shared_records.get((str(target),digest),{}))
                exists=target.is_file();same=exists and sha(target)==digest
                record={'target':str(target),'sha256':digest,'owned':old.get('owned',not exists),'original_backup':old.get('original_backup')}
                if not same:
                    undo=None
                    if exists:
                        undo=backup_root/str(index);undo.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,undo)
                        if not old and not record['original_backup']: record['original_backup']=str(undo)
                    target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(temporary,target);applied.append((target,undo))
                files.append(record)
            checkpoint(97,'Verifying installed files')
            if any(sha(f['target'])!=f['sha256'] for f in files): raise ValueError('Installation verification failed')
            manifest_path(package_id).parent.mkdir(parents=True,exist_ok=True)
            _save_json(manifest_path(package_id),{'id':package_id,'files':files,'installed_at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'root':str(root)})
            return {'success':True,'message':f"Installed and verified {package['name']}. Restart Resolve, then open the listed Effects Library category.",
                    'locations':package['locations'],'fonts':[font_status(f) for f in package.get('fonts',[])],'target':str(root)}
        except BaseException:
            for target,undo in reversed(applied):
                if undo and undo.exists(): shutil.copy2(undo,target)
                elif target.exists(): target.unlink()
            raise
        finally: shutil.rmtree(staged,ignore_errors=True)


def uninstall(package_id):
    with _lock:
        package_by_id(package_id)
        path=manifest_path(package_id);manifest=_read_json(path,None)
        if not manifest: raise ValueError('No managed installation for this package')
        root=Path(manifest['root']).resolve()
        others=[]
        for file in path.parent.glob('*.json'):
            if file!=path: others.extend(_read_json(file,{'files':[]})['files'])
        shared={f['target'] for f in others}
        changed=[]
        for record in manifest['files']:
            target=Path(record['target'])
            if not target.resolve().is_relative_to(root): raise ValueError('Invalid installation manifest path')
            if target.is_file() and sha(target)!=record['sha256']: changed.append(str(target))
        if changed: raise ValueError('Installed files were modified outside the app. Repair or back them up before removal.')
        # Only files tracked by this package are eligible. Shared/unmanaged files are retained.
        removed=0
        for record in manifest['files']:
            target=Path(record['target'])
            if str(target) in shared: continue
            backup=record.get('original_backup')
            if backup and Path(backup).is_file(): shutil.copy2(backup,target);removed+=1
            elif record['owned'] and target.is_file(): target.unlink();removed+=1
        path.unlink()
        return {'success':True,'message':f'Removed {removed} managed files; originals and shared files were preserved. Restart Resolve.'}


def scan_folder(directory):
    source=Path(directory).expanduser().resolve()
    if not source.is_dir(): raise ValueError('Choose an existing library folder')
    custom=_read_json(state_dir()/'catalog.json',{'packages':[]})['packages']
    known={p['sha256'] for p in packages()};added=[]
    for path in sorted(source.rglob('*.drfx')):
        if '__MACOSX' in path.parts or path.name.startswith('._') or not zipfile.is_zipfile(path):continue
        digest=sha(path)
        if digest in known:continue
        entries=archive_entries(path)
        package={'id':'user-'+digest[:16],'name':path.stem,'file':str(path),'sha256':digest,'bytes':path.stat().st_size,
          'categories':sorted({r.parts[2] for _,r,_,_ in entries}),'template_count':sum(e[0].endswith('.setting') for e in entries),
          'locations':sorted({' → '.join(['Effects Library']+r.parts[2:-1]) for _,r,_,_ in entries if r.suffix=='.setting'})[:12],
          'fonts':[],'notes':[],'dependencies':[],'preview':None,'bundled':False}
        custom.append(package);added.append(package['id']);known.add(digest)
    _save_json(state_dir()/'catalog.json',{'packages':custom})
    return {'success':True,'message':f'Added {len(added)} new packages; duplicate packages skipped.','added':added}
