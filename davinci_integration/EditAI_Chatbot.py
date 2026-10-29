#!/usr/bin/env python3
"""
=============================================================================
EditAI Assistant — Integrated DaVinci Resolve AI Chatbot (In-App Script)
=============================================================================
Runs directly inside DaVinci Resolve using the built-in Fusion UIManager.
Available under: Workspace -> Scripts -> EditAI_Chatbot
"""

import sys
import os

# Ensure local modules can be loaded
current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Utility"
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import automation controller & NLP engine
try:
    from davinci_controller import DaVinciController
    from davinci_nlp_engine import DaVinciNLPEngine
except ImportError:
    # Look in d:/Ryathon/davinci_integration
    dev_path = r"D:\Ryathon\davinci_integration"
    if dev_path not in sys.path:
        sys.path.insert(0, dev_path)
    from davinci_controller import DaVinciController
    from davinci_nlp_engine import DaVinciNLPEngine

# Obtain resolve & fusion instances
if 'resolve' not in globals() or not hasattr(resolve, 'GetVersion'):
    try:
        import DaVinciResolveScript as dvr_script
        resolve = dvr_script.scriptapp("Resolve")
    except Exception as e:
        resolve = None

if 'fusion' not in globals() or not fusion:
    if resolve:
        fusion = resolve.Fusion()

if 'bmd' not in globals() or not bmd:
    try:
        import DaVinciResolveScript as bmd
    except Exception:
        pass

# Initialize Controller and NLP Engine
controller = DaVinciController(resolve)
nlp_engine = DaVinciNLPEngine(controller)

# Setup UI Manager
ui = fusion.UIManager
dispatcher = bmd.UIDispatcher(ui)

winID = "com.editai.davinci.integrated_chatbot"

# Check if an instance already exists
existing_win = ui.FindWindow(winID)
if existing_win:
    existing_win.Show()
    existing_win.Raise()
    sys.exit()

# Element IDs
HEADER_ID = "HeaderLabel"
STATUS_ID = "StatusLabel"
HISTORY_ID = "ChatHistory"
INPUT_ID = "UserInput"
SEND_BTN_ID = "SendBtn"
CLEAR_BTN_ID = "ClearBtn"

# Quick Action IDs
PAGE_EDIT_ID = "PageEdit"
PAGE_COLOR_ID = "PageColor"
PAGE_DELIVER_ID = "PageDeliver"
AI_CUTS_ID = "AiCuts"
AI_SUBS_ID = "AiSubs"
AI_VOICE_ID = "AiVoice"
SAVE_ID = "SaveProject"

# Title header HTML styling
header_html = """
<div style="background-color: #1a1e26; padding: 10px; border-radius: 6px; border: 1px solid #2d3748;">
    <h2 style="color: #38bdf8; margin: 0; font-family: 'Segoe UI', sans-serif;">
        EDITMIND AI &bull; DaVinci Resolve Co-Pilot
    </h2>
    <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 11px;">
        Integrated AI Video Editing Chatbot &bull; Natural Language Control Engine
    </p>
</div>
"""

def get_status_text():
    summary = controller.get_project_summary()
    if not summary.get("connected"):
        return "<span style='color: #ef4444;'>&#9679; Resolve Disconnected</span>"
    proj = summary.get("project_name", "No Project Open")
    tl = summary.get("timeline_name", "No Active Timeline")
    tc = summary.get("timeline_timecode", "N/A")
    return (
        f"<span style='color: #22c55e;'>&#9679; Connected</span> &nbsp;|&nbsp; "
        f"<b>Project:</b> <span style='color: #f1f5f9;'>{proj}</span> &nbsp;|&nbsp; "
        f"<b>Timeline:</b> <span style='color: #38bdf8;'>{tl}</span> &nbsp;|&nbsp; "
        f"<b>TC:</b> <span style='color: #fbbf24;'>{tc}</span>"
    )

