import { useEffect, useId, useRef, useState } from 'react'
import { CircleHelp, X } from 'lucide-react'

/** Contextual help stays beside the tool; keyboard and pointer dismissal are local. */
export function ToolHelp({title,details}:{title:string;details:string}) {
  const [open,setOpen]=useState(false)
  const root=useRef<HTMLDivElement>(null)
  const trigger=useRef<HTMLButtonElement>(null)
  const close=useRef<HTMLButtonElement>(null)
  const id=useId()
  useEffect(()=>{
    if(!open)return
    close.current?.focus()
    const outside=(e:PointerEvent)=>{if(!root.current?.contains(e.target as Node))setOpen(false)}
    const focusOutside=(e:FocusEvent)=>{if(!root.current?.contains(e.target as Node))setOpen(false)}
    const escape=(e:KeyboardEvent)=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();setOpen(false);trigger.current?.focus()}}
    document.addEventListener('pointerdown',outside)
    document.addEventListener('keydown',escape)
    document.addEventListener('focusin',focusOutside)
    return()=>{document.removeEventListener('pointerdown',outside);document.removeEventListener('keydown',escape);document.removeEventListener('focusin',focusOutside)}
  },[open])
  return <div className="tool-help-anchor" ref={root}>
    <button ref={trigger} className="tool-help" aria-label={`Help for ${title}`} aria-expanded={open} aria-controls={open?id:undefined} title="Tool details" onClick={()=>setOpen(value=>!value)}><CircleHelp size={18}/></button>
    {open&&<div className="tool-help-popover" id={id} role="dialog" aria-labelledby={`${id}-title`}><div className="popover-heading"><h3 id={`${id}-title`}>{title}</h3><button ref={close} className="icon-button" aria-label="Close tool details" onClick={()=>{setOpen(false);trigger.current?.focus()}}><X size={16}/></button></div><p>{details}</p></div>}
  </div>
}
