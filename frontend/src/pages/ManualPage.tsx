import { useState } from 'react'
import { Activity, ArrowDownToLine, AudioLines, BookOpen, Check, ChevronDown, CircleHelp, Clapperboard, Cloud, FolderTree, Library, ListChecks, Search, Scissors, Settings2, Sparkles } from 'lucide-react'
import '../styles/manual.css'

type Guide = { title: string; purpose: string; steps: string[]; note?: string; keywords?: string }
type Chapter = { id: string; label: string; icon: typeof BookOpen; intro: string; guides: Guide[] }

const chapters: Chapter[] = [
  {
    id: 'overview', label: 'Start here', icon: BookOpen,
    intro: 'A practical reference for preparing a project, running a task safely and finding the result.',
    guides: [
      { title: 'A reliable first run', purpose: 'Use the same review-first sequence for every job that changes a project or creates files.', steps: ['Open DaVinci Resolve and open the project you intend to work on.', 'Check the project and active timeline in the app header. Select the correct timeline there when needed.', 'Open the matching workspace and enter its source, options and output location.', 'Choose the review action. Read the project, timeline, settings and warnings in the review screen.', 'Confirm the job. Follow its progress in Jobs & Results, then open the reported timeline or output path.'], note: 'Review again whenever the Resolve project, selected timeline or source media changes.' },
      { title: 'Enable the Resolve scripting connection', purpose: 'Allow this local app to control the Resolve session you opened.', steps: ['In Resolve, open Preferences → System → General.', 'Set “External scripting using” to “Local”, save, then close Preferences.', 'If Resolve asks to restart, restart it. Keep the target project open.', 'Return to Clip Assassin and select the Resolve status badge to check or reconnect.', 'If it still shows disconnected, make sure Resolve is open and the app server is running, then check the preference again.'], note: 'This app connects to the local Resolve scripting API. It does not connect to a cloud Resolve session.' },
      { title: 'Know where work happens', purpose: 'Understand the difference between the app workspace and Resolve.', steps: ['The app gathers settings and previews the intended change.', 'Resolve performs timeline, Media Pool and render operations in the open session.', 'The Jobs page records queued work, progress, logs, completion and available output actions.', 'The Templates page installs bundled or added packages into Resolve’s local template locations.'], keywords: 'connection timeline resolve' },
    ],
  },
  {
    id: 'ingest', label: 'Folders & ingest', icon: FolderTree,
    intro: 'Set up a production folder tree, then optionally create a Resolve project and separate timelines from card media.',
    guides: [
      { title: 'Build and save a folder preset', purpose: 'Create a reusable folder structure that matches how your team stores a project.', steps: ['Open Master Ingest and open Folder Presets. Choose a saved preset, or select New Preset.', 'Add, rename, reorder or remove folders in the visual tree. Use a loop when you want repeated camera, day or card folders.', 'Use custom fields to make project or client names part of the resulting paths. Give the preset a clear name and save it.', 'Use the preset actions menu to edit, duplicate or delete saved presets. Import or export JSON to move a preset between app installations.', 'Select the preset, enter the project details, choose its parent directory and inspect the expanded folder preview.', 'Create the folders only after the preview matches the intended project structure.'], note: 'Creating folders makes directories on disk. It does not move, copy or ingest footage.' },
      { title: 'Capture an existing folder structure', purpose: 'Turn an existing directory tree into a reusable preset.', steps: ['Choose New Preset or Edit to open the visual builder.', 'Expand “Capture or import an existing structure” and choose the folder to capture.', 'Select Capture folder names only. Review the generated tree, rename or remove folders you do not want, then save it as a preset.'], keywords: 'manual preset add existing directory' },
      { title: 'Prepare media for Auto Ingest', purpose: 'Keep camera cards separate while allowing camera, day and card folders to appear in different arrangements.', steps: ['Organize the project root so the footage sits below folders such as Raw Footages, Day 01, Sony A7, FX3 or Card 01. Any of these can be nested in a different order.', 'Open Auto Ingest and select the project root. Inspect the discovered media groups and their folder-path labels in Review.', 'Each folder containing footage becomes its own group and timeline. Files at a parent level stay in that parent group; they are not also repeated in child groups.', 'Known camera-card structures, including PRIVATE/M4ROOT/CLIP, AVCHD and DCIM, stay attached to the enclosing card group.', 'Separate Audio folders are imported into Audio & Music rather than turned into footage timelines. Export, cache and graphics folders are excluded.', 'Confirm only when every camera/day/card maps to the timeline you expect. The app creates a versioned Resolve project, Media Pool bins and an individual timeline for each group.'], note: 'Media is referenced in place, not copied. If you add or move files after review, scan and review again. Unsupported or empty footage stops before project creation. A codec failure or cancellation can leave a partial new Resolve project; inspect it before retrying.' },
      { title: 'Use the ingest review as a conflict check', purpose: 'Keep similarly named cards from different shoot days separate.', steps: ['Check that timeline labels include their parent folder path (for example Day 01 / Card 01 and Day 02 / Card 01).', 'Check that camera names appear in the path when cameras have separate cards.', 'Confirm audio-only folders appear as audio imports and do not create video timelines.', 'If the grouping is ambiguous, reorganize the source folders or rename them, then run the scan again before confirming.'], keywords: 'timeline card conflict camera day' },
    ],
  },
  {
    id: 'magic', label: 'Magic Tools', icon: Sparkles,
    intro: 'Quick actions for the active project, selected clips and playhead. Check the tool help icon for a short reminder inside the workspace.',
    guides: [
      { title: 'Timeline Snapshot', purpose: 'Save a copy of the active timeline before a substantial edit.', steps: ['Select the source timeline in the app header.', 'Run Timeline Snapshot and confirm the proposed copy.', 'Keep the snapshot as a recovery point; switch to it from Resolve if you need the pre-change edit.'] },
      { title: 'Magic Bin Organizer', purpose: 'Sort loose root-level Media Pool items into standard type bins.', steps: ['Open the intended project in Resolve.', 'Run the organizer and review its summary.', 'Check the Video, Audio and Image bins in the Media Pool. Items already inside nested bins are not the target of root-level organization.'] },
      { title: 'Batch Clip Renamer', purpose: 'Apply a numbered name pattern to clips on Video Track 1.', steps: ['Enter the prefix you want, such as Interview.', 'Review the affected clip count and sequence.', 'Confirm; Resolve names the clips Interview_001, Interview_002, and so on.'] },
      { title: 'Social Media Reframe', purpose: 'Create a portrait or square copy of the active timeline.', steps: ['Choose 9:16 or 1:1.', 'Review the output timeline and scale-to-crop behavior.', 'Confirm, then inspect important subjects near the frame edges. This uses a center crop and does not track faces.'] },
      { title: 'Quick Title', purpose: 'Place a Text+ title at the current playhead position.', steps: ['In Resolve, park the playhead where the title should begin.', 'Run Quick Title and review the active timeline and playhead.', 'Confirm, then edit the new Text+ title in Resolve.'] },
      { title: 'Quick Adjustment Layer', purpose: 'Add an adjustment clip on Video Track 5 without moving existing clips.', steps: ['Make sure an Adjustment Clip is available in the Resolve Media Pool.', 'Park the playhead where the layer should begin.', 'Run the tool and confirm. Inspect its duration and track placement in Resolve.'] },
      { title: 'Multi-Cam Auto Sync', purpose: 'Synchronize separately recorded audio with selected video by waveform.', steps: ['Select at least one video and one matching audio clip in the Media Pool.', 'Run Auto Sync and review the selected media.', 'Confirm, then inspect the synchronized result and audio alignment in Resolve.'] },
      { title: 'BadWords Cleaner', purpose: 'Find BadWords marker colors and create a cleaned timeline that omits flagged sections.', steps: ['Scan the active timeline for markers.', 'Choose which marker colors should identify sections to remove.', 'Review the detected marker list and proposed result, then confirm.', 'Check the new timeline before using it as a final edit.'] },
    ],
  },
  {
    id: 'cut', label: 'Cut & Trim', icon: Scissors,
    intro: 'These tools build a new timeline from the active source timeline; they leave the source timeline available for comparison.',
    guides: [
      { title: 'Timecode Cutter', purpose: 'Keep or remove exact time ranges to create a new timeline.', steps: ['Enter ranges such as 00:01:30-00:02:00 or 1:30-2:00.', 'Choose whether listed ranges are the sections to keep or remove.', 'Review each boundary in the preview before confirming.', 'Numeric-only time values are seconds. Timecode boundaries are placed to the timeline frame rate.'], note: 'Valid 29.97/59.94 drop-frame timecodes are supported. Check range ordering and the new timeline before continuing.' },
      { title: 'Clip Picker', purpose: 'Build a timeline from selected clip names or one-based clip numbers.', steps: ['Enter clip numbers and ranges such as 1-5, Interview, 10-15.', 'Use the source timeline’s V1 clip order for numbered entries; numbering starts at 1.', 'Review matched clips and their order. Confirm to create the new timeline.'] },
      { title: 'Markers to Timeline', purpose: 'Create a timeline from clips associated with a selected marker color.', steps: ['Choose the marker color to extract.', 'Review the matching clips and their sequence.', 'Confirm and inspect the generated timeline.'] },
      { title: 'Flag Filter', purpose: 'Create a timeline from clips carrying a selected flag color.', steps: ['Choose a flag color.', 'Review the clips that match.', 'Confirm and check the resulting order in Resolve.'] },
    ],
  },
  {
    id: 'process', label: 'Process', icon: AudioLines,
    intro: 'Processing tools assemble or modify a copy. Compare the output in Resolve before replacing your source workflow.',
    guides: [
      { title: 'Merge Timelines', purpose: 'Append selected timelines into one master timeline.', steps: ['Choose at least two timelines and arrange them in the intended order.', 'Review the source list and resulting sequence.', 'Confirm, then check transitions, track alignment and duration in the new master.'] },
      { title: 'Watermark Track', purpose: 'Add a supplied image as a watermark on an upper video track.', steps: ['Choose a supported logo or watermark image.', 'Select the active timeline and review its expected duration and track placement.', 'Confirm, then inspect sizing, alpha and positioning in Resolve.'] },
      { title: 'Auto J-Cut / L-Cut', purpose: 'Create an audio-overlap copy for aligned picture and sound edits.', steps: ['Use a timeline with aligned V1/A1 clips and enough source handles at each edit.', 'Choose the overlap amount and J-cut or L-cut behavior.', 'Review the proposed boundaries, then create the copy.', 'Listen through each edit and inspect clip effects, automation and routing manually.'], note: 'J-cut starts the next clip’s audio early; L-cut lets the current clip’s audio continue over the next picture. Tight edits without source handles may not have room for the overlap.' },
      { title: 'Silence Remover', purpose: 'Analyze timeline audio and create a new timeline with detected silent regions removed.', steps: ['Install the optional audio dependencies and FFmpeg if the capability check says they are missing.', 'Choose detection sensitivity and minimum silence duration.', 'Review detected regions before confirming.', 'Listen to the resulting joins and restore any pauses that carry meaning.'], note: 'Audio analysis and cuts are automated; always audition the result.' },
    ],
  },
  {
    id: 'export', label: 'Export', icon: ArrowDownToLine,
    intro: 'Export tools either prepare Resolve render jobs or write supporting files to the selected output directory.',
    guides: [
      { title: 'Batch Timeline Render', purpose: 'Queue one or more selected Resolve timelines using a render preset.', steps: ['Select the timelines and an installed Resolve render preset.', 'Choose or confirm the output directory and review the queue summary.', 'Confirm to add render jobs to Resolve’s Deliver queue.', 'Start rendering in Resolve, or open the completed queue job under Jobs & Results and choose Review & render videos.', 'Inspect the output files and Resolve render status.'], note: 'Existing output files are left in place. Choose a distinct output path if you need another version.' },
      { title: 'Extract Thumbnails', purpose: 'Save still frames from timeline markers or the timeline center.', steps: ['Choose Markers to export a still at each marker, or Center for one still.', 'Choose an output directory and inspect the source timeline.', 'Confirm, then open the output folder from the completed job.'] },
      { title: 'Auto YouTube Chapters', purpose: 'Format timeline markers as timestamped YouTube chapter text.', steps: ['Check marker names and positions in Resolve; YouTube chapter lists need a first chapter at 00:00.', 'Run the tool and review the generated timestamp list.', 'Copy or save the result from the job output and check chapter labels before publishing.'] },
      { title: 'Client Shotlist / Document Exporter', purpose: 'Export the active timeline’s Video Track 1 shot list as CSV or Word.', steps: ['Choose CSV or Word (.docx).', 'Select an optional Word template when that format is chosen.', 'Set an output file path and review the source timeline.', 'Confirm and open the generated file to check client-facing names and data.'] },
    ],
  },
  {
    id: 'templates', label: 'Templates', icon: Library,
    intro: 'The app includes twelve bundled DaVinci Resolve .drfx packages. Review the package and its requirements before installing.',
    guides: [
      { title: 'Install a bundled .drfx package', purpose: 'Add titles, transitions, effects and related assets to your local Resolve installation.', steps: ['Open Templates and select a bundled package. The built-in set contains 12 packages and 547 catalogued template entries.', 'Read the package notes and font status. Open the preview to inspect available examples.', 'Choose Review & install. Read the planned paths, conflicts and replacement behavior before confirming.', 'Wait for verification and installation to finish, then restart Resolve and look in the relevant Effects Library section.', 'If Resolve does not show an item, return to the package details and run Verify or Repair.'], note: 'Some supplied packages include font names and download links but not font binaries. Install needed fonts through the operating system, then refresh the font check and restart Resolve. Six NeoFX Fuse dependencies are also bundled with their package.' },
      { title: 'Add your own package or template folder', purpose: 'Extend the library with local assets you are licensed to use.', steps: ['Use Add Folder or upload a .drfx package in Templates.', 'Wait for scanning to finish, then open the package and review its contents and notes.', 'Preview and verify the files before choosing an install action.', 'Restart Resolve after installation.'], note: 'Large uploads are streamed (up to 512 MiB). Do not close the app while a package scan or install job is running.' },
      { title: 'Repair, replace or remove managed files', purpose: 'Safely maintain files installed through the Clip Assassin library.', steps: ['Run Verify to compare the package with its installed files.', 'Use Repair for missing or altered managed files.', 'When a conflict needs replacement, read the list of originals that will be backed up before confirming.', 'Use managed Remove to uninstall files tracked for that package. Check the package result before removing dependencies used by another item.'] },
    ],
  },
  {
    id: 'connections', label: 'Connections', icon: Cloud,
    intro: 'Connections reports local readiness and configures optional transcription and YouTube features. Cloud actions always need your review.',
    guides: [
      { title: 'Read capability checks', purpose: 'See whether Resolve, FFmpeg, local Whisper, cloud SDKs and secure credential storage are ready.', steps: ['Open Connections and wait for the checks to finish.', 'Use Check again after installing a dependency or changing Resolve settings.', 'Follow the detail shown beside any unavailable capability. Resolve must be running for its scripting connection.'] },
      { title: 'Generate subtitles in Resolve', purpose: 'Use Resolve Studio’s native speech features without uploading media to a cloud provider.', steps: ['Select a timeline with speech in Resolve.', 'Choose Review subtitle generation from Connections.', 'Check the transcription options in the review step and confirm.', 'Inspect the resulting subtitle track in Resolve.'] },
      { title: 'Configure media transcription', purpose: 'Save a transcript and timestamped JSON from an audio or video file.', steps: ['Install integrations with “python -m pip install -r requirements-integrations.txt”. Install openai-whisper separately to use local Whisper.', 'Choose Local Whisper or OpenAI. Local Whisper may download the selected model on first use.', 'Choose the input media file, optional language code (such as bn or en), and output directory.', 'For OpenAI, enter your own key under Connections and explicitly tick the media-sharing consent on the transcription form.', 'Review the selected provider, file and output path before confirming.'], note: 'Cloud transcription sends the selected media to OpenAI and may incur API charges. Local Whisper processes on this device after its model is available.' },
      { title: 'Connect a YouTube account', purpose: 'Authorize the app to upload videos through your Google account.', steps: ['In Google Cloud, create a Desktop OAuth client and enable YouTube Data API access for the project.', 'In Connections, import the client JSON or enter the client ID and secret, then save the client settings.', 'Choose Connect YouTube and complete sign-in in your system browser.', 'Return to Connections and confirm the account shows as connected.'], note: 'OAuth credentials are stored using the OS credential manager when available. The app does not bundle credentials or your account authorization.' },
      { title: 'Review a YouTube upload', purpose: 'Upload a rendered video with explicit visibility and consent.', steps: ['Connect the account first.', 'Choose the video file, title, description and visibility (Private is the default).', 'Tick the upload consent for the selected video and visibility.', 'Review the upload details before confirming. Follow the job until YouTube returns its result.'], note: 'Uploads use resumable chunks. Cancellation takes effect between chunks; a video that has already completed upload remains in your YouTube account.' },
    ],
  },
  {
    id: 'jobs', label: 'Jobs & settings', icon: Activity,
    intro: 'Use the job record to understand what happened before repeating an action.',
    guides: [
      { title: 'Track a job, open results or retry', purpose: 'Review completed work and recover from an interrupted operation.', steps: ['Open Jobs & Results to see queued, running, completed, failed and cancelled work.', 'Open a job for its progress checkpoints, log and result details.', 'Use an output link or reveal/open-folder action to inspect generated files.', 'Retry only after reading the error and checking whether the earlier job created partial work.', 'For a cancellable job, use Cancel and wait for its safe checkpoint before closing the app.'], note: 'A native Resolve call already in progress must finish before cancellation takes effect. Folder creation and ingest may retain completed steps; template installation attempts to roll back files.' },
      { title: 'Use app preferences', purpose: 'Adjust the appearance and clear app data deliberately.', steps: ['Open Settings to choose an accent color or motion preference.', 'Use Clear app activity to clear the recent activity feed.', 'Use Reset Dashboard Defaults to restore dashboard choices.', 'Factory Reset App clears broader app configuration. Read the on-screen confirmation carefully before proceeding.'] },
      { title: 'Keyboard shortcuts', purpose: 'Jump between major workspaces without searching the sidebar.', steps: ['Use Cmd/Ctrl+1 through Cmd/Ctrl+6 to open Magic Tools, Cut & Trim, Process, Export, Templates or Manual.', 'Use Cmd/Ctrl+K to open tool search when available.', 'Use Cmd/Ctrl+S to create a Timeline Snapshot.', 'The ? beside a tool opens a short contextual explanation while you stay in the workspace.'], keywords: 'hotkey keyboard shortcut help popup' },
    ],
  },
  {
    id: 'troubleshooting', label: 'Troubleshooting', icon: CircleHelp,
    intro: 'Check the source, connection and most recent job record before repeating a failed action.',
    guides: [
      { title: 'Resolve shows disconnected', purpose: 'Restore the local scripting connection.', steps: ['Open Resolve and the target project. Check Preferences → System → General → External scripting using: Local.', 'Save the preference and restart Resolve if prompted.', 'Return to the app and use the Resolve status badge to reconnect.', 'Open Jobs & Results or the app activity details for the exact connection error.'] },
      { title: 'An action fails or is only partly complete', purpose: 'Identify whether an error happened before or after Resolve started changing the project.', steps: ['Open the failed job and read its message and last completed checkpoint.', 'Check the Resolve project, timeline and Media Pool for partial results.', 'Verify the correct source timeline and output folder are still available.', 'Fix the reported dependency, source path or setting, then preview the job again before retrying.'] },
      { title: 'A template is missing in Resolve', purpose: 'Resolve package, font or dependency issues.', steps: ['Restart Resolve after installation.', 'Run Verify for the selected package and read any missing file or dependency details.', 'Install any required fonts in the operating system, refresh font status, then restart Resolve.', 'Run Repair for missing managed files and inspect package notes for required Fuse dependencies.'] },
      { title: 'Media is grouped into unexpected timelines', purpose: 'Correct the source folder names before an ingest creates a Resolve project.', steps: ['Use the Auto Ingest review to identify the exact folder path that became each timeline.', 'Make ambiguous camera, day or card folder names distinct.', 'Move unrelated assets such as graphics, cache and exports outside the footage tree.', 'Scan again and check that duplicate-looking Card 01 names retain their distinct parent paths.'] },
      { title: 'Find the app’s local setup requirements', purpose: 'Check supported launch routes and dependency setup.', steps: ['macOS: run Run_Clip_Assassin.command or “.venv/bin/python launch.py”. Windows: run INSTALL.bat, then RUN_CLIP_ASSASSIN.bat.', 'The browser opens locally at http://127.0.0.1:8000 when the backend is ready. Keep the launch terminal open.', 'The development setup uses Python 3.10+, Node.js 20.19+ and npm; FFmpeg is recommended.', 'Optional transcription and YouTube integrations need their own packages or Google OAuth credentials.'], keywords: 'install launch setup localhost server python node' },
    ],
  },
]