# Build UI Layout
win = dispatcher.AddWindow({
    'ID': winID,
    'Geometry': [250, 150, 800, 680],
    'WindowTitle': "EditAI Assistant — DaVinci Resolve 21",
},
ui.VGroup({'Spacing': 8, 'Margin': 12}, [
    # Header Banner
    ui.Label({'ID': HEADER_ID, 'Text': header_html, 'Weight': 0}),
    
    # Live Status Bar
    ui.Label({'ID': STATUS_ID, 'Text': get_status_text(), 'Weight': 0}),

    # Quick Action Toolbar
    ui.HGroup({'Weight': 0, 'Spacing': 5}, [
        ui.Label({'Text': "<b>Quick Actions:</b>", 'Weight': 0}),
        ui.Button({'ID': PAGE_EDIT_ID, 'Text': "Edit Page", 'Weight': 0.1}),
        ui.Button({'ID': PAGE_COLOR_ID, 'Text': "Color Page", 'Weight': 0.1}),
        ui.Button({'ID': PAGE_DELIVER_ID, 'Text': "Deliver Page", 'Weight': 0.1}),
        ui.Button({'ID': AI_CUTS_ID, 'Text': "Detect Cuts", 'Weight': 0.1}),
        ui.Button({'ID': AI_SUBS_ID, 'Text': "Auto Subtitles", 'Weight': 0.1}),
        ui.Button({'ID': AI_VOICE_ID, 'Text': "Voice Isolation", 'Weight': 0.1}),
        ui.Button({'ID': SAVE_ID, 'Text': "Save Project", 'Weight': 0.1}),
    ]),

    # Chat Transcript Box
    ui.Label({'Text': "<b>Chat History & Execution Log:</b>", 'Weight': 0}),
    ui.TextEdit({
        'ID': HISTORY_ID,
        'ReadOnly': True,
        'Weight': 1.0,
        'PlaceholderText': "Welcome to EditAI Assistant!\nEnter any natural language command below to control DaVinci Resolve.\nExample: 'Import media sample.mp4', 'Go to 01:00:15:00', 'Create a new timeline called Cut 1'...",
        'Font': ui.Font({'Family': "Consolas", 'PixelSize': 12})
    }),

    # User Input Field
    ui.Label({'Text': "<b>Natural Language Prompt:</b>", 'Weight': 0}),
    ui.LineEdit({
        'ID': INPUT_ID,
        'PlaceholderText': "Type a command (e.g. 'Switch to color page', 'Add blue marker called Cut Here', 'Export timeline')...",
        'Weight': 0,
        'ClearButtonEnabled': True
    }),

    # Command Execution Bar
    ui.HGroup({'Weight': 0, 'Spacing': 6}, [
        ui.Button({'ID': SEND_BTN_ID, 'Text': "Send Command (Enter)", 'Weight': 0.8}),
        ui.Button({'ID': CLEAR_BTN_ID, 'Text': "Clear History", 'Weight': 0.2}),
    ])
]))

# Chat log state
chat_log = []

def append_to_chat(role: str, text: str):
    prefix = "[USER]" if role == "user" else "[EditAI]"
    chat_log.append(f"{prefix} {text}\n")
    history_widget = win.Find(HISTORY_ID)
    if history_widget:
        history_widget.PlainText = "\n".join(chat_log)

def update_status():
    status_widget = win.Find(STATUS_ID)
    if status_widget:
        status_widget.Text = get_status_text()

# Event Handlers
def OnClose(ev):
    dispatcher.ExitLoop()

def OnSend(ev):
    input_widget = win.Find(INPUT_ID)
    prompt = input_widget.Text.strip() if input_widget else ""
    if not prompt:
        return

    # Add user message
    append_to_chat("user", prompt)
    input_widget.Text = ""

    # Execute via NLP engine
    result = nlp_engine.execute_prompt(prompt)
    msg = result.get("message", "Action processed.")
    append_to_chat("assistant", msg)
    update_status()

def OnClear(ev):
    global chat_log
    chat_log = []
    history_widget = win.Find(HISTORY_ID)
    if history_widget:
        history_widget.PlainText = ""

# Quick Action Handlers
def OnPageEdit(ev):
    res = controller.switch_page("edit")
    append_to_chat("assistant", res.get("message", "Switched to Edit."))
    update_status()

def OnPageColor(ev):
    res = controller.switch_page("color")
    append_to_chat("assistant", res.get("message", "Switched to Color."))
    update_status()

def OnPageDeliver(ev):
    res = controller.switch_page("deliver")
    append_to_chat("assistant", res.get("message", "Switched to Deliver."))
    update_status()

def OnAiCuts(ev):
    append_to_chat("user", "Detect scene cuts")
    res = controller.detect_scene_cuts()
    append_to_chat("assistant", res.get("message", res.get("error", "")))
    update_status()

def OnAiSubs(ev):
    append_to_chat("user", "Auto generate subtitles")
    res = controller.create_subtitles_from_audio()
    append_to_chat("assistant", res.get("message", res.get("error", "")))
    update_status()

def OnAiVoice(ev):
    append_to_chat("user", "Enable voice isolation on audio track 1")
    res = controller.enable_voice_isolation(1)
    append_to_chat("assistant", res.get("message", res.get("error", "")))
    update_status()

def OnSaveProject(ev):
    append_to_chat("user", "Save project")
    res = controller.save_project()
    append_to_chat("assistant", res.get("message", res.get("error", "")))
    update_status()

# Connect Event Listeners
win.On[winID].Close = OnClose
win.On[SEND_BTN_ID].Clicked = OnSend
win.On[INPUT_ID].ReturnPressed = OnSend
win.On[CLEAR_BTN_ID].Clicked = OnClear

win.On[PAGE_EDIT_ID].Clicked = OnPageEdit
win.On[PAGE_COLOR_ID].Clicked = OnPageColor
win.On[PAGE_DELIVER_ID].Clicked = OnPageDeliver
win.On[AI_CUTS_ID].Clicked = OnAiCuts
win.On[AI_SUBS_ID].Clicked = OnAiSubs
win.On[AI_VOICE_ID].Clicked = OnAiVoice
win.On[SAVE_ID].Clicked = OnSaveProject

# Show Window & Enter Event Loop
win.Show()
append_to_chat("assistant", "EditAI Assistant is active and connected to DaVinci Resolve.")
append_to_chat("assistant", get_status_text().replace("<b>", "").replace("</b>", "").replace("<span style='color: #22c55e;'>", "").replace("<span style='color: #38bdf8;'>", "").replace("<span style='color: #fbbf24;'>", "").replace("<span style='color: #f1f5f9;'>", "").replace("</span>", "").replace("&nbsp;|&nbsp;", " | "))
dispatcher.StartLoop()
