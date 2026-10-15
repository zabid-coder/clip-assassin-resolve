import { useState, useEffect, useRef } from 'react'
import {
  Scissors, Target, MapPin, Combine,
  MonitorUp, Video, Camera, PenLine, VolumeX,
  FolderTree, Smartphone
} from 'lucide-react'
import { Header } from './components/layout/Header'
import { Sidebar } from './components/layout/Sidebar'
import { CommandPalette } from './components/ui'
import { DashboardPage } from './pages/DashboardPage'
import { MasterIngestPage } from './pages/MasterIngestPage'
import { MagicToolsPage } from './pages/MagicToolsPage'
import { CutToolsPage } from './pages/CutToolsPage'
import { ProcessPage } from './pages/ProcessPage'
import { ExportPage } from './pages/ExportPage'
import { TemplatesPage } from './pages/TemplatesPage'
import { SettingsPage } from './pages/SettingsPage'
import { ManualPage } from './pages/ManualPage'
import { JobsPage } from './pages/JobsPage'
import { ConnectionsPage } from './pages/ConnectionsPage'
import { ToolWorkspace } from './components/workflow/ToolWorkspace'
import { ReviewDialog } from './components/workflow/ReviewDialog'
import { api, type Job, type Review } from './api'
import type {
  AppStatus, AppStats, AppContext, LogEntry, Toast,
  ProjectStatsResponse, BadWordsScanResponse
} from './types/api'

async function readResponse(res: Response) {
  const data = await res.json()
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : Array.isArray(data.detail) ? data.detail.map((e: { msg: string }) => e.msg).join('; ') : data.message || `Request failed (${res.status})`)
  return data
}

const API_BASE = import.meta.env.DEV ? 'http://localhost:8000/api' : '/api'

const themes = [
  { name: 'Purple', primary: '#7e5cf5', bg: '#111318' },
  { name: 'Rose', primary: '#f43f5e', bg: '#111318' },
  { name: 'Emerald', primary: '#10b981', bg: '#111318' },
  { name: 'Cyan', primary: '#06b6d4', bg: '#111318' },
  { name: 'Amber', primary: '#f59e0b', bg: '#111318' },
]

