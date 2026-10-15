import { BarChart3 } from 'lucide-react'
import { ActionButton } from '../components/ui'
import type { ProjectStatsResponse } from '../types/api'

interface Props {
  API_BASE: string
  favorites: string[]
  setFavorites: (v: string[]) => void
  loading: Record<string, boolean>
  setLoading: React.Dispatch<React.SetStateAction<Record<string, boolean>>>
  projectStats: ProjectStatsResponse | null
  setProjectStats: (v: ProjectStatsResponse) => void
  addLog: (msg: string, type: 'info' | 'success' | 'error') => void
}

export function DashboardPage({ API_BASE, favorites, setFavorites, loading, setLoading, projectStats, setProjectStats, addLog }: Props) {
  return (
    <>
      <div className="section-heading dashboard-heading"><div><h1>Your workspace</h1><p>Project stats and your pinned tools.</p></div>{favorites.length>0&&<button className="secondary-button" onClick={()=>setFavorites([])}>Reset pins</button>}</div>

      <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 grid grid-cols-1 md:grid-cols-2 gap-5 items-start mb-5">
        <div className="bg-black/20 backdrop-blur-3xl border border-white/5 rounded-[20px] p-6 shadow-2xl md:col-span-2">
          <h3 className="text-sm font-semibold mb-4 text-white/80 uppercase tracking-wider flex items-center gap-2">
            <BarChart3 size={16} className="text-brand-primary" /> Project Stats Dashboard
          </h3>
          <div className="mb-4">
            <ActionButton
              text="Refresh Stats"
              category="neutral" variant="secondary"
              isLoading={loading['proj_stats']}
              onClick={async () => {
                setLoading(prev => ({ ...prev, proj_stats: true }))
                try {
                  const res = await fetch(`${API_BASE}/project_stats`)
                  const data = await res.json()
                  setProjectStats(data)
                  if (data.success) addLog(`Loaded stats for ${data.project_name}`, 'success')
                } catch { addLog('Failed to get project stats', 'error') }
                finally { setLoading(prev => ({ ...prev, proj_stats: false })) }
              }}
            />
          </div>
          {projectStats?.success ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-black/40 p-4 rounded-xl border border-white/5">
                <p className="text-[10px] text-white/40 uppercase tracking-widest mb-1">Total Timelines</p>
                <p className="text-2xl font-semibold text-white/90">{projectStats.timeline_count}</p>
              </div>
              <div className="bg-black/40 p-4 rounded-xl border border-white/5">
                <p className="text-[10px] text-white/40 uppercase tracking-widest mb-1">Total Duration</p>
                <p className="text-2xl font-semibold text-white/90">{projectStats.total_duration_seconds}s</p>
              </div>
              <div className="bg-black/40 p-4 rounded-xl border border-white/5">
                <p className="text-[10px] text-white/40 uppercase tracking-widest mb-1">Used Clips</p>
                <p className="text-2xl font-semibold text-white/90">{projectStats.total_clips_used}</p>
              </div>
              <div className="bg-black/40 p-4 rounded-xl border border-white/5">
                <p className="text-[10px] text-white/40 uppercase tracking-widest mb-1">Media Pool Files</p>
                <p className="text-2xl font-semibold text-white/90">{projectStats.total_pool_clips}</p>
              </div>
            </div>
          ) : (
            <p className="text-xs text-white/30 italic">Click refresh to load project statistics.</p>
          )}
        </div>
      </div>
    </>
  )
}
