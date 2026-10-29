# EditMind AI — Professional AI-Powered Video Editing Workstation

A standalone desktop-quality web application built with a precision dark-themed editing workspace inspired by **DaVinci Resolve 21**. EditMind AI integrates non-destructive multi-track editing, an authentic Media Pool, video viewer with SMPTE frame timecode & vertical stereo audio VU meter, an Inspector panel, persistent SQLite project storage, and an AI Editing Assistant supporting natural-language editing commands.

---

## 🎨 Visual Design & DaVinci Resolve 21 Workflow

The user interface reproduces the clean, matte, subtle aesthetic of professional non-linear editing software (NLE):
- **Monochrome Dark Palette**: Deep matte neutral graphite (`#111215`, `#16171a`, `#1c1d21`, `#212328`) with crisp 1px borders. No artificial neon glows or cartoon bubbly widgets.
- **Top Menu & Sub-toolbar**: DaVinci Resolve file menus (`EditMind AI`, `File`, `Edit`, `Trim`, `Timeline`, `Clip`, `Mark`, `View`, `Playback`, `Help`) with sub-header controls (`Media Pool`, `Sync Bin`, `Transitions`, `Titles`, `Effects`, Project status, `Quick Export`, `Inspector`, `AI Assistant`).
- **Media Pool**: Left workspace panel with Master folder hierarchy, grid/list view toggles, metadata inspection, and authentic empty state (`"No clips in media pool / Add clips from Media Storage to get started"`).
- **Center Video Viewer**: Aspect ratio framing safe guides (9:16 vertical, 16:9 landscape, 1:1 square), top-right SMPTE timecode (`00:00:00:00`), live stereo audio level VU meter (`0` to `-50 dB`), and frame-accurate transport controls (`|<`, `< Step 1 Frame`, `Play/Pause`, `> Step 1 Frame`, `>|`, `Loop`, `TCG`).
- **Right Panel (Inspector & AI Assistant)**:
  - **Inspector**: Selected clip properties, source/timeline in-out points, duration, transform playback speed (0.25x - 3.0x), and detected scene transitions.
  - **AI Assistant**: Natural-language editing chat with **Proposed Edit Action Cards** allowing users to inspect and apply edits to the timeline.
- **Bottom Multi-Track Timeline**:
  - Upper mini-overview strip with boundary indicators.
  - Tool buttons: Selection arrow, Blade (split) tool, Ripple delete, Undo/Redo.
  - Track headers: `V1` (Video), `A1` (Audio), `Sub1` (Subtitles) with Lock, Mute, and Solo.
  - Sleek matte clip blocks, time ruler, and red/amber vertical playhead needle.
- **Bottom Workspace Page Bar**: DaVinci Resolve page icons (`Media`, `Cut`, `Edit` with active red tab indicator, `Fusion`, `Color`, `Fairlight`, `Deliver`).

---

## 🏗️ Architecture & Technology Stack

- **Frontend**: React 19, TypeScript/Vite, Tailwind CSS, Lucide icons, HTML5 video player with timeline synchronization.
- **Backend**: Python 3.14 / 3.11+, FastAPI, Pydantic, FFmpeg & FFprobe (via bundled `imageio-ffmpeg`).
- **Persistence**: Built-in SQLite database (`editmind.db`) with tables for `projects`, `media_assets`, `timeline_clips`, `subtitles`, and `edit_history`.
- **AI & Analysis Engine**:
  - Local Ollama LLM adapter (`http://localhost:11434`) with automatic fallback to deterministic rule-based NLP parser.
  - PySceneDetect & OpenCV for scene boundary detection, brightness calculation, and visual motion scoring.
  - SpeechRecognition for speech transcription with start/end timestamps.
  - FFmpeg silencedetect for audio pause analysis.
- **Export Engine**: Real FFmpeg rendering pipeline supporting 16:9 Landscape, 9:16 Vertical (Center Crop or Fit/Letterbox), and 1:1 Square MP4 outputs with audio preservation and subtitle burn-in.

