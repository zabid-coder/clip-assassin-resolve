import { Combine, Droplet, AudioLines, VolumeX } from 'lucide-react'
import { ActionButton, FeatureCard, InputField, SelectField } from '../components/ui'
import type { AppContext } from '../types/api'

interface Props {
  isDashboard: boolean
  favorites: string[]
  toggleFavorite: (id: string) => void
  loading: Record<string, boolean>
  context: AppContext
  selectedMergeTimelines: string[]
  setSelectedMergeTimelines: React.Dispatch<React.SetStateAction<string[]>>
  runTask: (endpoint: string, payload: any, buttonId: string) => void
  addLog: (msg: string, type: 'info' | 'success' | 'error') => void
}

export function ProcessPage({ isDashboard, favorites, toggleFavorite, loading, context, selectedMergeTimelines, setSelectedMergeTimelines, runTask, addLog }: Props) {
  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 grid grid-cols-1 md:grid-cols-2 gap-5 items-start">
      <FeatureCard hidden={isDashboard && !favorites.includes('merge_timelines')}
        id="merge_timelines"
        isFavorite={favorites.includes('merge_timelines')}
        onToggleFavorite={() => toggleFavorite('merge_timelines')}
        description="Appends the timelines you select into one master timeline, in order."
        warning="Creates a new timeline and preserves the source. Review the result before exporting."
        className="md:col-span-2 ring-1 ring-brand-primary/30 shadow-xl shadow-brand-primary/20"
        title="Merge Timelines"
        icon={<Combine size={18} />}
        category="destructive"
        helpText="Click to select multiple timelines. They will be copied into a single Master Timeline."
      >
        <div className="flex flex-col gap-4">
          <div className="selection-heading">
            <span>Select Timelines to Merge:</span>
            {context.timelines.length > 0 && (
              <div className="flex gap-3">
                <button onClick={() => setSelectedMergeTimelines([...context.timelines])} className="text-xs text-brand-secondary hover:text-white transition-colors">Select All</button>
                <button onClick={() => setSelectedMergeTimelines([])} className="text-xs text-brand-secondary hover:text-white transition-colors">Clear All</button>
              </div>
            )}
          </div>
          {context.timelines.length > 0 ? (
            <div className="flex flex-col gap-1.5 max-h-48 overflow-y-auto pr-2 custom-scrollbar border border-white/5 rounded-lg p-2 bg-black/20">
              {context.timelines.map(t => (
                <button
                  key={t}
                  onClick={() => setSelectedMergeTimelines(prev => prev.includes(t) ? prev.filter(x => x !== t) : [...prev, t])}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium transition-all text-left w-full ${selectedMergeTimelines.includes(t) ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.1)]' : 'bg-transparent text-white/60 hover:bg-white/5 border border-transparent'}`}
                >
                  <div className={`w-3.5 h-3.5 rounded-sm border flex items-center justify-center transition-colors ${selectedMergeTimelines.includes(t) ? 'bg-amber-500 border-amber-500 text-black' : 'border-white/30'}`}>
                    {selectedMergeTimelines.includes(t) && <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                  </div>
                  <span className="truncate">{t}</span>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-sm text-white/30 italic p-3 bg-black/20 rounded-xl border border-white/5">No timelines found. Connect to a project first.</div>
          )}
          <div className="flex justify-end mt-2">
            <div className="tool-action-slot">
              <ActionButton
                text={selectedMergeTimelines.length > 0 ? `Merge ${selectedMergeTimelines.length} Timelines` : 'Merge Timelines'}
                category="destructive" variant="primary"
                isLoading={loading['merge']}
                onClick={() => {
                  if (selectedMergeTimelines.length < 1) {
                    addLog('Please select at least one timeline to merge', 'error')
                    return
                  }
                  return runTask('merge_timelines', { timeline_names: selectedMergeTimelines.join(',') }, 'merge')
                }}
              />
            </div>
          </div>
        </div>
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('watermark_track')}
        id="watermark_track"
        isFavorite={favorites.includes('watermark_track')}
        onToggleFavorite={() => toggleFavorite('watermark_track')}
        description="Places your logo across the top track of the whole video."
        className="md:col-span-2 ring-1 ring-brand-primary/30 shadow-xl shadow-brand-primary/20"
        title="Watermark Track"
        icon={<Droplet size={18} />}
        category="output"
        helpText="Provide the path to an image to place it on a top video track."
      >
        <div className="tool-settings-layout">
          <div className="flex-1">
            <InputField id="watermarkPath" browseType="file" placeholder="/Users/name/Desktop/logo.png" />
          </div>
          <div className="tool-action-slot">
            <ActionButton
              text="Apply Watermark"
              category="output" variant="primary"
              isLoading={loading['watermark']}
              disabled={!context.current_timeline}
              title={!context.current_timeline ? 'Requires an active timeline' : undefined}
              onClick={() => runTask('apply_watermark', { image_path: (document.getElementById('watermarkPath') as HTMLInputElement).value }, 'watermark')}
            />
          </div>
        </div>
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('auto_jcut__lcut')}
        id="auto_jcut__lcut"
        isFavorite={favorites.includes('auto_jcut__lcut')}
        onToggleFavorite={() => toggleFavorite('auto_jcut__lcut')}
        description="Creates an edited copy with overlapping audio on alternating tracks."
        warning="Creates a new timeline and preserves the source. Review the result before exporting."
        className="md:col-span-2 ring-1 ring-brand-primary/30 shadow-xl shadow-brand-primary/20"
        title="Auto J-Cut / L-Cut"
        icon={<AudioLines size={18} />}
        category="destructive"
        helpText="Requires aligned V1/A1 clips and available source handles. Clip FX and automation need manual review in the copy. J-Cut starts next audio early; L-Cut extends current audio."
      >
        <div className="tool-settings-layout">
          <div className="responsive-fields">
            <div className="min-w-0">
              <SelectField id="jlType" options={['J-Cut (Audio First)', 'L-Cut (Audio Extends)']} />
            </div>
            <div className="min-w-0">
              <InputField id="jlOverlap" placeholder="Overlap frames (default: 10)" />
            </div>
          </div>
          <div className="tool-action-slot">
            <ActionButton
              text="Apply Cuts"
              isLoading={loading['jlcut']}
              disabled={!context.current_timeline}
              title={!context.current_timeline ? 'Requires an active timeline' : undefined}
              category="destructive" variant="primary"
              onClick={() => {
                const typeVal = (document.getElementById('jlType') as HTMLSelectElement).value
                const cutType = typeVal.startsWith('J') ? 'j' : 'l'
                const overlap = parseInt((document.getElementById('jlOverlap') as HTMLInputElement).value) || 10
                return runTask('jl_cut', { cut_type: cutType, overlap_frames: overlap }, 'jlcut')
              }}
            />
          </div>
        </div>
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('silence_remover')}
        id="silence_remover"
        isFavorite={favorites.includes('silence_remover')}
        onToggleFavorite={() => toggleFavorite('silence_remover')}
        description="Analyzes timeline audio and creates a new timeline without silence."
        warning="Creates a new timeline and preserves the source. Review the result before exporting."
        className="md:col-span-2 ring-1 ring-brand-primary/30 shadow-xl shadow-brand-primary/20"
        title="Silence Remover"
        icon={<VolumeX size={18} />}
        category="destructive"
        helpText="Detects silent sections in the audio and creates a new timeline without them. Perfect for jump-cut style content. Requires pydub + ffmpeg."
      >
        <div className="tool-settings-layout">
          <div className="responsive-fields">
            <InputField id="silenceDb" placeholder="Threshold dB (-40)" />
            <InputField id="silenceMin" placeholder="Min silence ms (500)" />
            <InputField id="silencePad" placeholder="Padding ms (100)" />
          </div>
          <div className="tool-action-slot">
            <ActionButton
              text="Remove Silence"
              isLoading={loading['silence']}
              disabled={!context.current_timeline}
              title={!context.current_timeline ? 'Requires an active timeline' : undefined}
              category="destructive" variant="primary"
              onClick={() => {
                const db = parseInt((document.getElementById('silenceDb') as HTMLInputElement).value) || -40
                const minMs = parseInt((document.getElementById('silenceMin') as HTMLInputElement).value) || 500
                const padMs = parseInt((document.getElementById('silencePad') as HTMLInputElement).value || '100')
                return runTask('silence_remove', { threshold_db: db, min_silence_ms: minMs, padding_ms: padMs }, 'silence')
              }}
            />
          </div>
        </div>
      </FeatureCard>
    </div>
  )
}
