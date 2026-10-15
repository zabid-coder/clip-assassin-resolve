import { Camera, FolderTree, PenLine, Smartphone, Type, Combine, Link, Wand2 } from 'lucide-react'
import { ActionButton, FeatureCard, InputField } from '../components/ui'
import type { AppContext, BadWordsScanResponse } from '../types/api'

interface Props {
  API_BASE: string
  isDashboard: boolean
  favorites: string[]
  toggleFavorite: (id: string) => void
  loading: Record<string, boolean>
  setLoading: React.Dispatch<React.SetStateAction<Record<string, boolean>>>
  context: AppContext
  bwScan: BadWordsScanResponse | null
  setBwScan: (v: BadWordsScanResponse) => void
  bwColors: Record<string, boolean>
  setBwColors: React.Dispatch<React.SetStateAction<Record<string, boolean>>>
  runTask: (endpoint: string, payload: any, buttonId: string) => void
  addLog: (msg: string, type: 'info' | 'success' | 'error') => void
}

export function MagicToolsPage({ API_BASE, isDashboard, favorites, toggleFavorite, loading, setLoading, context, bwScan, setBwScan, bwColors, setBwColors, runTask, addLog }: Props) {
  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 grid grid-cols-1 md:grid-cols-2 gap-5 items-start">
      <FeatureCard hidden={isDashboard && !favorites.includes('snapshot')}
        id="snapshot"
        isFavorite={favorites.includes('snapshot')}
        onToggleFavorite={() => toggleFavorite('snapshot')}
        description="Saves a full backup of your current timeline before you run destructive tools."
        className="md:col-span-2 ring-1 ring-brand-primary/30 shadow-xl shadow-brand-primary/20"
        title="Timeline Snapshot"
        icon={<Camera size={18} />}
        category="magic"
        helpText="Creates a backup copy of the active timeline. Keep this copy before editing; switch back to it when you need the original sequence."
      >
        <div className="tool-action-slot">
          <ActionButton
            text="Save Snapshot"
            category="magic" variant="primary"
            isLoading={loading['snapshot']}
            disabled={!context.current_timeline}
            title={!context.current_timeline ? 'Requires an active timeline' : undefined}
            onClick={() => runTask('snapshot', {}, 'snapshot')}
          />
        </div>
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('magic_bin_organizer')}
        id="magic_bin_organizer"
        isFavorite={favorites.includes('magic_bin_organizer')}
        onToggleFavorite={() => toggleFavorite('magic_bin_organizer')}
        description="Sorts your Media Pool into video, audio, and image bins automatically."
        className="md:col-span-2 ring-1 ring-brand-primary/30 shadow-xl shadow-brand-primary/20"
        title="Magic Bin Organizer"
        icon={<FolderTree size={18} />}
        category="organize"
        helpText="Scans the root Media Pool and automatically moves loose Video, Audio, and Image files into standard organized Bins."
      >
        <div className="tool-action-slot">
          <ActionButton
            text="Organize Media Pool"
            category="organize" variant="primary"
            isLoading={loading['magic_bins']}
            onClick={() => runTask('organize_bins', {}, 'magic_bins')}
          />
        </div>
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('batch_clip_renamer')}
        id="batch_clip_renamer"
        isFavorite={favorites.includes('batch_clip_renamer')}
        onToggleFavorite={() => toggleFavorite('batch_clip_renamer')}
        description="Renames timeline clip instances on Video Track 1 using your prefix."
        warning="This modifies your timeline directly. Use Timeline Snapshot first if unsure."
        title="Batch Clip Renamer"
        icon={<PenLine size={18} />}
        category="destructive"
        helpText="Rename all clips on Video Track 1 with a sequential pattern. Enter a prefix like 'Interview' and clips become Interview_001, Interview_002, etc."
      >
        <InputField id="renamePrefix" placeholder="Name prefix (e.g. Interview)" />
        <div className="mt-4">
          <ActionButton
            text="Rename All Clips"
            isLoading={loading['rename']}
            category="destructive" variant="primary"
            onClick={() => runTask('batch_rename', {
              prefix: (document.getElementById('renamePrefix') as HTMLInputElement).value,
              start_number: 1,
              scope: 'timeline'
            }, 'rename')}
          />
        </div>
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('social_media_reframe')}
        id="social_media_reframe"
        isFavorite={favorites.includes('social_media_reframe')}
        onToggleFavorite={() => toggleFavorite('social_media_reframe')}
        description="Reframes your timeline to 9:16 for Shorts or 1:1 for Square."
        title="Social Media Reframe"
        icon={<Smartphone size={18} />}
        category="output"
        helpText="Duplicates your current timeline and automatically sets the resolution to 9:16 or 1:1 with scale-to-crop settings."
      >
        <div className="flex flex-col gap-3">
          <ActionButton
            text="Convert to 9:16 (Shorts/Reels)"
            category="output" variant="primary"
            isLoading={loading['magic_reframe_916']}
            onClick={() => runTask('social_reframe', { format: '9:16' }, 'magic_reframe_916')}
          />
          <ActionButton
            text="Convert to 1:1 (Square)"
            category="output" variant="secondary"
            isLoading={loading['magic_reframe_11']}
            onClick={() => runTask('social_reframe', { format: '1:1' }, 'magic_reframe_11')}
          />
        </div>
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('quick_title')}
        id="quick_title"
        isFavorite={favorites.includes('quick_title')}
        onToggleFavorite={() => toggleFavorite('quick_title')}
        description="Drops a title card at the playhead."
        title="Quick Title"
        icon={<Type size={18} />}
        category="magic"
        helpText="Instantly adds a standard Text+ title at your current playhead position."
      >
        <ActionButton
          text="Add Title at Playhead"
          category="magic" variant="primary"
          isLoading={loading['magic_title']}
          onClick={() => runTask('add_title', {}, 'magic_title')}
        />
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('adjustment_layer')}
        id="adjustment_layer"
        isFavorite={favorites.includes('adjustment_layer')}
        onToggleFavorite={() => toggleFavorite('adjustment_layer')}
        description="Drops an Adjustment Clip on Track 5 at playhead."
        title="Quick Adjustment Layer"
        icon={<Combine size={18} />}
        category="magic"
        helpText="Instantly adds an Adjustment Layer to Video Track 5 at your current playhead position without shifting clips. Requires an 'Adjustment Clip' in your Media Pool."
      >
        <ActionButton
          text="Add Adjustment Layer"
          category="magic" variant="primary"
          isLoading={loading['magic_adj']}
          disabled={!context.current_timeline}
          title={!context.current_timeline ? 'Requires an active timeline' : undefined}
          onClick={() => runTask('add_adjustment_layer', {}, 'magic_adj')}
        />
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('multicam_auto_sync')}
        id="multicam_auto_sync"
        isFavorite={favorites.includes('multicam_auto_sync')}
        onToggleFavorite={() => toggleFavorite('multicam_auto_sync')}
        description="Syncs the clips you've selected using their audio waveforms."
        title="Multi-Cam Auto Sync"
        icon={<Link size={18} />}
        category="organize"
        helpText="Select at least one video and one audio clip in the Media Pool, then click this to auto-sync them by waveform."
      >
        <ActionButton
          text="Sync Selected Clips"
          category="organize" variant="primary"
          isLoading={loading['magic_sync']}
          onClick={() => runTask('auto_sync', {}, 'magic_sync')}
        />
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('badwords')}
        id="badwords"
        isFavorite={favorites.includes('badwords')}
        onToggleFavorite={() => toggleFavorite('badwords')}
        description="Scans your timeline markers for flagged words and lists them for review."
        warning="Creates a new timeline and preserves the source."
        className="md:col-span-2 ring-1 ring-brand-primary/30 shadow-xl shadow-brand-primary/20"
        title="BadWords Cleaner"
        icon={<Wand2 size={18} />}
        category="destructive"
        helpText="Scans BadWords-generated color markers from the current timeline. Select which marker colors to remove, then create a clean timeline without those segments."
      >
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <div className="tool-action-slot">
              <ActionButton
                text="Scan Markers"
                category="destructive" variant="secondary"
                isLoading={loading['bw_scan']}
                onClick={async () => {
                  setLoading(prev => ({ ...prev, bw_scan: true }))
                  try {
                    const res = await fetch(`${API_BASE}/badwords/scan`)
                    const data = await res.json()
                    setBwScan(data)
                    if (data.success) {
                      addLog(`Found ${data.total_markers} markers on '${data.timeline_name}'`, 'success')
                    } else {
                      addLog(data.message, 'error')
                    }
                  } catch { addLog('Failed to scan markers', 'error') }
                  finally { setLoading(prev => ({ ...prev, bw_scan: false })) }
                }}
              />
            </div>
            {bwScan?.success && (
              <p className="text-xs text-white/50">
                Found <strong className="text-white/80">{bwScan.total_markers}</strong> markers ·
                <strong className="text-white/80"> {bwScan.total_marked_seconds}s</strong> marked
              </p>
            )}
          </div>

          {bwScan?.success && (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {Object.entries(bwScan.summary).map(([color, data]) => {
                  const colorMap: Record<string, string> = {
                    Red: 'bg-red-500/20 border-red-500/40 text-red-300',
                    Blue: 'bg-blue-500/20 border-blue-500/40 text-blue-300',
                    Green: 'bg-green-500/20 border-green-500/40 text-green-300',
                    Yellow: 'bg-yellow-500/20 border-yellow-500/40 text-yellow-300',
                    Purple: 'bg-purple-500/20 border-purple-500/40 text-purple-300',
                    Cyan: 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300',
                  }
                  const chipClass = colorMap[color] || 'bg-white/10 border-white/20 text-white/70'
                  return (
                    <span key={color} className={`px-3 py-1.5 rounded-lg border text-xs font-medium ${chipClass}`}>
                      {color}: {data.count} ({data.total_seconds}s)
                    </span>
                  )
                })}
              </div>

              <div className="flex flex-wrap gap-4 px-1">
                {['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Cyan'].filter(c => bwScan.summary[c]).map(color => (
                  <label key={color} className="flex items-center gap-2 cursor-pointer text-white/70 hover:text-white transition-colors text-xs">
                    <input
                      type="checkbox"
                      checked={bwColors[color] || false}
                      onChange={(e) => setBwColors(prev => ({ ...prev, [color]: e.target.checked }))}
                      className="w-3.5 h-3.5 accent-orange-500"
                    />
                    Remove {color}
                  </label>
                ))}
              </div>

              <div className="tool-action-slot">
                <ActionButton
                  text="Clean Timeline"
                  category="destructive" variant="primary"
                  isLoading={loading['bw_clean']}
                  onClick={() => {
                    const selectedColors = Object.entries(bwColors)
                      .filter(([_, checked]) => checked)
                      .map(([color]) => color)
                    if (selectedColors.length === 0) {
                      addLog('No colors selected for removal', 'error')
                      return
                    }
                    return runTask('badwords/clean', { colors: selectedColors }, 'bw_clean')
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </FeatureCard>
    </div>
  )
}
