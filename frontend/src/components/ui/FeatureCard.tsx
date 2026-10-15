import React, { useEffect, useRef } from 'react'
import { Pin } from 'lucide-react'
import { useToolWorkspace } from '../workflow/ToolWorkspace'
import { ToolHelp } from './ToolHelp'
import { toolHelp } from '../workflow/toolHelp'
import type { CategoryKey } from './design-tokens'
interface Props {icon:React.ReactNode;title:string;category?:CategoryKey;description?:string;warning?:string;helpText?:string;children:React.ReactNode;className?:string;id?:string;isFavorite?:boolean;onToggleFavorite?:()=>void;hidden?:boolean}
export function FeatureCard({icon,title,description='',warning,helpText,children,id,isFavorite,onToggleFavorite,hidden=false}:Props){
  const workspace=useToolWorkspace()
  const register=workspace?.register
  const toolId=id || title
  const navIcon=useRef(icon)
  useEffect(()=>{if(register && !hidden)return register({id:toolId,title,description,icon:navIcon.current})},[register,toolId,title,description,hidden])
  if(hidden || (workspace && workspace.active!==toolId))return null
  return <section className="tool-card">
    <div className="tool-card-header">{!workspace&&<span className="tool-icon">{icon}</span>}<div><h2>{title}</h2><p>{description}</p></div><ToolHelp title={title} details={helpText||toolHelp.find(tool=>tool.id===toolId)?.help||description}/>{onToggleFavorite && <button className={`pin-button ${isFavorite?'active':''}`} onClick={onToggleFavorite} title={isFavorite?'Unpin from Dashboard':'Pin to Dashboard'} aria-label={isFavorite?'Unpin from Dashboard':'Pin to Dashboard'}><Pin size={17}/></button>}</div>
    <div className="tool-form">{children}</div>
    {warning && <p className="notice">{warning}</p>}
  </section>
}
