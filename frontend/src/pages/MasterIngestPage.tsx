import { useCallback, useEffect, useState } from 'react'
import { FolderTree, FolderPlus, Plus, Pencil, Copy, MoreHorizontal } from 'lucide-react'
import { ActionButton, FeatureCard, InputField } from '../components/ui'
import { FolderPresetBuilder, type FolderPreset } from '../components/workflow/FolderPresetBuilder'
import { api } from '../api'
interface Props {isDashboard:boolean;favorites:string[];toggleFavorite:(id:string)=>void;loading:Record<string,boolean>;addLog:(msg:string,type:'info'|'success'|'error')=>void;runTask:(endpoint:string,payload:any,buttonId:string)=>void}
export function MasterIngestPage({isDashboard,favorites,toggleFavorite,loading,addLog,runTask}:Props){
 const [presets,setPresets]=useState<FolderPreset[]>([])
 const [selected,setSelected]=useState(localStorage.getItem('clipAssassin:folderPresetId')||'')
 useEffect(()=>{if(selected)localStorage.setItem('clipAssassin:folderPresetId',selected)},[selected])
 const [values,setValues]=useState<Record<string,string>>({})
 const [preview,setPreview]=useState('')
 const [builder,setBuilder]=useState<FolderPreset|null|undefined>(undefined)
 const [error,setError]=useState('')
 const refresh=useCallback(async()=>{try{const data=await api('templates');setPresets(data.templates);setSelected(prev=>data.templates.some((p:FolderPreset)=>p.id===prev)?prev:data.templates[0]?.id||'')}catch(e){setError(e instanceof Error?e.message:'Could not load presets')}},[])
 useEffect(()=>{void refresh();const listener=(event:Event)=>{const target=(event as CustomEvent<string>).detail;localStorage.setItem('clipAssassin:masterFolderInput',target);const input=document.getElementById('masterFolderInput') as HTMLInputElement|null;if(input)input.value=target};window.addEventListener('folder-generated',listener);return()=>window.removeEventListener('folder-generated',listener)},[refresh])
 const active=presets.find(p=>p.id===selected)
 useEffect(()=>{if(!active)return;const next:Record<string,string>={project:'',client:'',date:new Date().toLocaleDateString('en-CA'),operator:''};active.parameters.forEach(p=>{next[p.name]=p.default??''});setValues(next);setPreview('')},[active])
 const act=async(fn:()=>Promise<void>)=>{setError('');try{await fn();return true}catch(e){setError(e instanceof Error?e.message:'Operation failed');return false}}
 const update=(name:string,value:string)=>{setValues(prev=>({...prev,[name]:value}));setPreview('')}
 return <div className="page-stack">

 <FeatureCard hidden={isDashboard&&!favorites.includes('create_master_folder')} id="create_master_folder" title="Master Folder Setup" icon={<FolderTree size={20}/>} description="Create folders from a saved preset. Add your own presets here." helpText="1. Select a preset or create one. 2. Enter project details and choose a parent directory. 3. Preview the complete structure before creating folders." isFavorite={favorites.includes('create_master_folder')} onToggleFavorite={()=>toggleFavorite('create_master_folder')}>
 <div className="preset-toolbar"><select aria-label="Folder Template Preset" value={selected} onChange={e=>setSelected(e.target.value)}>{presets.map(p=><option key={p.id} value={p.id}>{p.name}{p.id.startsWith('custom-')?' · My preset':''}</option>)}</select><button className="secondary-button" onClick={()=>setBuilder(null)}><Plus size={14}/>New Preset</button><details className="preset-menu"><summary aria-label="Preset actions"><MoreHorizontal size={20}/></summary><div className="preset-menu-items"><button disabled={!active} onClick={()=>setBuilder(active)}><Pencil size={14}/>Edit</button><button disabled={!active} onClick={()=>setBuilder(active?{...structuredClone(active),id:'',name:active.name+' copy'}:null)}><Copy size={14}/>Duplicate</button>{selected.startsWith('custom-')&&<ActionButton text="Delete preset" variant="secondary" requiresConfirm onClick={()=>act(async()=>{await api(`templates/${selected}`,undefined,'DELETE');await refresh();addLog('Custom preset deleted','info')})}/>}</div></details></div>

 <div className="form-grid">{active&&[...Object.entries(active.builtin_params||{}).map(([name,p])=>({name,label:p.label,type:p.type,required:p.required,options:null as string[]|null})),...active.parameters].map(param=><label key={param.name} className="field-label">{param.label}{param.required?' *':''}{param.type==='select'?<select value={values[param.name]||''} onChange={e=>update(param.name,e.target.value)}>{param.options?.map(option=><option key={option}>{option}</option>)}</select>:param.type==='boolean'?<select value={values[param.name]||'false'} onChange={e=>update(param.name,e.target.value)}><option value="false">No</option><option value="true">Yes</option></select>:<input type={param.type==='number'?'number':param.type==='date'?'date':'text'} value={values[param.name]||''} onChange={e=>update(param.name,e.target.value)}/>}</label>)}</div>
 <InputField id="createParentFolderInput" browseType="folder" placeholder="Parent directory for this project"/>
 {error&&<p className="error-note">{error}</p>}
 {preview&&<pre className="folder-preview" aria-label="Expanded folder preview">{preview}</pre>}
 <div className="action-row"><button className="secondary-button" disabled={!active} onClick={()=>act(async()=>{const data=await api('templates/preview',{template_id:selected,parameters:values});setPreview(data.preview_tree)})}>Preview Structure</button><button className="primary-button" disabled={!active} onClick={()=>runTask('folder_generate',{template_id:selected,parameters:values,base_path:(document.getElementById('createParentFolderInput') as HTMLInputElement).value},'create_master_folder')}>Create folders</button></div>
 </FeatureCard>
 {builder!==undefined&&<FolderPresetBuilder key={builder?.id||'new'} initial={builder||undefined} onClose={()=>setBuilder(undefined)} onSaved={preset=>{setBuilder(undefined);void refresh().then(()=>setSelected(preset.id));addLog('Folder preset saved and added to this menu','success')}}/>}
 <FeatureCard hidden={isDashboard&&!favorites.includes('master_ingest')} id="master_ingest" title="Auto Ingest" icon={<FolderPlus size={20}/>} description="Create a versioned Resolve project from your footage folder." helpText="Choose your project root. Camera, day and card folders can be nested in any order. Review the folder-to-timeline mapping before confirming. This creates a new Resolve project and references supported media in its existing location." isFavorite={favorites.includes('master_ingest')} onToggleFavorite={()=>toggleFavorite('master_ingest')}>
 <InputField id="masterFolderInput" browseType="folder" placeholder="Project footage folder"/>
 <ActionButton text="Auto Ingest" isLoading={loading.master_ingest} onClick={()=>runTask('master_ingest',{master_folder_path:(document.getElementById('masterFolderInput') as HTMLInputElement).value.trim()},'master_ingest')}/>
 </FeatureCard>
 </div>
}
