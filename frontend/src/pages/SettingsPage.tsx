import { useState } from 'react'
import { Sparkles, MonitorUp, Activity, User, Mail } from 'lucide-react'
import { ActionButton } from '../components/ui'

const themes = [
  { name: 'Purple', primary: '#7e5cf5', bg: '#111318' },
  { name: 'Rose', primary: '#f43f5e', bg: '#111318' },
  { name: 'Emerald', primary: '#10b981', bg: '#111318' },
  { name: 'Cyan', primary: '#06b6d4', bg: '#111318' },
  { name: 'Amber', primary: '#f59e0b', bg: '#111318' },
]

interface Props {
  animationsEnabled: boolean
  setAnimationsEnabled: (v: boolean) => void
  setFavorites: (v: string[]) => void
  setLogs: (v: any[]) => void
  applyTheme: (theme: typeof themes[0]) => void
  addLog: (msg: string, type: 'info' | 'success' | 'error') => void
}

export function SettingsPage({ animationsEnabled, setAnimationsEnabled, setFavorites, setLogs, applyTheme, addLog }: Props) {
  const [themeName, setThemeName] = useState(localStorage.getItem('appTheme') || 'Purple')
  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-5 mb-5">
      <div className="section-heading"><div><h1>Settings</h1><p>Appearance and workspace preferences.</p></div></div>
      <div className="bg-black/20 backdrop-blur-3xl border border-white/5 rounded-[20px] p-6 shadow-2xl">
        <h3 className="text-sm font-semibold mb-4 text-white/80 uppercase tracking-wider flex items-center gap-2">
          <Sparkles size={16} className="text-brand-primary" /> App Customization
        </h3>
        <div className="flex gap-4">
          {themes.map(t => (
            <button
              key={t.name}
              onClick={() => { applyTheme(t); setThemeName(t.name) }}
              className={`w-8 h-8 rounded-full border-2 transition-all hover:scale-110 ${themeName === t.name ? 'border-white' : 'border-transparent'}`}
              style={{ backgroundColor: t.primary }}
              title={t.name}
            />
          ))}
        </div>
        <p className="text-xs text-white/40 mt-4">Select a theme color. It will automatically save and persist across sessions.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="bg-black/20 backdrop-blur-3xl border border-white/5 rounded-[20px] p-6 shadow-2xl">
          <h3 className="text-sm font-semibold mb-4 text-white/80 uppercase tracking-wider flex items-center gap-2">
            <MonitorUp size={16} className="text-brand-primary" /> App Preferences
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white/90">Interface animations</p>
                <p className="text-xs text-white/40 mt-0.5">Toggle subtle motion and transitions</p>
              </div>
              <button
                aria-label="Interface animations" role="switch" aria-checked={animationsEnabled}
                onClick={() => setAnimationsEnabled(!animationsEnabled)}
                className={`w-12 h-6 rounded-full transition-colors relative ${animationsEnabled ? 'bg-brand-primary' : 'bg-white/10'}`}
              >
                <div className={`w-4 h-4 rounded-full bg-white absolute top-1 transition-all ${animationsEnabled ? 'left-7' : 'left-1'}`} />
              </button>
            </div>
            <div className="pt-4 border-t border-white/5">
              <ActionButton
                text="Clear app activity"
                variant="secondary"
                onClick={() => setLogs([])}
              />
            </div>
          </div>
        </div>

        <div className="bg-black/20 backdrop-blur-3xl border border-rose-500/20 rounded-[20px] p-6 shadow-2xl">
          <h3 className="text-sm font-semibold mb-4 text-rose-400 uppercase tracking-wider flex items-center gap-2">
            <Activity size={16} /> Danger Zone
          </h3>
          <div className="space-y-3">
            <p className="text-xs text-white/40 mb-2">Reset the application if you encounter bugs or want a fresh start.</p>
            <ActionButton
              text="Reset Dashboard Defaults"
              variant="secondary"
              onClick={() => {
                setFavorites([])
                addLog('Dashboard reset to defaults', 'info')
              }}
            />
            <ActionButton
              text="Factory Reset App"
              variant="secondary"
              onClick={() => {
                Object.keys(localStorage).filter(key => key.startsWith('app') || key.startsWith('clipAssassin:')).forEach(key => localStorage.removeItem(key))
                window.location.reload()
              }}
            />
          </div>
        </div>
      </div>

      <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 grid grid-cols-1 md:grid-cols-2 gap-5 items-start">
        <div className="bg-black/20 backdrop-blur-3xl border border-white/5 rounded-[20px] p-6 shadow-2xl md:col-span-2">
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-sm font-semibold mb-3 text-white/80 uppercase tracking-wider">Developer Contact</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 rounded-xl bg-black/20 border border-white/5">
                  <User size={16} className="text-brand-primary/70" />
                  <div>
                    <p className="text-[10px] text-white/40 uppercase tracking-wider">Creator</p>
                    <p className="font-medium text-white/80 text-xs">Zabid Al Muttaki</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-xl bg-black/20 border border-white/5">
                  <Mail size={16} className="text-brand-primary/70" />
                  <div>
                    <p className="text-[10px] text-white/40 uppercase tracking-wider">Email</p>
                    <p className="font-medium text-white/80 text-xs">zabid.coder@gmail.com</p>
                  </div>
                </div>
              </div>
            </div>
            <div>
              <h3 className="text-sm font-semibold mb-3 text-white/80 uppercase tracking-wider">About Clip Assassin</h3>
              <p className="text-xs text-white/50 leading-relaxed mb-3">Clip Assassin is an advanced automation suite tailored specifically for DaVinci Resolve. Built to dramatically reduce repetitive tasks in professional post-production workflows.</p>
              <p className="text-[10px] font-mono text-brand-primary bg-brand-primary/10 px-2 py-1 rounded inline-block">Version 2.1.1</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
