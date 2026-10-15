import { useEffect, useState } from 'react'
import { MonitorUp, Image as ImageIcon, Video, FileSpreadsheet } from 'lucide-react'
import { ActionButton, FeatureCard, InputField, SelectField } from '../components/ui'
import type { AppContext } from '../types/api'

interface Props {
  API_BASE: string
  isDashboard: boolean
  favorites: string[]
  toggleFavorite: (id: string) => void
  loading: Record<string, boolean>
  context: AppContext
  selectedBatchTimelines: string[]
  setSelectedBatchTimelines: React.Dispatch<React.SetStateAction<string[]>>
  shotlistFormat: string
  setShotlistFormat: (v: string) => void
  runTask: (endpoint: string, payload: any, buttonId: string) => void
}

export function ExportPage({ API_BASE, isDashboard, favorites, toggleFavorite, loading, context, selectedBatchTimelines, setSelectedBatchTimelines, shotlistFormat, setShotlistFormat, runTask }: Props) {
  const [renderPresets, setRenderPresets] = useState<string[]>([])
  const [renderPreset, setRenderPreset] = useState('')
  useEffect(() => {
    fetch(`${API_BASE}/render_presets`).then(res => res.json()).then(data => {
      setRenderPresets(data.presets || [])
      setRenderPreset(prev => (data.presets || []).includes(prev) ? prev : (data.presets || []).includes('H.264 Master') ? 'H.264 Master' : data.presets?.[0] || '')
    }).catch(() => setRenderPresets([]))
  }, [context.project, API_BASE])
  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 grid grid-cols-1 md:grid-cols-2 gap-5 items-start">
      <FeatureCard hidden={isDashboard && !favorites.includes('multiplatform_render')}
        id="multiplatform_render"
        isFavorite={favorites.includes('multiplatform_render')}
        onToggleFavorite={() => toggleFavorite('multiplatform_render')}
        description="Batch render multiple timelines with your chosen preset."
        className="md:col-span-2 ring-1 ring-brand-primary/30 shadow-xl shadow-brand-primary/20"
        title="Batch Timeline Render"
        icon={<MonitorUp size={18} />}
        category="render"
        helpText="Adds render jobs to the Render Queue for selected timelines using a Resolve Preset."
      >
        <div className="flex flex-col gap-4 mb-4">
          <div className="selection-heading">
            <span>Select Timelines to Render:</span>
            {context.timelines.length > 0 && (
              <div className="flex gap-3">
                <button onClick={() => setSelectedBatchTimelines([...context.timelines])} className="text-xs text-brand-secondary hover:text-white transition-colors">Select All</button>
                <button onClick={() => setSelectedBatchTimelines([])} className="text-xs text-brand-secondary hover:text-white transition-colors">Clear All</button>
              </div>
            )}
          </div>
          {context.timelines.length > 0 ? (
            <div className="flex flex-col gap-1.5 max-h-48 overflow-y-auto pr-2 custom-scrollbar border border-white/5 rounded-lg p-2 bg-black/20">
              {context.timelines.map(name => (
                <button
                  key={name}
                  onClick={() => setSelectedBatchTimelines(prev => prev.includes(name) ? prev.filter(t => t !== name) : [...prev, name])}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium transition-all text-left w-full ${selectedBatchTimelines.includes(name) ? 'bg-brand-primary/20 text-brand-primary border border-brand-primary/30' : 'bg-transparent text-white/60 hover:bg-white/5 border border-transparent'}`}
                >
                  <div className={`w-3.5 h-3.5 rounded-sm border flex items-center justify-center transition-colors ${selectedBatchTimelines.includes(name) ? 'bg-brand-primary border-brand-primary text-black' : 'border-white/30'}`}>
                    {selectedBatchTimelines.includes(name) && <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                  </div>
                  <span className="truncate">{name}</span>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-xs text-brand-warning/80 italic bg-brand-warning/10 p-2 rounded border border-brand-warning/20">No timelines found in project.</div>
          )}
        </div>

        <div className="tool-settings-layout">
          <div className="tool-settings-fields space-y-4">
            <div>
              <div className="field-heading">
                <label htmlFor="renderPresetName">Resolve preset</label>
                <button
                  onClick={() => fetch(`${API_BASE}/open_folder?path=presets`)}
                  className="text-brand-secondary hover:text-brand-secondary/80 hover:underline"
                >
                  Locate Bundled XML
                </button>
              </div>
              <select id="renderPresetName" aria-label="Resolve render preset" value={renderPreset} onChange={e => setRenderPreset(e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white/90">
                <option className="bg-slate-900" value="">Use current Resolve settings</option>
                {renderPresets.map(name => <option className="bg-slate-900" key={name}>{name}</option>)}
              </select>
            </div>
            <InputField id="renderDir" browseType="folder" placeholder="Output Directory Path" />
          </div>
          <div className="tool-action-slot">
            <ActionButton
              text="Add to Render Queue"
              category="render" variant="primary"
              isLoading={loading['render']}
              disabled={selectedBatchTimelines.length === 0}
              title={selectedBatchTimelines.length === 0 ? 'Select at least one timeline' : undefined}
              onClick={() => {
                return runTask('batch_render', {
                  timelines: selectedBatchTimelines,
                  preset_name: (document.getElementById('renderPresetName') as HTMLInputElement).value,
                  target_dir: (document.getElementById('renderDir') as HTMLInputElement).value
                }, 'render')
              }}
            />
          </div>
        </div>
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('extract_thumbnails')}
        id="extract_thumbnails"
        isFavorite={favorites.includes('extract_thumbnails')}
        onToggleFavorite={() => toggleFavorite('extract_thumbnails')}
        description="Saves a still frame at every marker (or selection) to your chosen folder."
        title="Extract Thumbnails"
        icon={<ImageIcon size={18} />}
        category="output"
        helpText="'Markers' mode exports a still frame at every timeline marker."
      >
        <SelectField id="thumbMode" options={['Markers', 'Timeline Center']} />
        <div className="mb-4">
          <InputField id="thumbDir" browseType="folder" placeholder="Save directory" />
        </div>
        <ActionButton
          text="Export Still Frames"
          category="output" variant="primary"
          isLoading={loading['thumb']}
          onClick={() => runTask('extract_thumbnails', { mode: (document.getElementById('thumbMode') as HTMLSelectElement).value, target_dir: (document.getElementById('thumbDir') as HTMLInputElement).value }, 'thumb')}
        />
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('auto_youtube_chapters')}
        id="auto_youtube_chapters"
        isFavorite={favorites.includes('auto_youtube_chapters')}
        onToggleFavorite={() => toggleFavorite('auto_youtube_chapters')}
        description="Generates timestamped chapters from your timeline markers."
        className="md:col-span-2 ring-1 ring-brand-primary/30 shadow-xl shadow-brand-primary/20"
        title="Auto YouTube Chapters"
        icon={<Video size={18} />}
        category="render"
        helpText="Generates a YouTube timestamp list from timeline markers."
      >
        <div className="tool-action-slot">
          <ActionButton
            text="Generate Chapters"
            category="render" variant="primary"
            isLoading={loading['yt']}
            onClick={() => runTask('youtube_chapters', {}, 'yt')}
          />
        </div>
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('shotlist_generator')}
        id="shotlist_generator"
        isFavorite={favorites.includes('shotlist_generator')}
        onToggleFavorite={() => toggleFavorite('shotlist_generator')}
        description="Exports your clip list as a CSV for client review."
        className="md:col-span-2 ring-1 ring-brand-primary/30 shadow-xl shadow-brand-primary/20"
        title="Client Shotlist / Document Exporter"
        icon={<FileSpreadsheet size={18} />}
        category="output"
        helpText="Exports a professional shotlist of Video Track 1. Choose CSV or Word (.docx) template."
      >
        <div className="flex flex-col gap-3">
          <div className="responsive-fields">
            <select
              className="bg-black/40 border border-white/5 rounded-xl px-4 py-3 text-xs text-white/90 focus:outline-none appearance-none cursor-pointer w-full min-w-0"
              aria-label="Shotlist format"
              value={shotlistFormat}
              onChange={(e) => setShotlistFormat(e.target.value)}
            >
              <option value="csv" className="bg-[#111]">CSV Spreadsheet</option>
              <option value="docx" className="bg-[#111]">Word Document (.docx)</option>
            </select>

            <div className="flex-1">
              <InputField id="shotlistPath" browseType="folder" placeholder="Output directory" />
            </div>
          </div>

          {shotlistFormat === 'docx' && (
            <InputField id="shotlistTemplate" browseType="file" placeholder="Word template (.docx)" />
          )}

          <div className="tool-action-slot">
            <ActionButton
              text={`Export ${shotlistFormat === 'docx' ? 'Word Document' : 'CSV'}`}
              category="output" variant="primary"
              isLoading={loading['shotlist']}
              disabled={!context.current_timeline}
              title={!context.current_timeline ? 'Requires an active timeline' : undefined}
              onClick={() => runTask('export_shotlist', {
                format: shotlistFormat,
                target_path: (document.getElementById('shotlistPath') as HTMLInputElement).value,
                template_path: shotlistFormat === 'docx' ? (document.getElementById('shotlistTemplate') as HTMLInputElement).value : ''
              }, 'shotlist')}
            />
          </div>
        </div>
      </FeatureCard>
    </div>
  )
}