---

## 🎬 Native DaVinci Resolve 21 Integrated AI Chatbot

EditMind AI provides a direct integration for **Blackmagic DaVinci Resolve 21**, embedding an AI-powered conversational chatbot directly inside the official DaVinci Resolve workstation.

### In-App DaVinci Resolve Chatbot (Native Window)
The script uses DaVinci Resolve's native `fusion.UIManager` and `bmd.UIDispatcher`, rendering a dark-themed AI co-pilot window directly inside the application:
1. Open **DaVinci Resolve 21**.
2. Open or create any project.
3. In the top application menu bar, navigate to:
   ```
   Workspace -> Scripts -> EditAI_Chatbot
   ```
4. The **EditAI Assistant** window opens instantly inside DaVinci Resolve with a live project status bar, quick action buttons, execution transcript, and prompt input box.

### One-Click Desktop Companion
You can also launch the floating desktop chatbot that connects to DaVinci Resolve over the local scripting IPC:
- Simply run:
  ```cmd
  start_davinci_chatbot.bat
  ```
  *(Or run `python davinci_integration/EditAI_Desktop_Chatbot.py`)*

### Supported Natural Language Commands inside DaVinci Resolve
- **Workspace Page Switching**:
  - *"Switch to edit page"*, *"Go to color grading"*, *"Open cut page"*, *"Switch to deliver"*
- **Media Ingestion & Bins**:
  - *"Import media C:/videos/interview.mp4"*, *"Import media into bin B-Roll"*, *"Create bin Music"*
  - *"List all clips in media pool"*
- **Timeline Creation & Sequencing**:
  - *"Create a new timeline called Final Cut"*, *"Create timeline from clips"*, *"Add all clips to timeline"*
  - *"Duplicate timeline as Version 2"*, *"Switch to timeline 1"*
- **Timecode & Playhead Navigation**:
  - *"Go to timecode 01:00:15:00"*, *"Seek to 10 seconds"*, *"Jump to beginning"*, *"Jump to end"*, *"Where is playhead"*
- **Markers & Annotations**:
  - *"Add a blue marker called Cut Here"*, *"Add red marker"*, *"Delete all markers"*
- **Track Controls**:
  - *"Add video track"*, *"Add audio track"*, *"Mute audio track 2"*, *"Lock video track 1"*
- **Clip Color Labeling**:
  - *"Color selected clip green"*, *"Label clip cyan"*
- **DaVinci 21 AI Suite**:
  - *"Enable voice isolation on audio track 1"* (DaVinci Neural Engine)
  - *"Auto generate subtitles from audio"* (Automatic speech captions)
  - *"Detect scene cuts"* (Timeline scene detection)
- **Titles & Generators**:
  - *"Insert title Introduction"*, *"Insert fusion composition"*
- **Save & Render**:
  - *"Save project"*, *"Export timeline to C:/exports/final.mp4"*, *"Start rendering"*

---

## 🚀 Setup & Execution Instructions

### Prerequisites
- Python 3.10+ (tested with Python 3.14)
- Node.js 18+ and npm (tested with Node v22.14.0)
- FFmpeg is bundled automatically via `imageio-ffmpeg` — no separate system installation required.

---

### Step 1: Virtual Environment Setup

#### On Windows (PowerShell):
```powershell
cd d:\Ryathon
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### On Windows (Command Prompt):
```cmd
cd d:\Ryathon
python -m venv .venv
.venv\Scripts\activate.bat
```

#### On macOS / Linux:
```bash
cd d:\Ryathon
python3 -m venv .venv
source .venv/bin/activate
```

---

### Step 2: Install Backend Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 3: Launch the Application

Run the application launcher:

```bash
python run_app.py
```
*(Or on Windows, double-click `start.bat`)*

- The launcher verifies/generates sample media assets.
- Starts the FastAPI backend and serves the compiled React application at `http://127.0.0.1:8000`.
- Automatically opens your default web browser to the editing workspace.

