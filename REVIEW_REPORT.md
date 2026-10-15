# Clip Assassin review — October 15, 2026

## Result

Clip Assassin's own Python backend successfully connected to the installed DaVinci Resolve Studio **21.1.0.14**, read the active project, four timelines and live clip statistics. This was verified directly through the app's connection code and through its browser UI.

Functional edits were tested only in dedicated QA projects with generated media. The original project was restored after each group of tests; no edits were performed on the user's working timeline. QA projects were retained for inspection.

## Fixed

1. Removed duplicate/conflicting template and preset API routes, an undefined template database reference, unreachable late routes, and handlers that claimed to save templates without persisting anything.
2. Separated folder-template objects from Resolve asset filenames. This fixes the Templates page crash and missing asset import endpoint.
3. Added persistent custom folder templates, JSON editing/import/export, full recursive preview, loop index scopes, numeric/date formatting and matching folder creation.
4. Replaced template `eval` conditions with restricted AST comparisons; preflight validates paths, rejects traversal, bounds loops and preserves existing files.
5. Refreshed live Resolve project references, cleared stale connections, and serialized shared native API operations to prevent concurrent context changes.
6. Replaced whole-clip-only timecode deletion with exact partial-range assembly in a new timeline. Invalid lines abort the request; source edits remain intact.
7. Fixed marker-relative offsets, chapter timestamps, clip-number matching, selection order during merge and source-range preservation during extraction.
8. Added strict timecode validation and correct SMPTE drop-frame parsing/formatting.
9. Rebuilt J/L cuts using supported audio append operations in a duplicate rather than unsupported Start/End property writes that falsely reported success.
10. Corrected waveform sync to use Resolve's `AUDIO_SYNC_WAVEFORM` constant and the current API's `syncMode` key. The old code used the wrong value and option name.
11. Fixed silence export's audio codec, export flags, job-status field and job ID list. Added render-settings preservation, timeout handling, temporary job cleanup and the Python 3.13+ audio dependency.
12. Fixed thumbnail export's page context, marker offsets, non-integer frame rates, return-value checks and playhead/page restoration.
13. Fixed render queue numeric dimensions and live job status. Batch render now validates presets, fails on rejected jobs, restores the selected timeline, and uses a dropdown populated by Resolve.
14. Fixed social resolution duplication/name collisions, adjustment track creation, timeline-instance renaming, source-safe snapshots and mixed-frame-rate project duration totals.
15. Fixed ingest's loose media handling, media filtering and folder aliases. Ingest keeps the active project library and reports empty/failed imports rather than claiming full success.
16. Implemented real asset uploads with filename, type and size validation. `.drfx` packages open the correct installer; empty assets are shown as unavailable.
17. Fixed frontend HTTP validation messages, misleading success indicators, stale project selections, info-toast color, text-area keyboard shortcuts, manual navigation, visible chapter output, narrow-screen navigation and theme selection state.
18. Repaired macOS/Windows source launchers and installers that referenced missing Python files or absent environments. Added backend readiness checking, local environment support, consistent version labels and corrected the pywebview packaging module name.

## Verification

- **16 automated regression tests passed**: API uniqueness/validation, template CRUD, preview-to-disk equivalence for all three built-ins, loop scope, existing-file preservation, path protection, restricted conditions, drop-frame timecodes, normalized ranges, disconnected behavior, asset upload validation, native failure handling, sync settings and exact-duration rollback.
- **Frontend production build and lint passed**, with no lint warnings.
- **Python compilation and shell syntax checks passed.**
- **Browser review passed across all nine navigation pages**, with no console errors. The folder preview showed two distinct shoot days, and Export displayed installed Resolve render presets.

| Workflow | Actual Resolve result |
|---|---|
| Connection, context and statistics | Passed through Clip Assassin backend and UI |
| Master folders → Auto Ingest → timeline merge | Passed using synthetic card footage |
| Snapshot and clip-instance rename | Passed |
| Partial-range cut / keep | Passed: 147-frame source became 127 / 20 frames |
| Clip picker and marker extraction | Passed: selected edited section retained 49 frames |
| Flag filter | Passed; flags can apply to every instance of a shared source |
| BadWords clean | Passed: removed a 10-frame marker, retained 137 frames |
| 9:16 / 1:1 reframe | Passed |
| J/L cuts | Passed with two transitions and the source preserved |
| Silence remover | Passed: 147-frame source became 128 frames |
| Watermark | Passed on a new overlay track |
| Quick Title | Passed in QA project |
| Waveform sync | Passed on matching 30-second generated video/audio |
| Batch render / render queue | Job queued successfully; queue state read correctly |
| Marker thumbnails | Passed; JPEG and PNG export checked |
| CSV / Word shotlist | Both files created successfully |
| Adjustment Layer | Missing-asset error checked; positive execution needs a real Adjustment Clip in the Media Pool |
| Resolve asset installation | Package listing and upload validation checked; bundled installer was not installed during review |

Resolve 21.1 in this environment returned exclusive source end-frame behavior during append. Range assembly verifies actual appended duration and removes an incorrect output instead of reporting success if another Resolve version behaves differently.

## Remaining limitations

- Two original `.drfx` assets are zero-byte files. Their intended animations cannot be recovered from this source archive; replace them with valid originals.
- Adjustment Layer requires a Media Pool adjustment asset. This prerequisite is explained in the UI.
- J/L reconstruction requires aligned normal-speed clips and source handles. Audio clip FX, custom routing/channel mapping and automation need manual review in its duplicate.
- Output from range tools uses nested timelines; subsequent edits to the source can alter that output.
- The native subtitle backend is implemented but has not been tested with spoken audio. Cloud AI, YouTube OAuth upload and distributed background workers are outside the current wired UI.
- Windows/Linux runtime behavior, full installer packaging, long render completion and every codec/retime/multicam combination were not verified on this Mac.

## Suggested next improvements

1. Add a background job panel with progress, cancel and timeout reporting for ingest, sync, silence analysis and renders.
2. Add a visible dry-run summary of affected tracks/ranges and a link back to the source timeline before an editing operation.
3. Ship valid, versioned assets and show capability checks for Adjustment Clip, FFmpeg, Studio features and installed templates.
4. Add integration fixtures for mixed frame rates, retimed media, multiple audio channels, multicam, transitions and long timelines; run them on Windows/macOS with supported Resolve versions.
5. Connect AI transcription and optional OAuth upload only after adding explicit provider settings and user-controlled media submission.

Original source backup: `.review/original-source.tar.gz`.
Live QA results and export examples: `.review/`.
