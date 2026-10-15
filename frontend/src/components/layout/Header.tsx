import { useState } from 'react'
import { Folder, Clapperboard, RefreshCw, ShieldCheck, Unplug } from 'lucide-react'
interface HeaderProps {
 status:{connected:boolean;message:string};handleConnect:()=>void|Promise<void>;
 context:{project:string;timelines:string[];current_timeline:string};handleSetTimeline:(name:string)=>void;
 stats:{name:string;fps:string;clips:number;timecode:string};activeTab?:string
}
export function Header({status,handleConnect,context,handleSetTimeline}:HeaderProps) {
 const [connecting,setConnecting]=useState(false)
 const reconnect=async()=>{setConnecting(true);try{await handleConnect()}finally{setConnecting(false)}}
 const state=connecting?'connecting':status.connected?'connected':'disconnected'
 return <header className="app-header"><div className="header-context">
   <div className="header-project context-tile" title={context.project||'No project'}><Folder size={18}/><div><span className="context-label">Project</span><strong>{context.project||'No project open'}</strong></div></div>
   <label className="header-timeline context-tile"><Clapperboard size={18}/><span><span className="context-label">Timeline</span><select aria-label="Active timeline" value={context.current_timeline||''} disabled={!context.timelines.length} onChange={e=>handleSetTimeline(e.target.value)}>{!context.timelines.length&&<option value="">No timeline selected</option>}{context.timelines.map(name=><option key={name} value={name}>{name}</option>)}</select></span></label>
 </div><button className={`resolve-status ${state}`} disabled={connecting} title={`${status.message} · Click to reconnect`} onClick={reconnect} aria-label={connecting?'Reconnecting to Resolve':status.connected?'Resolve connected — reconnect':'Connect to Resolve'}><span className="resolve-status-icon">{connecting?<RefreshCw size={18} className="animate-spin"/>:status.connected?<ShieldCheck size={19}/>:<Unplug size={18}/>}</span><span className="resolve-status-copy"><span>DaVinci Resolve</span><strong aria-live="polite">{connecting?'Reconnecting…':status.connected?'Connected':'Disconnected'}</strong></span><span className="resolve-status-end" aria-hidden="true"><span className="connection-dot"/>{!connecting&&<RefreshCw size={12} className="reconnect-hint"/>}</span></button></header>
}
