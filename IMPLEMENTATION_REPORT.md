# Clip Assassin 2.1.0 — implementation and verification

## Delivered

The twelve supplied `.drfx` packages are now physically included under `templates/bundled/`, together with their font/install notes, preview images where available, and NeoFX Core's six Fuse dependencies. They contain **547 usable `.setting` entries** and approximately **159 MiB of bundled assets**. The application does not need the original `Davinci Plugin` folder to list or install these built-ins. Both packaging paths already include the entire `templates` directory.

| Built-in package | Template entries |
|---|---:|
| Number Counter Pack | 9 |
| Animated Text Pack 2.0 | 135 |
| Caption Creator Pack | 194 |
| NeoFX Core Pack | 9 |
| Neo Highlighter Pro | 1 |
| Motion Essentials Pack | 16 |
| SaaS Text Animation | 12 |
| Trendy Titles | 12 |
| Animated Calendar | 124 |
| Finance Infographic Widgets | 6 |
| Text Animation Light | 9 |
| Text Elite Presets | 20 |

The Library has package search, category filtering, thumbnails, size/template counts, font readiness, original notes, install locations, installation review, verification, repair and managed removal. The six separate NeoFX Fuse files install with their package. Additional local folders can be scanned; duplicate package checksums are skipped. Uploaded `.drfx` files are validated and registered, and uploads stream to disk with a 512 MiB limit instead of buffering large files in memory.

## Installation behavior

1. The user selects a package and sees the required fonts, dependencies and Effects Library locations.
2. Review lists the destination and file count. Replacing existing files requires the explicit repair/replace checkbox.
3. The installer validates the archive, skips Finder/Windows metadata, stages files, backs up conflicting originals and preserves the `Edit/Titles`, `Effects`, `Generators` and `Transitions` structure.
4. Installation verifies file hashes and writes a managed manifest. Failure or cancellation during installation rolls back applied files.
5. Verify detects missing/changed managed files. Remove touches only tracked files, restores backed-up originals and retains shared dependencies until the last owning package is removed.
6. The user restarts Resolve to load newly installed templates, Fuses and fonts.

Fonts are not included as binary files in the supplied download. Their original download links are included; missing fonts can be downloaded and their TTF/OTF files opened in the OS font installer from the app. Font status is checked against the real font database: this Mac returned 680 families through AppKit. Unknown font-detection results are displayed as needing a check rather than being claimed as missing.

## Folder presets

Master Folder Setup now uses the saved template catalog rather than its previous hardcoded selector. **New Preset, Edit and Duplicate are available in that screen.** The visual builder supports nested folders, files, up/down ordering, repeated camera/card folders, fixed or parameter-based loop counts, text/number/date/select/boolean inputs, defaults and required fields. It also supports capturing directory names from an existing folder, and JSON import/export.

Saved presets appear immediately in the setup menu and survive reload. The selected preset is remembered. Expanded preview uses the same validated generator as actual folder creation. A usable **Two Camera Documentary** preset was created and retained while testing the interface.

## Shared guided tools

The four editing/export sections now show a tool list on the left and one selected workspace on the right. All twenty tools use the same header, input sizing, help text, spacing, steps and action treatment. Master Setup and the new provider tools use the same card system. Narrow screens stack the navigation and workspace.

A task opens **Source & settings → Review → Confirm & run → Jobs & results**. Review uses readable field labels and avoids showing package/template database IDs. Signed previews expire after ten minutes. Resolve jobs verify the project/timeline identity again when execution begins; selected media IDs are also checked for audio sync.

## Jobs and render progress

A local single-worker queue provides persistent history, progress checkpoints, elapsed time, logs, result locations, cancellation and reviewed retries. Status polling stays available during long native work. Unfinished jobs are marked interrupted after an app restart.

Cancellation is cooperative. Package installation rolls back. Silence analysis stops its temporary render at a checkpoint. A native call already in progress must return before cancellation can be acted on; a successfully completed native call is recorded as completed. Cancelled multi-step folder/ingest operations can leave completed steps, which are described in the UI rather than being represented as a full rollback.

Batch rendering still first queues the selected timelines. Its job result now offers **Review & render videos**, which starts only the selected render jobs, reports their actual completion percentages and stops the render it started if cancelled or timed out. It refuses to interfere with a render already in progress.

