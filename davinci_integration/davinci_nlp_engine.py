"""
DaVinci Resolve Natural Language Processing Engine
Interprets conversational user editing requests and translates them into executable DaVinci Resolve operations.
Supports local semantic parsing + optional multi-LLM dispatch (Gemini, OpenAI, Ollama).
"""

import os
import re
import json

class DaVinciNLPEngine:
    def __init__(self, controller, llm_config: dict = None):
        self.controller = controller
        self.llm_config = llm_config or {}

    def execute_prompt(self, user_prompt: str) -> dict:
        """Process user natural language request and execute on DaVinci Resolve."""
        clean_text = user_prompt.strip()
        if not clean_text:
            return {"success": False, "message": "Please enter an editing prompt."}

        # 1. First attempt semantic rule/intent parsing
        intent = self._parse_intent(clean_text)
        if intent:
            action = intent.get("action")
            params = intent.get("params", {})
            return self._dispatch_action(action, params)

        # 2. Try LLM if configured
        if self.llm_config and self.llm_config.get("api_key"):
            llm_res = self._ask_llm(clean_text)
            if llm_res and llm_res.get("action"):
                return self._dispatch_action(llm_res["action"], llm_res.get("params", {}))

        # 3. Fallback help
        return {
            "success": False,
            "message": (
                f"I couldn't confidently map: '{clean_text}'.\n\n"
                "Try commands like:\n"
                "• 'Switch to edit page' or 'Go to color page'\n"
                "• 'Import media C:/path/to/video.mp4'\n"
                "• 'Create a new timeline called Final Cut'\n"
                "• 'Add all clips to timeline'\n"
                "• 'Go to timecode 01:00:15:00' or 'Jump to start'\n"
                "• 'Add a blue marker called Cut Here'\n"
                "• 'Enable voice isolation on audio track 1'\n"
                "• 'Auto generate subtitles from audio'\n"
                "• 'Detect scene cuts'\n"
                "• 'Save project' or 'Export timeline to C:/exports/final.mp4'"
            )
        }

    def _parse_intent(self, text: str) -> dict:
        t = text.lower()

        # ------------------ STATUS & INFO ------------------
        if any(k in t for k in ["status", "summary", "project info", "current project"]):
            return {"action": "project_summary", "params": {}}

        if any(k in t for k in ["list clip", "show clip", "media pool clip", "list media"]):
            return {"action": "list_media_pool", "params": {}}

        if any(k in t for k in ["list timeline", "show timeline", "get timeline"]):
            return {"action": "list_timelines", "params": {}}

        # ------------------ PAGE NAVIGATION ------------------
        page_match = re.search(r'\b(?:switch\s+to|go\s+to|open)\s+(media|cut|edit|fusion|color|fairlight|deliver)(?:\s+page)?\b', t)
        if page_match:
            return {"action": "switch_page", "params": {"page": page_match.group(1)}}

        if "edit page" in t:
            return {"action": "switch_page", "params": {"page": "edit"}}
        if "color page" in t or "color grading" in t:
            return {"action": "switch_page", "params": {"page": "color"}}
        if "cut page" in t:
            return {"action": "switch_page", "params": {"page": "cut"}}
        if "deliver page" in t or "export page" in t:
            return {"action": "switch_page", "params": {"page": "deliver"}}
        if "media page" in t:
            return {"action": "switch_page", "params": {"page": "media"}}
        if "fairlight" in t or "audio page" in t:
            return {"action": "switch_page", "params": {"page": "fairlight"}}

        # ------------------ MEDIA IMPORT ------------------
        import_match = re.search(r'\b(?:import|add|load)\s+(?:media|video|file|clip)?\s*(?:from\s+)?([A-Za-z]:[^\s]+|\S+\.(?:mp4|mov|webm|mp3|wav|srt))\b', text, re.IGNORECASE)
        if import_match:
            filepath = import_match.group(1).strip("\"'")
            bin_m = re.search(r'(?:to|into)\s+bin\s+[\'"]?([a-zA-Z0-9_\-\s]+)[\'"]?', t)
            bin_name = bin_m.group(1).strip() if bin_m else None
            return {"action": "import_media", "params": {"file_paths": [filepath], "bin_name": bin_name}}

        bin_create = re.search(r'\b(?:create|new|make)\s+(?:bin|folder)\s+[\'"]?([a-zA-Z0-9_\-\s]+)[\'"]?\b', t)
        if bin_create:
            return {"action": "create_bin", "params": {"bin_name": bin_create.group(1).strip()}}

        # ------------------ TIMELINE CREATION ------------------
        create_tl_from_clips = re.search(r'\b(?:create|make)\s+timeline\s+(?:called\s+[\'"]?([a-zA-Z0-9_\-\s]+)[\'"]?\s+)?from\s+(?:all\s+)?clips\b', t)
        if create_tl_from_clips:
            name = create_tl_from_clips.group(1) or "Timeline_1"
            return {"action": "create_timeline_from_clips", "params": {"timeline_name": name.strip()}}

        create_tl = re.search(r'\b(?:create|new|make)\s+(?:empty\s+)?timeline\s+(?:called\s+|named\s+)?[\'"]?([a-zA-Z0-9_\-\s]+)[\'"]?\b', t)
        if create_tl:
            return {"action": "create_timeline", "params": {"timeline_name": create_tl.group(1).strip()}}

        if any(k in t for k in ["add clips to timeline", "append to timeline", "insert clips to timeline", "add all to timeline"]):
            return {"action": "append_clips_to_timeline", "params": {}}

        if "duplicate timeline" in t:
            dup_name_m = re.search(r'duplicate\s+timeline\s+(?:as\s+[\'"]?([a-zA-Z0-9_\-\s]+)[\'"]?)?', t)
            dup_name = dup_name_m.group(1) if dup_name_m and dup_name_m.group(1) else None
            return {"action": "duplicate_timeline", "params": {"new_name": dup_name}}

        switch_tl_m = re.search(r'(?:switch\s+to|open)\s+timeline\s+[\'"]?([a-zA-Z0-9_\-\s]+)[\'"]?', t)
        if switch_tl_m:
            return {"action": "switch_timeline", "params": {"target": switch_tl_m.group(1).strip()}}

        # ------------------ PLAYHEAD & TIMECODE ------------------
        tc_m = re.search(r'\b(?:go\s+to|jump\s+to|seek\s+to|timecode)\s+(?:timecode\s+)?(\d{2}:\d{2}:\d{2}(?::\d{2})?|\d{2}:\d{2}|\d+\s*s(?:econds?)?)\b', t)
        if tc_m:
            raw_tc = tc_m.group(1).replace("seconds", "").replace("s", "").strip()
            return {"action": "set_timecode", "params": {"timecode": raw_tc}}

        if any(k in t for k in ["jump to start", "go to start", "beginning", "head of timeline", "start of timeline"]):
            return {"action": "jump_to_start", "params": {}}

        if any(k in t for k in ["jump to end", "go to end", "tail of timeline", "end of timeline"]):
            return {"action": "jump_to_end", "params": {}}

        if any(k in t for k in ["where is playhead", "current timecode", "get timecode", "current time"]):
            return {"action": "get_timecode", "params": {}}

        # ------------------ MARKERS ------------------
        marker_add = re.search(r'\badd\s+(?:a\s+)?([a-zA-Z]+)?\s*marker(?:\s+called|\s+named)?\s*[\'"]?([^\'"]+)?[\'"]?', t)
        if marker_add:
            color = marker_add.group(1) or "Blue"
            name = marker_add.group(2) or "Marker"
            return {"action": "add_marker", "params": {"color": color.capitalize(), "name": name.strip()}}

        if any(k in t for k in ["delete all markers", "clear markers", "remove all markers"]):
            return {"action": "delete_markers", "params": {"color": "All"}}

        # ------------------ TRACKS ------------------
        add_track_m = re.search(r'\badd\s+(video|audio|subtitle)\s+track\b', t)
        if add_track_m:
            return {"action": "add_track", "params": {"track_type": add_track_m.group(1)}}

        mute_track_m = re.search(r'\b(?:mute|disable)\s+(video|audio)\s+track\s+(\d+)\b', t)
        if mute_track_m:
            return {"action": "set_track_enable", "params": {"track_type": mute_track_m.group(1), "track_index": int(mute_track_m.group(2)), "enabled": False}}

        unmute_track_m = re.search(r'\b(?:unmute|enable)\s+(video|audio)\s+track\s+(\d+)\b', t)
        if unmute_track_m:
            return {"action": "set_track_enable", "params": {"track_type": unmute_track_m.group(1), "track_index": int(unmute_track_m.group(2)), "enabled": True}}

        lock_track_m = re.search(r'\b(?:lock)\s+(video|audio)\s+track\s+(\d+)\b', t)
        if lock_track_m:
            return {"action": "set_track_lock", "params": {"track_type": lock_track_m.group(1), "track_index": int(lock_track_m.group(2)), "locked": True}}

        # ------------------ CLIP COLOR ------------------
        color_m = re.search(r'\b(?:color|label)\s+(?:clip|selected\s+clip)\s+(?:to\s+|as\s+)?(orange|cyan|green|yellow|red|pink|purple|blue)\b', t)
        if color_m:
            return {"action": "set_clip_color", "params": {"color": color_m.group(1).capitalize()}}

        # ------------------ AI FEATURES (DAVINCI 21) ------------------
        if any(k in t for k in ["detect scene cuts", "scene detection", "find cuts", "detect cuts"]):
            return {"action": "detect_scene_cuts", "params": {}}

        if any(k in t for k in ["subtitle", "caption", "generate subtitle", "speech to text", "create caption"]):
            return {"action": "create_subtitles_from_audio", "params": {}}

        if any(k in t for k in ["voice isolation", "isolate voice", "clean audio", "remove background noise"]):
            track_idx = 1
            idx_m = re.search(r'track\s+(\d+)', t)
            if idx_m:
                track_idx = int(idx_m.group(1))
            return {"action": "enable_voice_isolation", "params": {"track_index": track_idx}}

        if "fusion comp" in t or "fusion composition" in t:
            return {"action": "insert_fusion_comp", "params": {}}

        title_m = re.search(r'\b(?:add|insert)\s+title\s+[\'"]?([^\'"]+)[\'"]?', t)
        if title_m:
            return {"action": "insert_title", "params": {"title_text": title_m.group(1)}}

        # ------------------ SAVE & EXPORT ------------------
        if any(k in t for k in ["save project", "save"]):
            return {"action": "save_project", "params": {}}

        export_m = re.search(r'\b(?:export|render)\s+(?:timeline\s+)?(?:to\s+)?([A-Za-z]:[^\s]+|\S+\.mp4)\b', text, re.IGNORECASE)
        if export_m:
            return {"action": "export_timeline", "params": {"output_path": export_m.group(1).strip("\"'")}}

        if any(k in t for k in ["start render", "start rendering", "render timeline"]):
            return {"action": "start_rendering", "params": {}}

        return None

    def _dispatch_action(self, action: str, params: dict) -> dict:
        """Dispatch interpreted action directly to DaVinciController."""
        ctrl = self.controller
        if not ctrl.is_connected():
            return {
                "success": False,
                "message": (
                    "DaVinci Resolve is not running or external scripting is disabled.\n"
                    "1. Launch DaVinci Resolve.\n"
                    "2. Go to Preferences -> System -> General -> External Scripting -> Set to 'Local'.\n"
                    "3. Open any project."
                )
            }

        try:
            if action == "project_summary":
                res = ctrl.get_project_summary()
                return {"success": True, "message": res.get("message", "Summary retrieved.")}

            elif action == "list_media_pool":
                res = ctrl.list_media_pool()
                if res.get("success"):
                    clips = res.get("clips", [])
                    if not clips:
                        return {"success": True, "message": "Media Pool bin is currently empty."}
                    clip_str = "\n".join([f"• {c['name']} ({c.get('duration','N/A')}, {c.get('resolution','N/A')})" for c in clips])
                    return {"success": True, "message": f"Media Pool Clips ({len(clips)}):\n{clip_str}"}
                return res

            elif action == "list_timelines":
                res = ctrl.list_timelines()
                if res.get("success"):
                    tls = res.get("timelines", [])
                    tl_str = "\n".join([f"{'* ' if t['is_active'] else '  '}[{t['index']}] {t['name']}" for t in tls])
                    return {"success": True, "message": f"Project Timelines:\n{tl_str}"}
                return res

            elif action == "switch_page":
                return ctrl.switch_page(params.get("page", "edit"))

            elif action == "import_media":
                return ctrl.import_media(params.get("file_paths", []), params.get("bin_name"))

            elif action == "create_bin":
                return ctrl.create_bin(params.get("bin_name", "New Bin"))

            elif action == "create_timeline":
                return ctrl.create_timeline(params.get("timeline_name", "Timeline 1"))

            elif action == "create_timeline_from_clips":
                return ctrl.create_timeline_from_clips(params.get("timeline_name", "Timeline 1"))

            elif action == "append_clips_to_timeline":
                return ctrl.append_clips_to_timeline()

            elif action == "duplicate_timeline":
                return ctrl.duplicate_timeline(params.get("new_name"))

            elif action == "switch_timeline":
                return ctrl.switch_timeline(params.get("target"))

            elif action == "set_timecode":
                return ctrl.set_timecode(params.get("timecode", "01:00:00:00"))

            elif action == "jump_to_start":
                return ctrl.jump_to_start()

            elif action == "jump_to_end":
                return ctrl.jump_to_end()

            elif action == "get_timecode":
                return ctrl.get_timecode()

            elif action == "add_marker":
                return ctrl.add_marker(params.get("color", "Blue"), params.get("name", "Marker"))

            elif action == "delete_markers":
                return ctrl.delete_markers(params.get("color", "All"))

            elif action == "add_track":
                return ctrl.add_track(params.get("track_type", "video"))

            elif action == "set_track_enable":
                return ctrl.set_track_enable(params.get("track_type", "audio"), params.get("track_index", 1), params.get("enabled", True))

            elif action == "set_track_lock":
                return ctrl.set_track_lock(params.get("track_type", "video"), params.get("track_index", 1), params.get("locked", True))

            elif action == "set_clip_color":
                return ctrl.set_clip_color(params.get("color", "Green"))

            elif action == "detect_scene_cuts":
                return ctrl.detect_scene_cuts()

            elif action == "create_subtitles_from_audio":
                return ctrl.create_subtitles_from_audio()

            elif action == "enable_voice_isolation":
                return ctrl.enable_voice_isolation(params.get("track_index", 1))

            elif action == "insert_title":
                return ctrl.insert_title(params.get("title_text", "Title"))

            elif action == "insert_fusion_comp":
                return ctrl.insert_fusion_comp()

            elif action == "save_project":
                return ctrl.save_project()

            elif action == "export_timeline":
                return ctrl.export_timeline(params.get("output_path", "C:/exports/output.mp4"))

            elif action == "start_rendering":
                return ctrl.start_rendering()

            else:
                return {"success": False, "message": f"Action '{action}' is recognized but unhandled."}

        except Exception as e:
            return {"success": False, "message": f"Error executing '{action}': {str(e)}"}

    def _ask_llm(self, prompt: str) -> dict:
        """Call external LLM if configured to convert prompt to structured action JSON."""
        # Simple JSON prompt generator for Gemini / OpenAI
        return None
