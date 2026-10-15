import { useState } from 'react'
import { Activity, RotateCcw, XCircle, FolderOpen, ExternalLink } from 'lucide-react'
import { api, type Job, type Review } from '../api'
export function JobsPage({jobs,onReview,addLog,activity,clearActivity}:{jobs:Job[];onReview:(r:Review)=>void;addLog:(m:string,t:'info'|'success'|'error')=>void;activity:{msg:string;type:'info'|'success'|'error'}[];clearActivity:()=>void}){
 const titles:Record<string,string>={folder_generate:'Create Project Folders',library_install:'Install Template Package',library_remove:'Remove Managed Installation',cut:'Timecode Cutter',pick_clips:'Clip Picker',jl_cut:'J/L Cuts',silence_remove:'Silence Remover',batch_render:'Queue Render Jobs',start_render:'Render Videos',youtube_chapters:'YouTube Chapters',transcribe:'Transcribe Media',youtube_upload:'Upload to YouTube','badwords/clean':'BadWords Cleaner'}
 const [expanded,setExpanded]=useState('')
 const [filter,setFilter]=useState('all')
 const request=async(fn:()=>Promise<unknown>)=>{try{await fn()}catch(e){addLog(e instanceof Error?e.message:'Job action failed','error')}}
 return <div className="page-stack"><div className="section-heading"><div><div className="eyebrow">Work history</div><h1>Jobs & results</h1><p>Track work, inspect outputs, and cancel at safe checkpoints.</p></div><Activity size={24}/></div>
 <div className="segmented-control">{['all','active','succeeded','failed'].map(f=><button className={filter===f?'selected':''} key={f} onClick={()=>setFilter(f)}>{f==='all'?'All jobs':f==='active'?'In progress':f==='succeeded'?'Completed':'Needs attention'}</button>)}</div>
 {jobs.filter(j=>filter==='all'||(filter==='active'?['running','queued','cancelling'].includes(j.status):filter==='failed'?['failed','interrupted','cancelled'].includes(j.status):j.status===filter)).map(job=><article className="job-card" key={job.id}>
 <div className="section-heading"><div><span className={`status-badge ${job.status}`}>{job.status}</span><h3>{titles[job.operation]||job.operation.replaceAll('_',' ').replace('/',' · ')}</h3><p>{job.source.project || 'Local workflow'}{job.source.timeline?' · '+job.source.timeline:''}</p></div><span className="muted">{job.elapsed_seconds.toFixed(1)}s</span></div>
 {['running','queued','cancelling'].includes(job.status) && <><progress aria-label="Job progress" value={job.progress} max={100}/><p className="muted">{job.progress}% · Progress advances at completed checkpoints.</p></>}
 <p className="job-message">{job.message}</p>
 <div className="action-row"><button className="text-button" onClick={()=>setExpanded(expanded===job.id?'':job.id)}>{expanded===job.id?'Hide details':'View details'}</button>
 {['running','queued'].includes(job.status)&&<button className="secondary-button" onClick={()=>request(()=>api(`jobs/${job.id}/cancel`,{}))}><XCircle size={15}/>Cancel</button>}
 {['failed','cancelled','interrupted'].includes(job.status)&&<button className="secondary-button" onClick={()=>request(async()=>onReview(await api(`jobs/${job.id}/retry`,{})))}><RotateCcw size={15}/>Review retry</button>}
 {job.result?.target&&<button className="secondary-button" onClick={()=>request(()=>api(`open_folder?path=${encodeURIComponent(job.result!.target!)}`))}><FolderOpen size={15}/>Open output folder</button>}
 {job.operation==='batch_render'&&job.status==='succeeded'&&job.result?.render_job_ids?.length&&<button className="primary-button" onClick={()=>request(async()=>onReview(await api('jobs/preview',{operation:'start_render',payload:{job_ids:job.result!.render_job_ids}})))}>Review & render videos</button>}
 {job.result?.url&&<a className="secondary-button" href={job.result.url} target="_blank" rel="noreferrer"><ExternalLink size={15}/>Open video</a>}
 </div>
 {expanded===job.id&&<div className="job-details">{job.result?.text&&<textarea readOnly rows={8} aria-label="Transcript result" value={job.result.text}/>}<pre>{job.result?.locations?.join('\n') || ''}</pre><ol>{job.logs.map((log,i)=><li key={i}><time>{new Date(log.time).toLocaleTimeString()}</time>{log.message}</li>)}</ol></div>}
 </article>)}
 {!jobs.length&&<div className="empty-state"><Activity size={28}/><h3>Your work will appear here</h3><p>Choose a tool, review the settings, and run your first job.</p></div>}
 <details className="activity-panel"><summary>App activity <span>{activity.length}</span></summary><div className="activity-heading"><p className="muted">Activity from this session</p><button className="text-button" onClick={clearActivity}>Clear activity</button></div>{activity.length?activity.map((entry,index)=><p key={index} className={`activity-entry activity-${entry.type}`}>{entry.msg}</p>):<p className="muted">No activity yet.</p>}</details>
 </div>
}