## Connections

The Connections screen checks Resolve, FFmpeg, audio analysis, optional local speech support and the required Media Pool Adjustment Clip. It includes:

- Resolve's native subtitle generation.
- Optional local Whisper transcription with a model selector.
- OpenAI transcription with explicit media-sharing consent and an API-key setup screen.
- Google Desktop OAuth client JSON import, secure client-secret storage, YouTube sign-in/disconnect, and resumable video upload with title, description and privacy review.

Provider credentials use the OS credential store through `keyring`; they are not placed in job payloads or browser storage. No account credentials are bundled. The optional cloud SDKs were installed in this workspace's `.venv`. Local Whisper/model weights were not installed. A working API key or Google Desktop OAuth client/account is still required before those respective cloud workflows can be exercised. No cloud transcription, account sign-in or YouTube upload was performed during this implementation.

API implementations followed the official [OpenAI transcription reference](https://developers.openai.com/api/reference/resources/audio/subresources/transcriptions/methods/create), [Google Desktop OAuth guide](https://developers.google.com/youtube/v3/guides/auth/installed-apps) and [YouTube resumable upload guide](https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol).

## Verification

- **35 regression tests passed.** They cover the earlier fixes plus bundled checksums/resources, archive traversal and metadata handling, install verification/repair/removal, backup restoration, cancellation rollback, shared-file ownership, duplicate scans, font uncertainty, persistent job history, source pinning, preview-token tampering, consent enforcement, directory capture, job submission and render completion/cancellation.
- **All twelve real packages** were installed, fully hash-verified and removed in isolated QA directories. This included the 152.8 MiB Text Animation Light package and all six NeoFX Fuses. The user's actual Resolve plugin directories were not modified during these tests.
- **Actual Resolve 21.1 job execution passed:** preview → queue → snapshot, partial cut (127 output frames), marker extraction (49 frames), J-cut, silence removal (128 frames), batch queue and an actual completed video render.
- The original working project was restored after Resolve tests.
- **Browser checks passed for all eleven pages and all twenty editing/export tool workspaces**, without console errors.
- The visual preset builder was tested through the browser: a two-camera preset was saved, selected, expanded, reviewed and used to create the expected seven directories in `.review/guided-output/`.
- **Frontend production build, lint, Python compilation and launcher shell syntax passed.**

Evidence: `.review/bundled-install-results.json`, `.review/native-job-results.json`, `.review/job-render-output/` and saved UI screenshots.

## Practical boundaries

File installation tests confirm package integrity, paths and reversibility; rendering every third-party template inside a restarted Resolve session was not performed. Some require the linked fonts and Resolve version/features supplied by their author. Native subtitle generation needs suitable speech media. Cloud execution requires the user's account setup; Windows/Linux runtime and signed installer distribution still need their own platform tests.

Source backup before this implementation: `.review/pre-bundled-library-source.tar.gz`.

## Compact layout and nested ingest update — 2026-10-15

Removed the secondary vertical tool navigation, repeated workflow steps, inline instructions and workflow footer. Sections use compact tabs (or a selector for the eight Magic tools); cards keep a title, one-line description, fields and actions. Master Ingest uses Folder Setup / Auto Ingest tabs and a preset actions menu. Tool-specific help opens User Manual; all former inline guidance is preserved there. Source context remains in the main header.

Auto Ingest now uses a shared read-only plan for preview and execution. Camera/day/card names and depth are unrestricted. Each media-bearing directory is an individual group, with full relative path in its timeline name and matching nested Media Pool bins. Known camera storage structures (PRIVATE, AVCHD, DCIM, M4ROOT, CONTENTS, etc.) stay with the enclosing card. Parent-level media is separate from descendants. Natural filename ordering, deterministic name collision suffixes, metadata/cache/output filtering, symlink avoidance and hard-link deduplication prevent accidental mixing or repeated imports. Separate project-level audio imports into Audio & Music. Review lists every folder → timeline mapping. The file-list fingerprint is checked again at job start; an empty plan stops before project creation. Import/timeline failures report a partial result instead of silent success.

Verification: **40 tests pass**, production build and lint pass. Browser checked all 20 editing/export tools, both Master Ingest tabs, preset actions, tool-specific manual links and nested mapping review; no JavaScript errors. Native preview → queue → job imported generated QA media into **5 distinct timelines**, including Day 01/FX3/Card 01/PRIVATE/M4ROOT/CLIP and Smartphone/Card 02/DCIM/100MEDIA, plus separate audio. The original working Resolve project was restored. Evidence: `.review/nested-ingest-results.json`, `.review/compact-master-ingest.png`, `.review/nested-ingest-review.png`. Unknown camera storage conventions follow the visible grouping rule and must be checked in Review; this does not infer recording sessions from arbitrary names or metadata.

## Approved glass redesign and local help — 2026-10-15

Implemented the approved visual direction across the app: charcoal surfaces, glass navigation with distinct hover/active/focus states, unified violet controls, a simplified project/timeline header, and a quieter sidebar. All eight Magic tools are directly visible in the same icon-tab system as Master Ingest and the editing/export sections; there is no tool dropdown. Dashboard guidance was shortened. Session activity moved from the sidebar into a collapsed App activity section in Jobs & Results, alongside the persistent job history. Theme accents and interface-motion preferences continue to work; mobile navigation uses readable labels.

Each tool's question-mark control now opens a small anchored details popup without navigating or resetting form values. Popups support close, outside-click, Escape and keyboard focus dismissal. User Manual remains independently accessible. The tabs support arrow-key navigation, Home/End and visible keyboard focus.

Validation: production build and lint pass; the existing 40 regression tests pass. Browser interaction verified **25 tool-help popups**, all 22 main tool tabs, Escape/outside-click dismissal, preserved form input, enabled timeline selector, restored theme/motion preferences, and zero console errors. A 390×844 responsive check verified all eight Magic tools remain accessible and the popup stays within the viewport; the normal viewport was restored. Final screenshots: `.review/glass-master-ingest.png` and `.review/glass-magic-tools-help.png`. Pre-change source backup: `.review/pre-glass-redesign.tar.gz`. No Resolve project edits were needed for this visual update.

## Surface contrast refinement from Settings reference

Applied the supplied Settings-page direction across the workspace: a charcoal canvas, darker work panels, inset dark controls, quieter borders, clearer label/value contrast and restrained accent use. Tool workspaces now sit on a distinct rounded panel instead of blending into the page background. Navigation retains its glass affordance with reduced bloom; sidebar, header, templates, jobs and dialogs use the same surface hierarchy. Native controls use dark color scheme, including the date picker. Existing selected accent preference is preserved.

Production build and lint pass. Browser review checked Master Ingest, the eight Magic tabs and local help, and the template library, with no console errors. Evidence: `.review/premium-surface-master.png` and `.review/premium-surface-magic.png`. This pass changes CSS only; tool/backend logic is unchanged.

## Collapsed form repair and connection header refinement

Fixed the shared action-wrapper rule that assigned full width to an action sibling inside horizontal form rows, squeezing the preceding fields. Replaced the broad `:has()` layout override and percentage-width wrappers with explicit action slots, stacked settings/action layouts and responsive field grids across Export, Process, Cut and Magic tools. Preset labels and selection actions wrap independently. Browse controls now occupy a dedicated grid cell inside the input container rather than relying on an absolute icon position. Master Ingest's preset selector wraps onto its own row when space is limited. Added an accessible Shotlist format label and readable output/template field labels.

The header now uses aligned Project and Timeline context tiles and a compact Resolve status card with an icon, app label, explicit connection state and reconnect affordance. Connected, connecting and disconnected have distinct presentation; the existing reconnect action is preserved.

Validation: build and lint pass. Browser geometry checks covered all **20 editing/export tools at 900px and 390px**, with zero collapsed (<120px) or out-of-panel text/select controls. At 320px, Export's preset remained 240px wide, path input 198px plus a contained 32px Browse button; the master preset remained 240px wide. Conditional Word-template input was checked and format restored to CSV. Browser console had no errors; normal viewport restored. Evidence: `.review/form-layout-checks.json`, `.review/export-layout-header-fixed.png`. Backend/tool operations were not changed.