*(Optional)* For frontend development with Hot Module Replacement (HMR):
```bash
cd frontend
npm run dev
# Vite dev server runs at http://localhost:5173
```

---

## 🎬 Testing the Workflow (Multi-Video AI Assembly & Timeline Refinement)

### Multi-Video AI Assembly Stage (Cut Page)
1. **Open AI Auto-Assemble**: Click **"AI Auto-Assemble"** in the top toolbar or click the **"Cut"** page icon in the bottom page bar.
2. **Batch Ingest Source Media**: Click **"Load 3-Clip Demo Pack"** (or upload multiple custom video files simultaneously).
   - *Clip 1: Interview & Dialogue (12.0s)* — Keynote speaker monologue.
   - *Clip 2: Dynamic Action B-Roll (10.0s)* — High kinetic movement & transition b-roll.
   - *Clip 3: Scenic Presentation & Outro (10.0s)* — Atmospheric visuals.
3. **Select Narrative Assembly Style**:
   - `Narrative Highlight Reel` (hook dialogue -> action b-roll -> core message -> scenic closure)
   - `Fast-Paced Social Cut` (punchy, high-tempo kinetic cuts)
   - `Interview + B-Roll Assembly` (dialogue anchor with illustrative cutaways)
   - `Chronological Cut` (temporal progression)
4. **Enter Optional Natural-Language Directives**: e.g., *"Emphasize high action b-roll and opening dialogue"*.
5. **Analyze & Assemble Sequence**: Click **"Analyze & Assemble Sequence"**.
   - The AI multimodal analyzer runs OpenCV/PySceneDetect scene detection, motion scoring, audio silence detection, and quality tagging across all clips.
   - The LLM/Heuristic sequence engine constructs an Edit Decision List (EDL) with **explicit editorial rationales** explaining why each cut was selected and what pre-roll/post-roll was trimmed.
   - Generates synchronized timeline subtitles and audio alignment notes.
6. **Mount to Timeline**: Click **"Apply to Timeline & Open Editor"**.
   - The assembled production is mounted directly onto the interactive multi-track timeline as individual editable clips.
7. **Timeline Inspection & Full Refinement**:
   - Click any cut on the timeline to inspect its **Source Filename**, **AI Role**, **Editorial Rationale**, and **Trimmed Reason** in the Inspector.
   - User has complete creative freedom: trim in/out points, split clips (`S` key or blade tool), delete segments (`Delete` key), adjust playback speed (0.25x - 3.0x), adjust volume, or reorder clips.
8. **Natural-Language Chatbot Refinement**:
   - In the **AI Assistant** panel, instruct:
     - *"Select the clip from 00:05 to 00:09."*
     - *"Split at 00:07."*
     - *"Delete the second half of the selected clip."*
     - *"Undo the last edit."*
9. **Multi-Aspect Ratio MP4 Export**:
   - Click **"Quick Export"** (or type *"Export the edited video"* in the AI chat).
   - Select desired aspect ratio:
     - `16:9 Landscape` (1920x1080)
     - `9:16 Vertical` (1080x1920 with Center Crop or Letterbox Fit for TikTok/Reels/Shorts)
     - `1:1 Square` (1080x1080)
   - Toggle subtitle burn-in and audio track mixing.
   - Click **"Render & Download MP4"** to produce the final playable video file.

---

## 🧪 Automated Test Suite

Run the backend test suites to verify full functionality:

```bash
# 1. Multi-clip AI sequence assembly test (pack load, multimodal analysis, EDL assembly, rationales, timeline mount)
python backend/tests/test_assembly.py

# 2. End-to-end workflow test (sample load, analysis, chatbot split, delete, ripple, and FFmpeg MP4 export)
python backend/tests/test_workflow.py

# 3. SQLite persistence test (create project, save clips, reload from DB)
python backend/tests/test_persistence.py
```
