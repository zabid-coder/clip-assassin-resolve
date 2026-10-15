import { useEffect } from 'react'
import { X, ArrowRight, AlertTriangle } from 'lucide-react'
import type { Review } from '../../api'
export function ReviewDialog({review,busy,onClose,onSubmit}:{review:Review|null;busy:boolean;onClose:()=>void;onSubmit:()=>void}) {
  useEffect(()=>{if(!review)return;const listener=(e:KeyboardEvent)=>{if(e.key==='Escape'&&!busy)onClose()};window.addEventListener('keydown',listener);return()=>window.removeEventListener('keydown',listener)},[review,busy,onClose])
  if(!review)return null
  const labels:Record<string,string>={base_path:'Parent directory',target_dir:'Output directory',target_path:'Output location',master_folder_path:'Project folder',clip_name:'Clip name filter',cut_type:'Cut type',overlap_frames:'Overlap (frames)',threshold_db:'Silence threshold (dB)',min_silence_ms:'Minimum silence (ms)',padding_ms:'Audio padding (ms)',preset_name:'Render preset',image_path:'Watermark image',audio_path:'Media file',video_path:'Video file',template_path:'Word template',replace:'Back up and replace existing files',provider:'Transcription provider',timecodes:'Time ranges',reverse:'Keep only these ranges',scope:'Rename scope'}
  const settings=Object.entries(review.settings).flatMap(([key,value])=>key==='parameters'?Object.entries(value as Record<string,unknown>):[[key,value]]).filter(([key])=>!['allow_cloud','template_id','package_id','job_ids'].includes(String(key)))
  const format=(value:unknown):string=>Array.isArray(value)?value.join(', '):typeof value==='boolean'?value?'Yes':'No':typeof value==='object'?JSON.stringify(value):String(value)||'Default'

  return <div className="modal-backdrop"><section role="dialog" aria-modal="true" aria-label="Review operation" className="review-dialog"><div className="section-heading"><div><div className="eyebrow">Review</div><h2>{review.title}</h2></div><button className="icon-button" aria-label="Close review" onClick={onClose} disabled={busy}><X size={20}/></button></div>
    <div className="review-source"><span className="eyebrow">Source</span><strong>{review.source.project || 'Local files'}</strong><span>{review.source.timeline || 'No timeline changes required'}</span></div>
    {review.details.length>0 && <ul className="review-details">{review.details.map((text,i)=><li key={i}>{text}</li>)}</ul>}
    <dl className="review-settings">{settings.map(([key,value])=><div key={String(key)}><dt>{labels[String(key)]||String(key).replaceAll('_',' ')}</dt><dd>{format(value)}</dd></div>)}</dl>
    {review.warnings.map((warning,i)=><p className="notice" key={i}><AlertTriangle size={15}/>{warning}</p>)}
    {review.errors.map((error,i)=><p className="error-note" key={i}>{error}</p>)}
    <div className="action-row"><button className="secondary-button" onClick={onClose} disabled={busy}>Back to settings</button><button className="primary-button" disabled={!review.ready || busy} onClick={onSubmit}>{busy?'Adding to queue…':'Confirm & run'}<ArrowRight size={16}/></button></div>
  </section></div>
}
