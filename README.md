# Clip Assassin 2.1.1

Local workflow automation for DaVinci Resolve, with a bundled template library, visual folder presets and guided editing jobs.

## Run on this Mac

Double-click `Run_Clip_Assassin.command`, or run:

```bash
.venv/bin/python launch.py
```

The browser opens at http://127.0.0.1:8000 after the backend is ready. Keep the terminal running. In Resolve Studio Preferences → System → General, set **External scripting using** to **Local**.

## Built-in Resolve templates

All twelve supplied `.drfx` packages are included inside the app under `templates/bundled/`: 547 template entries, font/install notes, available preview images and six NeoFX Fuse dependencies. The original download folder is not required.

The 160 MB Text Animation Light source package is tracked with Git LFS because GitHub blocks regular Git files above 100 MiB. Install Git LFS before cloning the source repository (`brew install git-lfs`, then `git lfs install`) so the real package is downloaded instead of its pointer. GitHub includes 10 GiB of LFS storage and bandwidth on Free and Pro accounts; actual availability depends on the account's existing usage. [GitHub's large-file guidance](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) · [LFS quota details](https://docs.github.com/en/billing/concepts/product-billing/git-lfs).

Open **Templates**, select a package, check its fonts, and choose **Review & install**. The app stages and verifies installation, backs up explicitly allowed replacements and tracks managed files for repair/removal. Restart Resolve after installation. Font binaries were not present in the supplied packages; use their download links and **Open font installer**, then recheck installed fonts.

The Library also supports additional local package folders and streamed uploads up to 512 MiB. See `IMPLEMENTATION_REPORT.md` for the complete package list and verified behavior.

## Folder presets and project ingest

Open **Master Ingest**. Select a saved folder preset or use **New Preset** or **Edit / Duplicate** in the preset actions (⋯) menu. Build folders visually, add camera/card loops and custom inputs, capture an existing directory structure, or import/export JSON. Presets persist in SQLite and appear in the setup selector.

Enter project details, choose a parent directory, preview, then review and create folders. Copy footage into the prepared card folders and use **Auto Ingest** to create a versioned Resolve project, bins and card timelines in the active project library.

## Guided tools and jobs

Cut & Trim, Magic Tools, Process and Export use a tool list and a common workspace. A task follows **Settings → Review → Confirm & run → Jobs & results**. Source project/timeline identity is checked when a queued Resolve task starts.

Jobs provide persistent history, actual progress checkpoints, logs, reviewed retries, cancellation and output links. An in-flight native call must finish before cancellation takes effect. Installation cancellation rolls back files; folder/ingest jobs can retain completed steps.

Batch Render queues timelines first. From its job result, choose **Review & render videos** to render those selected jobs with actual progress and cancellation. Existing renders are left alone.

Cut, extract, merge, BadWords and silence tools build new nested timelines. Source edits made afterward can affect those nested results. Numeric cut timestamps are seconds; timestamp/timecode formats and valid 29.97/59.94 drop-frame timecodes are supported. Clip picker numbers are one-based V1 positions.

J/L cuts require aligned V1/A1 clips and source handles. Review audio FX/routing in the duplicate. Adjustment Layer requires an **Adjustment Clip** in the Media Pool. Auto Sync needs a video and matching separate audio selected in the Media Pool. Reframe uses center cropping; it does not perform face tracking.

## Optional speech and YouTube connections

**Connections** checks local capabilities, exposes Resolve subtitle generation, and configures local Whisper, OpenAI transcription and YouTube OAuth/upload. Cloud operations require an explicit media-sharing/upload choice followed by review. Credentials are stored through the OS credential manager, not job payloads or browser storage.

```bash
.venv/bin/python -m pip install -r requirements-integrations.txt
# Optional local speech engine; its model downloads on first use:
.venv/bin/python -m pip install openai-whisper
```

Add an OpenAI API key for cloud transcription. For YouTube, create a Google Desktop OAuth client with YouTube Data API enabled, import its JSON in Connections, save settings and connect the account. Upload defaults to private. No credentials or account authorization are included with the app.

## Installation and verification

Requires Python 3.10+, Node.js 20.19+ and npm. FFmpeg is recommended. This workspace was checked on macOS with Python 3.14 and Resolve Studio 21.1.0.14.

```bash
./install.sh
./Run_Clip_Assassin.command
```

Windows: run `INSTALL.bat`, then `RUN_CLIP_ASSASSIN.bat`. A native window is available through `.venv/bin/python desktop_app.py`. Native Windows/Linux runtime and distributable installers still need platform testing.

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q tests
npm --prefix frontend run build
npm --prefix frontend run lint
```

`CLIP_ASSASSIN_DB_PATH` isolates the settings/jobs database. `CLIP_ASSASSIN_FUSION_DIR` overrides the installation target for QA. The backend defaults to localhost; `CLIP_ASSASSIN_PORT` and `CLIP_ASSASSIN_HOST` configure its address.

Current implementation and evidence: **`IMPLEMENTATION_REPORT.md`**. The earlier `REVIEW_REPORT.md` records the initial 2.0.3 repair pass; older enhancement/build documents are historical.

Tool sections share glass navigation tabs, including all eight Magic Tools. The **?** beside each tool opens a small local details popup; **User Manual** remains available in the sidebar. Session activity is collapsed under **Jobs & Results**, with job logs and history kept there. Accent colors and interface motion can be changed in Settings.

The in-app **User Manual** is a searchable, task-based field guide covering Resolve setup, every tool group, folder presets and camera/day/card ingest, template installation, integrations, jobs and troubleshooting. Use its section navigation for a topic or search by tool name; expand a guide for the actual steps and cautions.
