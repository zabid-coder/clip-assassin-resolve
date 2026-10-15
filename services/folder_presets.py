"""Folder templates shared by the master-setup workflow and visual preset builder."""
from pathlib import Path
from models.ingest_template import IngestTemplate,FolderNode
from services.builtin_templates import get_builtin_templates,get_builtin_template_by_id
import db


def all_templates():
    return [t.to_dict() for t in get_builtin_templates()]+db.get_folder_templates()


def find(template_id):
    builtin=get_builtin_template_by_id(template_id)
    if builtin:return builtin
    return next((IngestTemplate(**t) for t in db.get_folder_templates() if t['id']==template_id),None)


def capture(directory):
    root=Path(directory).expanduser().resolve()
    if not root.is_dir(): raise ValueError('Choose an existing folder')
    count=0
    def walk(path,depth=0):
        nonlocal count
        if depth>15:raise ValueError('Folder structure is deeper than 15 levels')
        nodes=[]
        for item in sorted(path.iterdir(),key=lambda p:p.name.casefold()):
            if item.name.startswith('.') or item.is_symlink() or not item.is_dir(): continue
            count+=1
            if count>2000:raise ValueError('Folder structure contains more than 2000 folders')
            nodes.append({'name':item.name,'type':'folder','children':walk(item,depth+1)})
        return nodes
    structure=[{'name':'{project}','type':'folder','children':walk(root)}]
    return {'success':True,'name':root.name,'structure':structure,'folder_count':count+1,
            'message':'Folder names only were captured. Files and media are not copied.'}