const quickFlow = [
  { number: '01', title: 'Connect', text: 'Open Resolve and confirm the project and timeline.' },
  { number: '02', title: 'Configure', text: 'Choose a tool and enter its source and options.' },
  { number: '03', title: 'Review', text: 'Check the preview, target and any warnings.' },
  { number: '04', title: 'Run', text: 'Confirm, then follow the job to its result.' },
]

export function ManualPage() {
  const [active, setActive] = useState('overview')
  const [query, setQuery] = useState('')
  const normalized = query.toLocaleLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
  const searchTerms = normalized ? normalized.split(/\s+/) : []
  const visibleChapters = chapters
    .map(chapter => ({ ...chapter, guides: chapter.guides.filter(guide => {
      const searchable = `${guide.title} ${guide.purpose} ${guide.steps.join(' ')} ${guide.note ?? ''} ${guide.keywords ?? ''} ${chapter.label}`.toLocaleLowerCase().replace(/[^a-z0-9]+/g, ' ')
      return !searchTerms.length || searchTerms.every(term => searchable.includes(term))
    }) }))
    .filter(chapter => chapter.guides.length > 0)

  const chooseChapter = (id: string) => {
    setActive(id)
    setQuery('')
    requestAnimationFrame(() => document.getElementById(`guide-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
  }

  return <main className="manual-page">
    <header className="manual-hero">
      <div className="manual-hero-mark"><BookOpen size={20}/><span>FIELD GUIDE</span><span className="manual-version">2.1.1</span></div>
      <h1>User Manual</h1>
      <p>Clear, practical instructions for preparing projects, working in Resolve and getting dependable results from Clip Assassin.</p>
      <label className="manual-search"><Search size={17}/><input aria-label="Search the user manual" placeholder="Search tools, tasks, settings…" value={query} onChange={event => setQuery(event.target.value)}/><kbd>⌘ K</kbd></label>
    </header>

    <section className="manual-flow" aria-label="Standard workflow">
      <div className="manual-section-kicker"><ListChecks size={15}/> YOUR WORKFLOW</div>
      <div className="manual-flow-steps">{quickFlow.map(step => <div className="manual-flow-step" key={step.number}><span>{step.number}</span><div><strong>{step.title}</strong><p>{step.text}</p></div></div>)}</div>
    </section>

    <nav className="manual-nav" aria-label="Manual sections">
      {chapters.map(chapter => { const Icon = chapter.icon; return <button key={chapter.id} type="button" className={active === chapter.id && !normalized ? 'active' : ''} onClick={() => chooseChapter(chapter.id)}><Icon size={14}/>{chapter.label}</button> })}
    </nav>

    <div className="manual-content">
      {visibleChapters.map(chapter => {
        const Icon = chapter.icon
        return <section className="manual-chapter" id={`guide-${chapter.id}`} key={chapter.id}>
          <div className="manual-chapter-heading"><span className="manual-chapter-icon"><Icon size={17}/></span><div><h2>{chapter.label}</h2><p>{chapter.intro}</p></div><span className="manual-chapter-count">{chapter.guides.length} {chapter.guides.length === 1 ? 'guide' : 'guides'}</span></div>
          <div className="manual-guides">{chapter.guides.map((guide, index) => <details className="manual-guide" key={guide.title} open={Boolean(normalized)}>
            <summary><span className="manual-guide-index">{String(index + 1).padStart(2, '0')}</span><span className="manual-guide-summary"><strong>{guide.title}</strong><small>{guide.purpose}</small></span><ChevronDown size={16} className="manual-guide-chevron"/></summary>
            <div className="manual-guide-body"><ol>{guide.steps.map(step => <li key={step}><span className="manual-step-check"><Check size={11}/></span><span>{step}</span></li>)}</ol>{guide.note && <aside><Settings2 size={14}/><span>{guide.note}</span></aside>}</div>
          </details>)}</div>
        </section>
      })}
      {!visibleChapters.length && <div className="manual-empty"><Search size={19}/><strong>No matching guidance</strong><span>Try another tool name or search term.</span><button type="button" className="secondary-button" onClick={() => setQuery('')}>Clear search</button></div>}
    </div>

    <footer className="manual-footer"><div><Clapperboard size={16}/><span>Clip Assassin · DaVinci Resolve workflow guide</span></div><span>Tool-specific <b>?</b> help is also available beside each workspace tool.</span></footer>
  </main>
}
