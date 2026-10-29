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

## 🎬 Testing the Workflow (9-Step Demonstration)

1. **Import Media**: Click **"Load Demo Sample"** in the top bar (or drag and drop your video file into the Media Pool). A 30s multi-scene video with subtitles is loaded.
2. **Analyze Video**: Click **"Analyze"** in the top toolbar. The analysis engine detects scene boundaries, audio silences, and visual motion.
3. **Select Clip Range**: In the **AI Assistant** panel, enter:
   ```text
   Select the clip from 00:10 to 00:25.
   ```
   *The timeline highlights the 10s–25s range.*
4. **Split Clip**: In the AI Assistant, enter:
   ```text
   Split at 00:18.
   ```
   *The clip splits into two independent clips at 18.00s.*
5. **Delete Segment**: In the AI Assistant, enter:
   ```text
   Delete the selected segment.
   ```
   *The segment is removed, following clips ripple forward, and timeline duration updates to 15.00s.*
6. **Preview Updated Video**: Press **Spacebar** or click **Play**. The player previews the edited sequence according to the updated EDL timeline.
7. **Subtitle Synchronization**: Subtitles adjust automatically after the cut. Subtitles in the deleted range are removed, and subsequent subtitles shift forward.
8. **Export Edited Video**: In the AI Assistant, enter `Export the edited video.` (or click **"Quick Export"** in the top bar). Choose your aspect ratio (16:9, 9:16 vertical, or 1:1 square) and click **Export**. Download the resulting MP4.
9. **Project Persistence**: Click **Save** in the top bar or let autosave run. Open the **Project Manager** to see your project stored in SQLite.

---

## 🧪 Automated Test Suite

Run the backend test suites to verify full functionality:

```bash
# 1. End-to-end workflow test (sample load, analysis, chatbot split, delete, ripple, and FFmpeg MP4 export)
python backend/tests/test_workflow.py

# 2. SQLite persistence test (create project, save clips, reload from DB)
python backend/tests/test_persistence.py
```
