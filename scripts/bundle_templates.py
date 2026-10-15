"""Build the self-contained catalog from licensed packages supplied by the user."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'templates' / 'bundled'
FONT_URLS = {'Playfair Display':'https://fonts.google.com/specimen/Playfair+Display','Inter':'https://fonts.google.com/specimen/Inter', 'Poppins':'https://fonts.google.com/specimen/Poppins',
 'Open Sans':'https://fonts.google.com/specimen/Open+Sans','League Spartan':'https://fonts.google.com/specimen/League+Spartan',
 'DM Serif Display':'https://fonts.google.com/specimen/DM+Serif+Display','Manrope':'https://www.1001fonts.com/manrope-font.html',
 'Coolvetica':'https://www.dafont.com/coolvetica.font'}

def build(source):
    packages=[]
    for path in sorted(source.rglob('*.drfx')):
        if '__MACOSX' in path.parts or path.name.startswith('._'): continue
        if not zipfile.is_zipfile(path): raise ValueError(f'Invalid package: {path}')
        digest=hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()
        slug=re.sub(r'[^a-z0-9]+','-',path.stem.lower()).strip('-')
        folder=DEST/slug; folder.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,folder/path.name)
        pack=path.parent.parent if path.parent.name.lower() in ('macros',) else path.parent
        notes=[]; note_text=''
        for note in sorted(pack.rglob('*.txt')):
            if '__MACOSX' in note.parts: continue
            relative=Path('notes')/note.relative_to(pack)
            (folder/relative).parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(note,folder/relative)
            notes.append({'name':note.name,'path':relative.as_posix()})
            note_text += '\n'+note.read_text(encoding='utf-8',errors='replace')
        dependencies=[]
        for fuse in sorted(pack.rglob('*.fuse')):
            if '__MACOSX' in fuse.parts: continue
            relative=Path('dependencies')/'Fuses'/fuse.name
            (folder/relative).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(fuse,folder/relative)
            dependencies.append({'name':fuse.name,'path':relative.as_posix(),'sha256':hashlib.sha256(fuse.read_bytes()).hexdigest()})
        fonts=set()
        with zipfile.ZipFile(path) as archive:
            names=[n for n in archive.namelist() if not n.endswith('/') and '__MACOSX' not in n and not Path(n).name.startswith('._')]
            settings=[n for n in names if n.lower().endswith('.setting')]
            categories=sorted({n.split('/')[1] for n in settings if n.startswith('Edit/') and len(n.split('/'))>2})
            locations=sorted({' → '.join(['Effects Library']+n.split('/')[1:-1]) for n in settings if n.startswith('Edit/')})
            for entry in settings:
                text=archive.read(entry).decode('utf-8',errors='replace')
                fonts.update(re.findall(r'\bFont\s*=\s*Input\s*\{\s*Value\s*=\s*"([^"]+)"',text))
            previews=[n for n in names if n.lower().endswith(('.png','.jpg','.jpeg'))]
            preview=None
            for entry in previews:
                if archive.getinfo(entry).file_size<2*1024*1024:
                    preview='preview'+Path(entry).suffix.lower();(folder/preview).write_bytes(archive.read(entry));break
        for family,url in FONT_URLS.items():
            if url in note_text or url.replace('+',' ') in note_text: fonts.add(family)
        package={'id':slug,'name':path.stem,'file':f'{slug}/{path.name}','sha256':digest,'bytes':path.stat().st_size,
          'categories':categories,'template_count':len(settings),'locations':locations[:12],
          'fonts':[{'family':f,'url':FONT_URLS.get(f,'')} for f in sorted(fonts)], 'notes':notes,
          'dependencies':dependencies,'preview':f'{slug}/{preview}' if preview else None,'bundled':True,
          'min_resolve_version':20 if 'neo' in path.as_posix().lower() else None}
        packages.append(package)
    DEST.mkdir(parents=True,exist_ok=True)
    (DEST/'catalog.json').write_text(json.dumps({'version':1,'packages':packages},indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'packages':len(packages),'templates':sum(p['template_count'] for p in packages),'bytes':sum(p['bytes'] for p in packages)}))

if __name__=='__main__':build(Path(sys.argv[1]))
