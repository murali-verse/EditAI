#!/usr/bin/env python3
"""
=============================================================================
EditAI Assistant — Integrated DaVinci Resolve AI Chatbot (In-App Script)
=============================================================================
Runs directly inside DaVinci Resolve using the built-in Fusion UIManager.
Available under: Workspace -> Scripts -> Edit -> EditAI_Chatbot
"""

import sys
import os
import traceback

LOG_FILE = r"D:\Ryathon\davinci_chatbot_last_error.log"

def log_msg(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

try:
    log_msg("--- Launching EditAI_Chatbot.py ---")

    # Add directories to sys.path
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else ""
    dev_dir = r"D:\Ryathon\davinci_integration"
    modules_dir = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"

    for p in [script_dir, dev_dir, modules_dir]:
        if p and p not in sys.path and os.path.exists(p):
            sys.path.insert(0, p)

    # Resolve environment variables for external fallback
    lib_path = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
    if os.path.exists(lib_path):
        os.environ["RESOLVE_SCRIPT_LIB"] = lib_path

    # Obtain bmd module
    if 'bmd' not in globals() or not globals()['bmd']:
        try:
            import DaVinciResolveScript as bmd
        except Exception as e:
            log_msg(f"Could not import DaVinciResolveScript: {e}")
            bmd = None
    else:
        bmd = globals()['bmd']

    # Obtain resolve instance
    if 'resolve' not in globals() or not globals()['resolve']:
        try:
            if bmd:
                resolve = bmd.scriptapp("Resolve")
            else:
                resolve = None
        except Exception as e:
            log_msg(f"Could not get Resolve instance: {e}")
            resolve = None
    else:
        resolve = globals()['resolve']

    # Obtain fusion instance
    if 'fusion' not in globals() or not globals()['fusion']:
        try:
            if resolve:
                fusion = resolve.Fusion()
            elif bmd:
                fusion = bmd.scriptapp("Fusion")
            else:
                fusion = None
        except Exception as e:
            log_msg(f"Could not get Fusion instance: {e}")
            fusion = None
    else:
        fusion = globals()['fusion']

    if not fusion or not bmd:
        err = f"Fatal: fusion={fusion}, bmd={bmd}. Cannot initialize Fusion UIManager."
        log_msg(err)
        print(err)
        sys.exit(1)

    log_msg("Acquired fusion and bmd instances successfully.")

    # Import automation controller & NLP engine
    from davinci_controller import DaVinciController
    from davinci_nlp_engine import DaVinciNLPEngine

    controller = DaVinciController(resolve)
    nlp_engine = DaVinciNLPEngine(controller)

    ui = fusion.UIManager
    dispatcher = bmd.UIDispatcher(ui)

    winID = "com.editai.davinci.integrated_chatbot"

    # Single instance check
    existing_win = ui.FindWindow(winID)
    if existing_win:
        existing_win.Show()
        existing_win.Raise()
        log_msg("Raised existing window instance.")
        sys.exit()

    # Widget IDs
    STATUS_ID = "StatusLabel"
    HISTORY_ID = "ChatHistory"
    INPUT_ID = "PromptInput"
    SEND_BTN_ID = "BtnSend"
    CLEAR_BTN_ID = "BtnClear"

    PAGE_EDIT_ID = "BtnEdit"
    PAGE_COLOR_ID = "BtnColor"
    PAGE_DELIVER_ID = "BtnDeliver"
    AI_CUTS_ID = "BtnCuts"
    AI_SUBS_ID = "BtnSubs"
    AI_VOICE_ID = "BtnVoice"
    SAVE_ID = "BtnSave"

    def get_summary_text():
        try:
            summary = controller.get_project_summary()
            if not summary.get("connected"):
                return "Resolve Status: Disconnected"
            proj = summary.get("project_name", "No Project Open")
            tl = summary.get("timeline_name", "None")
            tc = summary.get("timeline_timecode", "N/A")
            return f"Project: {proj}  |  Timeline: {tl}  |  TC: {tc}"
        except Exception as ex:
            return f"Status: {ex}"

    # Build Layout using standard Fusion UI containers
    header_title = "<b><big>EditAI Assistant &bull; DaVinci Resolve 21 Co-Pilot</big></b>"

    win = dispatcher.AddWindow({
        'ID': winID,
        'Geometry': [200, 150, 720, 620],
        'WindowTitle': "EditAI Assistant — DaVinci Resolve 21",
        },
        ui.VGroup([
            ui.Label({ 'Text': header_title, 'Weight': 0.05 }),
            ui.Label({ 'ID': STATUS_ID, 'Text': get_summary_text(), 'Weight': 0.05 }),
            
            # Quick Actions Row
            ui.HGroup({ 'Weight': 0 }, [
                ui.Button({ 'ID': PAGE_EDIT_ID, 'Text': "Edit Page" }),
                ui.Button({ 'ID': PAGE_COLOR_ID, 'Text': "Color Page" }),
                ui.Button({ 'ID': PAGE_DELIVER_ID, 'Text': "Deliver Page" }),
                ui.Button({ 'ID': AI_CUTS_ID, 'Text': "Detect Cuts" }),
                ui.Button({ 'ID': AI_SUBS_ID, 'Text': "Auto Subtitles" }),
                ui.Button({ 'ID': AI_VOICE_ID, 'Text': "Voice Iso" }),
                ui.Button({ 'ID': SAVE_ID, 'Text': "Save Project" }),
            ]),

            ui.Label({ 'Text': "<b>Chat History & Execution Log:</b>", 'Weight': 0 }),
            ui.TextEdit({
                'ID': HISTORY_ID,
                'ReadOnly': True,
                'Weight': 0.65,
                'Font': ui.Font({ 'Family': "Consolas", 'PixelSize': 12 })
            }),

            ui.Label({ 'Text': "<b>Enter Natural Language Command:</b>", 'Weight': 0 }),
            ui.TextEdit({
                'ID': INPUT_ID,
                'Weight': 0.2,
                'Font': ui.Font({ 'Family': "Consolas", 'PixelSize': 12 })
            }),

            ui.HGroup({ 'Weight': 0 }, [
                ui.Button({ 'ID': SEND_BTN_ID, 'Text': "Execute Command (Send)" }),
                ui.Button({ 'ID': CLEAR_BTN_ID, 'Text': "Clear Log" }),
            ])
        ])
    )

    log_msg("Window created successfully.")

    # Chat history state
    chat_entries = [
        "[EditAI] Welcome to EditAI Assistant inside DaVinci Resolve 21!",
        "[EditAI] " + get_summary_text(),
        "[EditAI] Type commands below (e.g. 'Go to 01:00:15:00', 'Add blue marker called Cut Here', 'Export to C:/video.mp4') and click Execute."
    ]

    def refresh_display():
        h = win.Find(HISTORY_ID)
        if h:
            h.PlainText = "\n\n".join(chat_entries)
        s = win.Find(STATUS_ID)
        if s:
            s.Text = get_summary_text()

    # Event handlers
    def OnClose(ev):
        dispatcher.ExitLoop()

    def OnSend(ev):
        try:
            inp = win.Find(INPUT_ID)
            prompt = inp.PlainText.strip() if inp else ""
            if not prompt:
                return
            
            chat_entries.append(f"[USER] {prompt}")
            inp.PlainText = ""
            refresh_display()

            # Execute
            res = nlp_engine.execute_prompt(prompt)
            msg = res.get("message") or res.get("error", "Action processed.")
            chat_entries.append(f"[EditAI] {msg}")
            refresh_display()
        except Exception as e:
            log_msg(f"Error in OnSend: {traceback.format_exc()}")
            chat_entries.append(f"[EditAI Error] {e}")
            refresh_display()

    def OnClear(ev):
        global chat_entries
        chat_entries = ["[EditAI] Log cleared."]
        refresh_display()

    def make_action_handler(action_name, params=None):
        def handler(ev):
            try:
                res = nlp_engine._dispatch_action(action_name, params or {})
                msg = res.get("message") or res.get("error", "Executed.")
                chat_entries.append(f"[EditAI] {msg}")
                refresh_display()
            except Exception as e:
                log_msg(f"Error in quick action {action_name}: {traceback.format_exc()}")
        return handler

    # Bind events
    win.On[winID].Close = OnClose
    win.On[SEND_BTN_ID].Clicked = OnSend
    win.On[CLEAR_BTN_ID].Clicked = OnClear

    win.On[PAGE_EDIT_ID].Clicked = make_action_handler("switch_page", {"page": "edit"})
    win.On[PAGE_COLOR_ID].Clicked = make_action_handler("switch_page", {"page": "color"})
    win.On[PAGE_DELIVER_ID].Clicked = make_action_handler("switch_page", {"page": "deliver"})
    win.On[AI_CUTS_ID].Clicked = make_action_handler("detect_scene_cuts", {})
    win.On[AI_SUBS_ID].Clicked = make_action_handler("create_subtitles_from_audio", {})
    win.On[AI_VOICE_ID].Clicked = make_action_handler("enable_voice_isolation", {"track_index": 1})
    win.On[SAVE_ID].Clicked = make_action_handler("save_project", {})

    # Initial view
    refresh_display()
    win.Show()
    log_msg("Calling dispatcher.RunLoop()")
    dispatcher.RunLoop()
    log_msg("Exited dispatcher.RunLoop()")

except Exception as fatal_e:
    log_msg(f"FATAL EXCEPTION: {traceback.format_exc()}")
    print(f"EditAI Fatal Exception: {traceback.format_exc()}")