export default function App() {
  const pollInFlight = useRef(false)
  const jobsPolling = useRef(false)
  const seenJobs = useRef<Record<string,string> | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [review, setReview] = useState<Review | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [chapterOutput, setChapterOutput] = useState('')
  const [activeTab, setActiveTab] = useState('dashboard')

  const [isCmdPaletteOpen, setIsCmdPaletteOpen] = useState(false)
  const [status, setStatus] = useState<AppStatus>({ connected: false, message: 'Checking connection...' })
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [toasts, setToasts] = useState<Toast[]>([])
  const [stats, setStats] = useState<AppStats>({ name: '', fps: '', clips: 0, timecode: '' })
  const [templates, setTemplates] = useState<string[]>([])
  const [context, setContext] = useState<AppContext>({ project: '', timelines: [], current_timeline: '' })
  const [selectedMergeTimelines, setSelectedMergeTimelines] = useState<string[]>([])
  const [selectedBatchTimelines, setSelectedBatchTimelines] = useState<string[]>([])
  const [loading, setLoading] = useState<Record<string, boolean>>({})
  const [bwScan, setBwScan] = useState<BadWordsScanResponse | null>(null)
  const [bwColors, setBwColors] = useState<Record<string, boolean>>({ Red: true, Blue: true, Green: false })
  const [projectStats, setProjectStats] = useState<ProjectStatsResponse | null>(null)
  const [shotlistFormat, setShotlistFormat] = useState('csv')
  const [animationsEnabled, setAnimationsEnabled] = useState<boolean>(() =>
    localStorage.getItem('appAnimations') !== 'false'
  )
  const [favorites, setFavorites] = useState<string[]>(() => {
    try { const saved = JSON.parse(localStorage.getItem('appFavorites_v2') || '[]'); return Array.isArray(saved) ? saved.filter((v: unknown) => typeof v === 'string') : [] }
    catch { return [] }
  })

  useEffect(() => {
    localStorage.setItem('appAnimations', String(animationsEnabled))
  }, [animationsEnabled])

  useEffect(() => {
    localStorage.setItem('appFavorites_v2', JSON.stringify(favorites))
  }, [favorites])

  const applyTheme = (theme: typeof themes[0]) => {
    document.documentElement.style.setProperty('--app-primary', theme.primary)
    document.documentElement.style.setProperty('--app-bg-hex', theme.bg)
    localStorage.setItem('appTheme', theme.name)
  }

  useEffect(() => {
    const savedTheme = localStorage.getItem('appTheme') || 'Purple'
    const theme = themes.find(t => t.name === savedTheme)
    if (theme) applyTheme(theme)
    const toggleCmd = () => setIsCmdPaletteOpen(p => !p)
    window.addEventListener('toggle-cmd-palette', toggleCmd)
    return () => window.removeEventListener('toggle-cmd-palette', toggleCmd)
  }, [])

  const checkStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/status`)
      const data = await readResponse(res)
      setStatus({ connected: data.success, message: data.message })
    } catch {
      setStatus({ connected: false, message: 'Server unreachable' })
    }
  }

  const checkStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`)
      const data = await readResponse(res)
      if (data.success) {
        setStats({ name: data.name, fps: data.fps, clips: data.clips, timecode: data.timecode })
      } else {
        setStats({ name: '', fps: '', clips: 0, timecode: '' })
      }
    } catch {
      setStats({ name: '', fps: '', clips: 0, timecode: '' })
    }
  }

  const fetchContext = async () => {
    try {
      const res = await fetch(`${API_BASE}/context`)
      const data = await readResponse(res)
      if (data.success) {
        setContext({ project: data.project, timelines: data.timelines, current_timeline: data.current_timeline })
      } else {
        setContext({ project: '', timelines: [], current_timeline: '' })
      }
    } catch { setContext({ project: '', timelines: [], current_timeline: '' }) }
  }

  const fetchTemplates = async () => {
    try {
      const res = await fetch(`${API_BASE}/assets`)
      const data = await readResponse(res)
      if (data.success) setTemplates(data.templates)
    } catch { /* ignore */ }
  }

  useEffect(() => {
    const poll = async () => {
      if (pollInFlight.current) return
      pollInFlight.current = true
      try { await Promise.all([checkStatus(), checkStats(), fetchContext()]) }
      finally { pollInFlight.current = false }
    }
    void poll()
    void fetchTemplates()
    const timer = setInterval(poll, 8000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    setSelectedMergeTimelines(prev => prev.filter(t => context.timelines.includes(t)))
    setSelectedBatchTimelines(prev => prev.filter(t => context.timelines.includes(t)))
  }, [context.timelines])
  useEffect(() => {
    setBwScan(null)
    setProjectStats(null)
  }, [context.project, context.current_timeline])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'SELECT' || document.activeElement?.tagName === 'TEXTAREA' || (document.activeElement as HTMLElement)?.isContentEditable) return
      if ((e.metaKey || e.ctrlKey) && !e.shiftKey && e.key.toLowerCase() === 's') {
        e.preventDefault()
        runTask('snapshot', {}, 'snapshot')
      }
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && !e.shiftKey && e.key.toLowerCase() === 's') {
        e.preventDefault()
        setLoading(prev => ({ ...prev, bw_scan: true }))
        fetch(`${API_BASE}/badwords/scan`)
          .then(readResponse)
          .then(data => {
            setBwScan(data)
            if (data.success) addLog(`Found ${data.total_markers} markers on '${data.timeline_name}'`, 'success')
            else addLog(data.message, 'error')
          })
          .catch(() => addLog('Failed to scan markers', 'error'))
          .finally(() => setLoading(prev => ({ ...prev, bw_scan: false })))
      }
      if ((e.metaKey || e.ctrlKey) && ['1', '2', '3', '4', '5', '6'].includes(e.key)) {
        e.preventDefault()
        const tabs = ['magic', 'cut', 'process', 'export', 'templates', 'manual']
        setActiveTab(tabs[parseInt(e.key) - 1])
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const toggleFavorite = (id: string) => {
    setFavorites(prev => prev.includes(id) ? prev.filter(f => f !== id) : [...prev, id])
  }

  const addLog = (msg: string, type: 'info' | 'success' | 'error') => {
    const id = Date.now() + Math.random()
    setLogs(prev => [{ id: String(id), msg, type, time: new Date().toLocaleTimeString() }, ...prev].slice(0, 10))
    setToasts(prev => [...prev, { id, msg, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000)
  }

  const handleConnect = async () => {
    addLog('Connecting to DaVinci Resolve...', 'info')
    try {
      const res = await fetch(`${API_BASE}/connect`, { method: 'POST' })
      const data = await readResponse(res)
      setStatus({ connected: data.success, message: data.message })
      addLog(data.message, data.success ? 'success' : 'error')
      if (data.success) { checkStats(); fetchContext(); fetchTemplates() }
    } catch {
      setStatus({ connected: false, message: 'Server unreachable' })
      addLog('Failed to reach Python backend.', 'error')
    }
  }

  const handleSetTimeline = async (timeline_name: string) => {
    addLog(`Switching to timeline: ${timeline_name}`, 'info')
    try {
      const res = await fetch(`${API_BASE}/set_context`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ timeline_name })
      })
      const data = await readResponse(res)
      addLog(data.message, data.success ? 'success' : 'error')
      if (data.success) { checkStats(); fetchContext() }
    } catch {
      addLog('Failed to switch timeline', 'error')
    }
  }

  const runTask = async (endpoint: string, payload: Record<string, unknown> = {}, buttonId: string) => {
    setLoading(prev => ({ ...prev, [buttonId]: true }))
    try {
      if (endpoint === 'import_template') {
        const data = await api(endpoint, payload)
        addLog(data.message, 'success')
        return true
      }
      const data = await api<Review>('jobs/preview', { operation: endpoint, payload })
      setReview(data)
    } catch (error) {
      addLog(error instanceof Error ? error.message : 'Could not prepare the operation', 'error')
      return false
    } finally {
      setLoading(prev => ({ ...prev, [buttonId]: false }))
    }
  }

  const submitReview = async () => {
    if (!review?.ready || submitting) return
    setSubmitting(true)
    try {
      const data = await api('jobs', { preview_token: review.preview_token })
      setJobs(previous => [data.job, ...previous.filter(job => job.id !== data.job.id)])
      if (seenJobs.current) seenJobs.current[data.job.id] = 'queued'
      setReview(null)
      addLog('Job queued. Follow progress in Jobs.', 'info')
    } catch (error) {
      addLog(error instanceof Error ? error.message : 'Could not queue the job', 'error')
    } finally { setSubmitting(false) }
  }

  useEffect(() => {
    const poll = async () => {
      if (jobsPolling.current) return
      jobsPolling.current = true
      try {
        const data = await api<{ jobs: Job[] }>('jobs')
        setJobs(data.jobs)
        if (seenJobs.current) {
          for (const job of data.jobs) {
            const previous = seenJobs.current[job.id]
            if (previous && previous !== job.status && ['succeeded', 'failed', 'cancelled', 'interrupted'].includes(job.status)) {
              if (job.operation === 'youtube_chapters' && job.status === 'succeeded') {
                setChapterOutput(job.message)
                addLog('Chapters are ready in Export and Jobs.', 'success')
              } else addLog(job.message, job.status === 'succeeded' ? 'success' : job.status === 'cancelled' ? 'info' : 'error')
              if (job.operation === 'folder_generate' && job.status === 'succeeded' && job.result?.target) {
                localStorage.setItem('clipAssassin:masterFolderInput', job.result.target)
                window.dispatchEvent(new CustomEvent('folder-generated', { detail: job.result.target }))
              }
              void checkStats(); void fetchContext()
            }
          }
        }
        seenJobs.current = Object.fromEntries(data.jobs.map(job => [job.id, job.status]))
      } catch { /* The connection indicator reports backend availability. */ }
      finally { jobsPolling.current = false }
    }
    void poll()
    const timer = setInterval(poll, 1500)
    return () => clearInterval(timer)
  }, [])

  const isDashboard = activeTab === 'dashboard'
  const sharedProps = { isDashboard, favorites, toggleFavorite, loading, context, runTask, addLog }

  return (
    <div data-motion={animationsEnabled?'on':'off'} className="app-shell flex h-screen bg-brand-bg font-sans overflow-hidden text-slate-200">
      {animationsEnabled && (
        <div className="glow-bg">
          <div className="glow-orb-1" />
          <div className="glow-orb-2" />
        </div>
      )}

      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} activeJobs={jobs.filter(job=>['queued','running','cancelling'].includes(job.status)).length} />

      <div className="app-main flex-1 flex flex-col relative h-screen overflow-y-auto overflow-x-hidden scroll-smooth">
        <Header
          status={status}
          handleConnect={handleConnect}
          context={context}
          handleSetTimeline={handleSetTimeline}
          stats={stats}
          activeTab={activeTab}
        />

        <div className="mobile-navigation md:hidden flex flex-wrap gap-2 px-4 pb-4">
          {['dashboard', 'master_ingest', 'cut', 'magic', 'process', 'export', 'templates', 'connections', 'jobs', 'settings', 'manual'].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} className={`text-xs px-3 py-2 rounded-lg ${activeTab === tab ? 'bg-brand-primary text-white' : 'bg-white/5'}`}>{({dashboard:'Dashboard',master_ingest:'Master Ingest',cut:'Cut & Trim',magic:'Magic Tools',process:'Process',export:'Export',templates:'Templates',connections:'Connections',jobs:'Jobs',settings:'Settings',manual:'Manual'} as Record<string,string>)[tab]}</button>
          ))}
        </div>
        <div className="app-content flex-1 w-full max-w-[1440px] mx-auto px-5 md:px-8 lg:px-10 pb-28 pt-4">
          <ToolWorkspace key={activeTab} enabled={['master_ingest', 'magic', 'cut', 'process', 'export'].includes(activeTab)} title={({master_ingest:'Master Ingest',magic:'Magic Tools',cut:'Cut & Trim',process:'Process',export:'Export'} as Record<string,string>)[activeTab]||''}>
          {isDashboard && (
            <DashboardPage
              API_BASE={API_BASE}
              favorites={favorites}
              setFavorites={setFavorites}
              loading={loading}
              setLoading={setLoading}
              projectStats={projectStats}
              setProjectStats={setProjectStats}
              addLog={addLog}
            />
          )}

          {(activeTab === 'master_ingest' || isDashboard) && (
            <MasterIngestPage
              {...sharedProps}
            />
          )}

          {(activeTab === 'magic' || isDashboard) && (
            <MagicToolsPage
              {...sharedProps}
              API_BASE={API_BASE}
              setLoading={setLoading}
              bwScan={bwScan}
              setBwScan={setBwScan}
              bwColors={bwColors}
              setBwColors={setBwColors}
            />
          )}

          {(activeTab === 'cut' || isDashboard) && (
            <CutToolsPage {...sharedProps} />
          )}

          {(activeTab === 'process' || isDashboard) && (
            <ProcessPage
              {...sharedProps}
              selectedMergeTimelines={selectedMergeTimelines}
              setSelectedMergeTimelines={setSelectedMergeTimelines}
            />
          )}

          {(activeTab === 'export' || isDashboard) && (
            <ExportPage
              {...sharedProps}
              API_BASE={API_BASE}
              selectedBatchTimelines={selectedBatchTimelines}
              setSelectedBatchTimelines={setSelectedBatchTimelines}
              shotlistFormat={shotlistFormat}
              setShotlistFormat={setShotlistFormat}
            />
          )}

          {activeTab === 'templates' && (
            <TemplatesPage
              templates={templates}
              fetchTemplates={fetchTemplates}
              loading={loading}
              setLoading={setLoading}
              runTask={runTask}
              addLog={addLog}
            />
          )}

          {activeTab === 'settings' && (
            <SettingsPage
              animationsEnabled={animationsEnabled}
              setAnimationsEnabled={setAnimationsEnabled}
              setFavorites={setFavorites}
              setLogs={setLogs}
              applyTheme={applyTheme}
              addLog={addLog}
            />
          )}

          {activeTab === 'jobs' && <JobsPage jobs={jobs} onReview={setReview} addLog={addLog} activity={logs} clearActivity={()=>setLogs([])} />}
          {activeTab === 'connections' && <ConnectionsPage runTask={runTask} addLog={addLog} />}
          {activeTab === 'manual' && <ManualPage />}
          {chapterOutput && (activeTab === 'export' || isDashboard) && <div className="mt-6 rounded-xl border border-white/10 bg-black/30 p-5">
            <div className="flex justify-between"><h3>YouTube Chapters</h3><button onClick={() => setChapterOutput('')}>Close</button></div>
            <textarea aria-label="Generated YouTube chapters" readOnly value={chapterOutput} rows={8} className="mt-3 w-full bg-black/30 p-3 text-sm font-mono" />
          </div>}

          </ToolWorkspace>
        </div>
      </div>
      <ReviewDialog review={review} busy={submitting} onClose={() => setReview(null)} onSubmit={submitReview} />
      {jobs.some(job => ['running', 'queued', 'cancelling'].includes(job.status)) && <button className="job-indicator" onClick={() => setActiveTab('jobs')}><span className="w-2 h-2 bg-brand-primary rounded-full animate-pulse" />{jobs.filter(job => ['running', 'queued', 'cancelling'].includes(job.status)).length} active jobs · View progress</button>}

      <div className="absolute top-24 right-8 z-[100] flex flex-col gap-3 pointer-events-none">
        {toasts.map(t => (
          <div key={t.id} className={`animate-in slide-in-from-right-8 fade-in duration-300 pointer-events-auto flex items-center gap-3 px-5 py-3 rounded-2xl shadow-2xl border backdrop-blur-xl ${
            t.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : t.type === 'info' ? 'bg-sky-500/10 border-sky-500/20 text-sky-400' : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
          }`}>
            <div className={`w-2 h-2 rounded-full ${t.type === 'success' ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.8)]' : 'bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.8)]'}`} />
            <span className="text-sm font-medium">{t.msg}</span>
          </div>
        ))}
      </div>

      <CommandPalette
        isOpen={isCmdPaletteOpen}
        onClose={() => setIsCmdPaletteOpen(false)}
        actions={[
          { id: 'snapshot', title: 'Timeline Snapshot', icon: <Camera size={16} />, keywords: ['backup', 'save'], perform: () => runTask('snapshot', {}, 'snapshot') },
          { id: 'magic_bin_organizer', title: 'Magic Bin Organizer', icon: <FolderTree size={16} />, keywords: ['organize', 'folder'], perform: () => runTask('organize_bins', {}, 'magic_bins') },
          { id: 'silence_remover', title: 'Silence Remover', icon: <VolumeX size={16} />, keywords: ['cut', 'dead space'], perform: () => setActiveTab('process') },
          { id: 'batch_clip_renamer', title: 'Batch Clip Renamer', icon: <PenLine size={16} />, perform: () => setActiveTab('magic') },
          { id: 'social_media_reframe', title: 'Social Media Reframe', icon: <Smartphone size={16} />, perform: () => runTask('social_reframe', { format: '9:16' }, 'magic_reframe_916') },
          { id: 'adjustment_layer', title: 'Quick Adjustment Layer', icon: <Combine size={16} />, keywords: ['fx', 'color', 'grade'], perform: () => runTask('add_adjustment_layer', {}, 'magic_adj') },
          { id: 'timecode_cutter', title: 'Timecode Cutter', icon: <Scissors size={16} />, perform: () => setActiveTab('cut') },
          { id: 'markers_to_timeline', title: 'Markers to Timeline', icon: <MapPin size={16} />, perform: () => setActiveTab('cut') },
          { id: 'batch_timeline_render', title: 'Batch Timeline Render', icon: <MonitorUp size={16} />, perform: () => setActiveTab('export') },
          { id: 'auto_youtube_chapters', title: 'Auto YouTube Chapters', icon: <Video size={16} />, perform: () => runTask('youtube_chapters', {}, 'chapters') },
          { id: 'shotlist_generator', title: 'Client Shotlist / Document Exporter', icon: <Target size={16} />, keywords: ['csv', 'excel', 'doc', 'word'], perform: () => setActiveTab('export') },
        ]}
      />


    </div>
  )
}
