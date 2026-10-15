"""Read-only, deterministic footage grouping shared by review and ingestion."""
import hashlib
import json
import re
from pathlib import Path

SUPPORTED_EXTENSIONS = {
    '.mp4', '.mov', '.mkv', '.m4v', '.avi', '.braw', '.arri', '.mxf', '.r3d',
    '.mp3', '.wav', '.aac', '.m4a', '.flac', '.aiff',
    '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.exr', '.dng',
}
IGNORED_FOLDERS = {
    'davinci resolve database', 'davinci database', 'database', 'after effects',
    'fcpx', 'illustrator', 'photoshop', 'premiere', 'export', 'exports',
    'production documents', 'documents', '__macosx', 'cacheclip',
    'audio & music', 'audio & voiceover', 'bg music', 'audio', 'music', 'sound',
    '03_audio', 'logos & branding', 'graphics & assets', 'motion graphics',
    'client approvals & exports', 'graphics', 'logos',
}
RAW_NAMES = {'raw footages', 'raw footage', 'footage', 'raw', '01_raw',
             '01_raw_footage', '01_raw footages', '02_footage', 'camera', 'production'}
AUDIO_NAMES = {'bg music', 'audio', 'music', 'sound', 'audio & music', 'audio & voiceover', '03_audio'}
# These directories belong to the enclosing card, rather than a camera/day group.
CARD_INTERNALS = {'private', 'avchd', 'bdmv', 'stream', 'm4root', 'xdroot', 'dcim', 'contents', 'clip', 'clips', 'video', 'avf_info'}


def natural(value):
    return tuple((1, int(p)) if p.isdigit() else (0, p.casefold()) for p in re.split(r'(\d+)', str(value)))


def plan_ingest(folder):
    root = Path(folder).expanduser().absolute()
    if not root.is_dir() or root.is_symlink():
        raise ValueError('Choose an existing project footage folder (not a symlink).')
    groups, audio, seen = {}, [], set()
    signatures = []

    def children(path):
        return sorted((p for p in path.iterdir() if not p.name.startswith('.') and not p.is_symlink()), key=lambda p: natural(p.name))

    def add(file, owner, audio_only=False):
        if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return
        stat = file.stat()
        identity = (stat.st_dev, stat.st_ino)
        if identity in seen:
            return
        seen.add(identity)
        signatures.append((str(file.relative_to(root)), stat.st_size, stat.st_mtime_ns))
        if audio_only:
            audio.append(str(file))
        else:
            groups.setdefault(owner, []).append(str(file))

    def visit(path, owner=None, audio_only=False):
        # owner is fixed once inside a camera's storage structure.
        entries = children(path)
        for item in entries:
            if item.is_file():
                add(item, owner or path, audio_only)
        for item in entries:
            if not item.is_dir():
                continue
            name = item.name.casefold()
            if not audio_only and name in IGNORED_FOLDERS and not (owner and name in AUDIO_NAMES):
                continue
            fixed = owner
            if not fixed and (name in CARD_INTERNALS or name.endswith('.rdc')):
                fixed = path
            visit(item, fixed, audio_only)

    entries = children(root)
    raw_roots = [p for p in entries if p.is_dir() and p.name.casefold() in RAW_NAMES]
    if raw_roots:
        for path in raw_roots:
            visit(path)
        # Direct media at project level remains its own group.
        for path in entries:
            if path.is_file():
                add(path, root)
    else:
        visit(root)
    for path in entries:
        if path.is_dir() and path.name.casefold() in AUDIO_NAMES:
            visit(path, audio_only=True)

    result = []
    used_names = set()
    for path in sorted(groups, key=lambda p: natural(p.relative_to(root))):
        relative = path.relative_to(root)
        parts = list(relative.parts) or ['Loose Media']
        # Hide the common wrapper only when it cannot make two roots ambiguous.
        if len(raw_roots) == 1 and parts[0].casefold() in RAW_NAMES:
            parts = parts[1:] or ['Loose Media']
        base = ' · '.join(part.replace(' · ', ' - ') for part in parts) + ' Timeline'
        name, n = base, 2
        while name.casefold() in used_names:
            name = f'{base} ({n})'
            n += 1
        used_names.add(name.casefold())
        result.append({'folder':str(relative) if relative.parts else '.', 'parts':list(relative.parts),
                       'timeline':name, 'files':groups[path]})
    fingerprint = hashlib.sha256(json.dumps(signatures, sort_keys=True).encode()).hexdigest()
    return {'root':str(root), 'groups':result, 'audio_files':audio, 'fingerprint':fingerprint,
            'file_count':sum(len(g['files']) for g in result), 'audio_count':len(audio)}
