import { Scissors, Target, MapPin, Flag } from 'lucide-react'
import { ActionButton, FeatureCard, InputField, SelectField } from '../components/ui'
import type { AppContext } from '../types/api'

interface Props {
  isDashboard: boolean
  favorites: string[]
  toggleFavorite: (id: string) => void
  loading: Record<string, boolean>
  context: AppContext
  runTask: (endpoint: string, payload: any, buttonId: string) => void
}

export function CutToolsPage({ isDashboard, favorites, toggleFavorite, loading, context, runTask }: Props) {
  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 grid grid-cols-1 md:grid-cols-2 gap-5 items-start">
      <FeatureCard hidden={isDashboard && !favorites.includes('timecode_cutter')}
        id="timecode_cutter"
        isFavorite={favorites.includes('timecode_cutter')}
        onToggleFavorite={() => toggleFavorite('timecode_cutter')}
        description="Creates a new timeline that removes or keeps your exact time ranges."
        warning="The source timeline is preserved. Output contains nested segments including video and audio."
        className="md:col-span-2 ring-1 ring-brand-primary/30 shadow-xl shadow-brand-primary/20"
        title="Timecode Cutter"
        icon={<Scissors size={18} />}
        category="destructive"
        helpText="Enter ranges like 00:01:30-00:02:00 or 1:30-2:00 and the app will create an edited copy with frame-accurate boundaries. Numeric values are seconds."
      >
        <div className="flex flex-col gap-3">
          <textarea
            id="timecodeInput"
            aria-label="Time ranges"
            defaultValue={localStorage.getItem('clipAssassin:timecodeInput') || ''}
            onChange={e => localStorage.setItem('clipAssassin:timecodeInput', e.target.value)}
            rows={3}
            className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-3 text-sm text-white/90 placeholder:text-white/30 focus:outline-none focus:border-brand-primary/50 transition-colors resize-none"
            placeholder="00:01:30-00:02:00&#10;00:05:00-00:06:30"
          />
          <div className="responsive-fields">
            <InputField id="cutClipName" placeholder="Filter by clip name (optional)" />
            <SelectField id="cutMode" options={['Normal (Cut Inside)', 'Reverse (Keep Inside)']} />
          </div>
          <div className="flex justify-end gap-3 mt-2">
            <div className="tool-action-slot">
              <ActionButton
                text="Execute Cut"
                category="destructive" variant="primary"
                isLoading={loading['cut']}
                disabled={!context.current_timeline}
                title={!context.current_timeline ? 'Requires an active timeline' : undefined}
                onClick={() => {
                  const timecodes = (document.getElementById('timecodeInput') as HTMLTextAreaElement).value
                  const clipName = (document.getElementById('cutClipName') as HTMLInputElement).value
                  const mode = (document.getElementById('cutMode') as HTMLSelectElement).value
                  const reverse = mode.startsWith('Reverse')
                  return runTask('cut', { timecodes, reverse, clip_name: clipName }, 'cut')
                }}
              />
            </div>
          </div>
        </div>
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('clip_picker')}
        id="clip_picker"
        isFavorite={favorites.includes('clip_picker')}
        onToggleFavorite={() => toggleFavorite('clip_picker')}
        description="Builds a new timeline from the specific clip numbers you list."
        title="Clip Picker"
        icon={<Target size={18} />}
        category="neutral"
        helpText="List clip names or number ranges (e.g. '1-5, Interview, 10-15') to copy them to a new timeline."
      >
        <InputField id="pickClipInput" placeholder="e.g. 1-5, Interview, 10-15" />
        <div className="mt-4">
          <ActionButton
            text="Pick Clips"
            category="neutral" variant="secondary"
            isLoading={loading['pick']}
            disabled={!context.current_timeline}
            title={!context.current_timeline ? 'Requires an active timeline' : undefined}
            onClick={() => runTask('pick_clips', { names: (document.getElementById('pickClipInput') as HTMLInputElement).value }, 'pick')}
          />
        </div>
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('markers_to_timeline')}
        id="markers_to_timeline"
        isFavorite={favorites.includes('markers_to_timeline')}
        onToggleFavorite={() => toggleFavorite('markers_to_timeline')}
        description="Extracts every clip marked with the selected color into a fresh timeline."
        title="Markers to Timeline"
        icon={<MapPin size={18} />}
        category="neutral"
        helpText="Select a marker color to extract all marked clips into a new timeline."
      >
        <SelectField id="markerColor" options={['All', 'Blue', 'Cyan', 'Green', 'Yellow', 'Red', 'Pink', 'Purple', 'Fuchsia', 'Rose', 'Lavender', 'Sky', 'Mint', 'Lemon', 'Sand', 'Cocoa', 'Cream']} />
        <ActionButton
          text="Extract Marked Clips"
          category="neutral" variant="secondary"
          isLoading={loading['markers']}
          onClick={() => runTask('markers_to_timeline', { color: (document.getElementById('markerColor') as HTMLSelectElement).value }, 'markers')}
        />
      </FeatureCard>

      <FeatureCard hidden={isDashboard && !favorites.includes('flag_filter')}
        id="flag_filter"
        isFavorite={favorites.includes('flag_filter')}
        onToggleFavorite={() => toggleFavorite('flag_filter')}
        description="Pulls only the clips flagged with the color you choose."
        title="Flag Filter"
        icon={<Flag size={18} />}
        category="organize"
        helpText="Select a flag color to copy flagged clips to a new timeline."
      >
        <SelectField id="flagColor" options={['Blue', 'Cyan', 'Green', 'Yellow', 'Red', 'Pink', 'Purple', 'Fuchsia', 'Rose', 'Lavender', 'Sky', 'Mint', 'Lemon', 'Sand', 'Cocoa', 'Cream']} />
        <ActionButton
          text="Extract Flagged Clips"
          category="organize" variant="secondary"
          isLoading={loading['flags']}
          disabled={!context.current_timeline}
          title={!context.current_timeline ? 'Requires an active timeline' : undefined}
          onClick={() => runTask('filter_by_flag', { color: (document.getElementById('flagColor') as HTMLSelectElement).value }, 'flags')}
        />
      </FeatureCard>
    </div>
  )
}
