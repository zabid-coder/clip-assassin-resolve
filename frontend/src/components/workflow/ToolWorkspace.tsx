import { createContext, useContext, useCallback, useEffect, useRef, useState, type ReactNode } from 'react'
interface Tool {id:string;title:string;description:string;icon:ReactNode}
interface Workspace {active:string;register:(tool:Tool)=>()=>void}
const ToolContext=createContext<Workspace | null>(null)
// oxlint-disable-next-line react/only-export-components
export const useToolWorkspace=()=>useContext(ToolContext)
const shortNames:Record<string,string>={create_master_folder:'Folder Setup',master_ingest:'Auto Ingest',snapshot:'Snapshot',magic_bin_organizer:'Bin Organizer',batch_clip_renamer:'Clip Renamer',social_media_reframe:'Reframe',quick_title:'Quick Title',adjustment_layer:'Adjustment Layer',multicam_auto_sync:'Audio Sync',badwords:'BadWords',timecode_cutter:'Timecode Cutter',clip_picker:'Clip Picker',markers_to_timeline:'Markers to Timeline',flag_filter:'Flag Filter',merge_timelines:'Merge Timelines',watermark_track:'Watermark',auto_jcut__lcut:'J-Cut / L-Cut',silence_remover:'Silence Remover',multiplatform_render:'Batch Render',extract_thumbnails:'Thumbnails',auto_youtube_chapters:'YouTube Chapters',shotlist_generator:'Shotlist'}
export function ToolWorkspace({children,enabled,title}:{children:ReactNode;enabled:boolean;title:string}) {
  const [tools,setTools]=useState<Tool[]>([])
  const [active,setActive]=useState('')
  const buttons=useRef<Array<HTMLButtonElement|null>>([])
  const register=useCallback((tool:Tool)=>{
    setTools(prev=>prev.some(t=>t.id===tool.id)?prev:[...prev,tool])
    setActive(prev=>prev||tool.id)
    return()=>setTools(prev=>prev.filter(t=>t.id!==tool.id))
  },[])
  useEffect(()=>{if(active&&!tools.some(t=>t.id===active))setActive(tools[0]?.id||'')},[active,tools])
  if(!enabled)return <>{children}</>
  return <ToolContext.Provider value={{active,register}}><div className="glass-workspace">
    <h1 className="workspace-title">{title}</h1>
    <nav className={`glass-tool-tabs tools-${tools.length}`} aria-label="Section tools" role="tablist">
      {tools.map((tool,index)=><button key={tool.id} ref={el=>{buttons.current[index]=el}} role="tab" id={`tab-${tool.id}`} aria-selected={active===tool.id} aria-controls={active===tool.id?`panel-${tool.id}`:undefined} tabIndex={active===tool.id?0:-1} className={active===tool.id?'selected':''} onClick={()=>setActive(tool.id)} onKeyDown={e=>{let next=index;if(e.key==='ArrowRight'||e.key==='ArrowDown')next=(index+1)%tools.length;else if(e.key==='ArrowLeft'||e.key==='ArrowUp')next=(index-1+tools.length)%tools.length;else if(e.key==='Home')next=0;else if(e.key==='End')next=tools.length-1;else return;e.preventDefault();setActive(tools[next].id);buttons.current[next]?.focus()}}><span aria-hidden="true">{tool.icon}</span>{shortNames[tool.id]||tool.title}</button>)}
    </nav>
    <div className="tool-detail" role="tabpanel" id={`panel-${active}`} aria-labelledby={`tab-${active}`}>{children}</div>
  </div></ToolContext.Provider>
}
