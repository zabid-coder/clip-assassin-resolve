export const API = import.meta.env.DEV ? 'http://localhost:8000/api' : '/api'
export async function api<T = any>(path: string, body?: unknown, method?: string): Promise<T> {
  const response = await fetch(`${API}/${path}`, {method: method || (body === undefined ? 'GET' : 'POST'), headers: {'Content-Type':'application/json'}, ...(body === undefined ? {} : {body:JSON.stringify(body)})})
  const data = await response.json()
  if (!response.ok || data.success === false) throw new Error(typeof data.detail === 'string' ? data.detail : Array.isArray(data.detail) ? data.detail.map((e: {msg:string}) => e.msg).join('; ') : data.message || data.preview_tree || `Request failed (${response.status})`)
  return data
}
export interface Review {ready:boolean;title:string;source:Record<string,string>;details:string[];settings:Record<string,unknown>;warnings:string[];errors:string[];preview_token:string}
export interface Job {id:string;operation:string;status:string;progress:number;message:string;elapsed_seconds:number;created_at:string;logs:{time:string;message:string}[];source:Record<string,string>;payload:Record<string,unknown>;result?:{success:boolean;message:string;target?:string;url?:string;text?:string;locations?:string[];source?:Record<string,string>;render_job_ids?:string[]}}
export type RunTask = (operation:string, payload:Record<string,unknown>, buttonId:string) => unknown
