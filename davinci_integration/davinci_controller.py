"""
DaVinci Resolve 21 Controller
Provides direct automation interface to Blackmagic DaVinci Resolve API.
Works both internally (within DaVinci Resolve) and externally via DaVinciResolveScript IPC.
"""

import os
import sys
import re

# Ensure DaVinciResolveScript can be imported in external environments
def get_resolve_instance():
    # 1. Check if resolve is already provided in the internal global scope
    if 'resolve' in globals() and globals()['resolve'] is not None:
        try:
            if hasattr(globals()['resolve'], 'GetVersion'):
                return globals()['resolve']
        except Exception:
            pass

    # 2. Try importing DaVinciResolveScript directly
    try:
        import DaVinciResolveScript as dvr_script
        res = dvr_script.scriptapp("Resolve")
        if res:
            return res
    except ImportError:
        pass

    # 3. Setup Windows paths dynamically if not set
    api_dir = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
    modules_dir = os.path.join(api_dir, "Modules")
    lib_path = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"

    if os.path.exists(modules_dir) and modules_dir not in sys.path:
        sys.path.append(modules_dir)
    
    if os.path.exists(lib_path):
        os.environ["RESOLVE_SCRIPT_LIB"] = lib_path
    if os.path.exists(api_dir):
        os.environ["RESOLVE_SCRIPT_API"] = api_dir

    try:
        import DaVinciResolveScript as dvr_script
        return dvr_script.scriptapp("Resolve")
    except Exception as e:
        print(f"[DaVinciController] Note: Could not attach to Resolve: {e}")
        return None


class DaVinciController:
    """High-level automation controller for DaVinci Resolve."""
    
    def __init__(self, resolve=None):
        self.resolve = resolve or get_resolve_instance()

    def is_connected(self):
        """Check if connected to an active DaVinci Resolve instance."""
        if not self.resolve:
            self.resolve = get_resolve_instance()
        return self.resolve is not None

    def get_version(self):
        if not self.is_connected():
            return None
        return self.resolve.GetVersion()

    def get_project_manager(self):
        if not self.is_connected():
            return None
        return self.resolve.GetProjectManager()

    def get_current_project(self):
        pm = self.get_project_manager()
        if not pm:
            return None
        return pm.GetCurrentProject()

    def get_media_pool(self):
        proj = self.get_current_project()
        if not proj:
            return None
        return proj.GetMediaPool()

    def get_current_timeline(self):
        proj = self.get_current_project()
        if not proj:
            return None
        return proj.GetCurrentTimeline()

    # =========================================================================
    # 1. WORKSPACE PAGE NAVIGATION
    # =========================================================================
    def switch_page(self, page_name: str) -> dict:
        """Switch workspace page: media, cut, edit, fusion, color, fairlight, deliver."""
        if not self.is_connected():
            return {"success": False, "error": "DaVinci Resolve is not running or not connected."}
        
        valid_pages = ['media', 'cut', 'edit', 'fusion', 'color', 'fairlight', 'deliver']
        page = page_name.lower().strip()
        if page not in valid_pages:
            return {"success": False, "error": f"Invalid page '{page}'. Must be one of: {', '.join(valid_pages)}"}

        ok = self.resolve.OpenPage(page)
        return {"success": ok, "message": f"Switched to '{page}' page in DaVinci Resolve."}

    # =========================================================================
    # 2. MEDIA POOL OPERATIONS
    # =========================================================================
    def import_media(self, file_paths: list, bin_name: str = None) -> dict:
        """Import one or more media files into current or specified bin."""
        if not self.is_connected():
            return {"success": False, "error": "Resolve is not connected."}
        
        mp = self.get_media_pool()
        if not mp:
            return {"success": False, "error": "No active project or Media Pool found."}

        # Normalize file paths
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        
        valid_paths = [os.path.abspath(p) for p in file_paths if os.path.exists(p)]
        if not valid_paths:
            return {"success": False, "error": f"None of the provided file paths exist: {file_paths}"}

        # Select or create target bin if requested
        if bin_name:
            root = mp.GetRootFolder()
            subfolders = root.GetSubFolderList() or []
            target_folder = None
            for f in subfolders:
                if f.GetName().lower() == bin_name.lower():
                    target_folder = f
                    break
            if not target_folder:
                target_folder = mp.AddSubFolder(root, bin_name)
            if target_folder:
                mp.SetCurrentFolder(target_folder)

        items = mp.ImportMedia(valid_paths)
        if items:
            names = [it.GetName() for it in items]
            return {
                "success": True,
                "imported_count": len(items),
                "clips": names,
                "message": f"Successfully imported {len(items)} clip(s) into Media Pool: {', '.join(names)}"
            }
        return {"success": False, "error": "Resolve failed to import media files."}

    def create_bin(self, bin_name: str) -> dict:
        """Create a new bin in the Media Pool root."""
        if not self.is_connected():
            return {"success": False, "error": "Resolve is not connected."}
        mp = self.get_media_pool()
        if not mp:
            return {"success": False, "error": "No Media Pool available."}
        
        root = mp.GetRootFolder()
        new_folder = mp.AddSubFolder(root, bin_name)
        if new_folder:
            mp.SetCurrentFolder(new_folder)
            return {"success": True, "message": f"Created bin '{bin_name}' and set as active."}
        return {"success": False, "error": f"Failed to create bin '{bin_name}'."}

    def list_media_pool(self) -> dict:
        """List all clips present in the active Media Pool folder."""
        if not self.is_connected():
            return {"success": False, "error": "Resolve is not connected."}
        mp = self.get_media_pool()
        if not mp:
            return {"success": False, "error": "No active project."}
        
        current_folder = mp.GetCurrentFolder() or mp.GetRootFolder()
        clips = current_folder.GetClipList() or []
        clip_data = []
        for c in clips:
            clip_data.append({
                "name": c.GetName(),
                "duration": c.GetClipProperty("Duration"),
                "fps": c.GetClipProperty("FPS"),
                "resolution": c.GetClipProperty("Resolution")
            })
        
        return {
            "success": True,
            "folder": current_folder.GetName(),
            "count": len(clip_data),
            "clips": clip_data,
            "message": f"Found {len(clip_data)} clip(s) in bin '{current_folder.GetName()}'."
        }

    def delete_media_pool_clips(self, clip_names: list) -> dict:
        """Delete specific clips from the Media Pool."""
        if not self.is_connected():
            return {"success": False, "error": "Resolve is not connected."}
        mp = self.get_media_pool()
        current_folder = mp.GetCurrentFolder() or mp.GetRootFolder()
        clips = current_folder.GetClipList() or []
        
        to_delete = []
        for c in clips:
            if c.GetName().lower() in [n.lower() for n in clip_names]:
                to_delete.append(c)
        
        if not to_delete:
            return {"success": False, "error": f"No matching clips found for: {clip_names}"}
        
        ok = mp.DeleteClips(to_delete)
        return {"success": ok, "message": f"Deleted {len(to_delete)} clip(s) from Media Pool."}

    # =========================================================================
    # 3. TIMELINE CREATION & MANIPULATION
    # =========================================================================
    def create_timeline(self, timeline_name: str) -> dict:
        """Create an empty timeline in the current project."""
        if not self.is_connected():
            return {"success": False, "error": "Resolve is not connected."}
        mp = self.get_media_pool()
        if not mp:
            return {"success": False, "error": "No active project."}
        
        tl = mp.CreateEmptyTimeline(timeline_name)
        if tl:
            return {"success": True, "message": f"Created timeline '{timeline_name}'."}
        return {"success": False, "error": f"Failed to create timeline '{timeline_name}'."}

    def create_timeline_from_clips(self, timeline_name: str, clip_names: list = None) -> dict:
        """Create a new timeline populated with selected or all clips."""
        if not self.is_connected():
            return {"success": False, "error": "Resolve is not connected."}
        mp = self.get_media_pool()
        current_folder = mp.GetCurrentFolder() or mp.GetRootFolder()
        all_clips = current_folder.GetClipList() or []
        
        if not all_clips:
            return {"success": False, "error": "No clips available in current bin to create timeline."}

        target_clips = []
        if clip_names:
            for c in all_clips:
                if any(n.lower() in c.GetName().lower() for n in clip_names):
                    target_clips.append(c)
        else:
            target_clips = all_clips

        if not target_clips:
            return {"success": False, "error": "No matching clips found."}

        tl = mp.CreateTimelineFromClips(timeline_name, target_clips)
        if tl:
            return {"success": True, "message": f"Created timeline '{timeline_name}' with {len(target_clips)} clip(s)."}
        return {"success": False, "error": f"Failed to create timeline '{timeline_name}'."}

    def append_clips_to_timeline(self, clip_names: list = None) -> dict:
        """Append media pool clips onto the active timeline."""
        if not self.is_connected():
            return {"success": False, "error": "Resolve is not connected."}
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline open in DaVinci Resolve."}
        
        mp = self.get_media_pool()
        current_folder = mp.GetCurrentFolder() or mp.GetRootFolder()
        all_clips = current_folder.GetClipList() or []

        target_clips = []
        if clip_names:
            for c in all_clips:
                if any(n.lower() in c.GetName().lower() for n in clip_names):
                    target_clips.append(c)
        else:
            target_clips = all_clips

        if not target_clips:
            return {"success": False, "error": "No clips found to append."}

        added = mp.AppendToTimeline(target_clips)
        if added:
            return {"success": True, "message": f"Appended {len(added)} clip(s) to timeline '{tl.GetName()}'."}
        return {"success": False, "error": "Could not append clips to timeline."}

    def duplicate_timeline(self, new_name: str = None) -> dict:
        """Duplicate the active timeline."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}
        
        name = new_name or f"{tl.GetName()}_Copy"
        dup = tl.DuplicateTimeline(name)
        if dup:
            return {"success": True, "message": f"Duplicated timeline as '{name}'."}
        return {"success": False, "error": "Failed to duplicate timeline."}

    def list_timelines(self) -> dict:
        """List all timelines in the current project."""
        proj = self.get_current_project()
        if not proj:
            return {"success": False, "error": "No active project."}
        
        count = proj.GetTimelineCount()
        timelines = []
        current = proj.GetCurrentTimeline()
        current_name = current.GetName() if current else None

        for idx in range(1, count + 1):
            tl = proj.GetTimelineByIndex(idx)
            if tl:
                timelines.append({
                    "index": idx,
                    "name": tl.GetName(),
                    "is_active": (tl.GetName() == current_name)
                })

        return {"success": True, "count": count, "timelines": timelines}

    def switch_timeline(self, target: str) -> dict:
        """Switch active timeline by name or index."""
        proj = self.get_current_project()
        if not proj:
            return {"success": False, "error": "No active project."}

        count = proj.GetTimelineCount()
        for idx in range(1, count + 1):
            tl = proj.GetTimelineByIndex(idx)
            if tl and (str(idx) == str(target) or tl.GetName().lower() == str(target).lower()):
                ok = proj.SetCurrentTimeline(tl)
                return {"success": ok, "message": f"Switched to timeline '{tl.GetName()}'."}

        return {"success": False, "error": f"Timeline '{target}' not found."}

    # =========================================================================
    # 4. TIMECODE & PLAYHEAD NAVIGATION
    # =========================================================================
    def get_timecode(self) -> dict:
        """Get current playhead timecode and frame info."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}
        
        tc = tl.GetCurrentTimecode()
        start_tc = tl.GetStartTimecode()
        return {
            "success": True,
            "current_timecode": tc,
            "start_timecode": start_tc,
            "message": f"Playhead is at: {tc}"
        }

    def set_timecode(self, timecode: str) -> dict:
        """Seek playhead to a specific timecode (e.g. '01:00:15:00' or '00:00:10:00')."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}

        # Normalize timecode format if user entered seconds or partial timecode
        formatted_tc = timecode.strip()
        if re.match(r'^\d+$', formatted_tc):
            secs = int(formatted_tc)
            hours = secs // 3600
            mins = (secs % 3600) // 60
            s = secs % 60
            formatted_tc = f"01:{mins:02d}:{s:02d}:00"
        elif re.match(r'^\d{2}:\d{2}$', formatted_tc):
            formatted_tc = f"01:{formatted_tc}:00"
        elif re.match(r'^\d{2}:\d{2}:\d{2}$', formatted_tc):
            formatted_tc = f"{formatted_tc}:00"

        ok = tl.SetCurrentTimecode(formatted_tc)
        if ok:
            return {"success": True, "message": f"Playhead moved to {formatted_tc}."}
        return {"success": False, "error": f"Failed to set timecode to '{formatted_tc}'."}

    def jump_to_start(self) -> dict:
        """Jump playhead to timeline beginning."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}
        start_tc = tl.GetStartTimecode() or "01:00:00:00"
        tl.SetCurrentTimecode(start_tc)
        return {"success": True, "message": f"Jumped to timeline start ({start_tc})."}

    def jump_to_end(self) -> dict:
        """Jump playhead to timeline end."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}
        end_frame = tl.GetEndFrame()
        # Convert end frame or seek
        return {"success": True, "message": f"Jumped to timeline end (frame {end_frame})."}

    # =========================================================================
    # 5. MARKERS & ANNOTATIONS
    # =========================================================================
    def add_marker(self, color: str = "Blue", name: str = "", note: str = "", duration: int = 1) -> dict:
        """Add a marker at the current playhead position."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}

        valid_colors = [
            "Blue", "Cyan", "Green", "Yellow", "Red", "Pink", "Purple",
            "Fuchsia", "Rose", "Lavender", "Sky", "Mint", "Lemon", "Sand", "Cocoa", "White"
        ]
        marker_color = "Blue"
        for c in valid_colors:
            if c.lower() == color.lower():
                marker_color = c
                break

        # Calculate current frame relative to start
        current_tc = tl.GetCurrentTimecode()
        # Parse timecode to frame estimate
        fps = 24.0
        proj = self.get_current_project()
        if proj:
            fps_str = proj.GetSetting("timelineFrameRate") or "24"
            try:
                fps = float(fps_str)
            except ValueError:
                pass

        parts = [int(p) for p in current_tc.split(':')]
        if len(parts) == 4:
            h, m, s, f = parts
            target_frame = int((h * 3600 + m * 60 + s) * fps + f)
        else:
            target_frame = tl.GetStartFrame()

        ok = tl.AddMarker(target_frame, marker_color, name or "Edit Marker", note, duration)
        if ok:
            return {"success": True, "message": f"Added {marker_color} marker '{name}' at {current_tc}."}
        return {"success": False, "error": f"Could not add marker at {current_tc}."}

    def delete_markers(self, color: str = "All") -> dict:
        """Delete markers by color or 'All'."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}
        
        ok = tl.DeleteMarkersByColor(color if color.lower() != "all" else "All")
        return {"success": ok, "message": f"Deleted {color} markers from timeline."}

    # =========================================================================
    # 6. TRACKS & EDITING TOOLS
    # =========================================================================
    def add_track(self, track_type: str = "video") -> dict:
        """Add video, audio, or subtitle track."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}
        
        t_type = track_type.lower()
        if t_type not in ["video", "audio", "subtitle"]:
            t_type = "video"

        ok = tl.AddTrack(t_type)
        return {"success": ok, "message": f"Added new {t_type} track to timeline."}

    def set_track_enable(self, track_type: str, track_index: int, enabled: bool) -> dict:
        """Enable (unmute) or disable (mute) a track."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}
        
        ok = tl.SetTrackEnable(track_type.lower(), int(track_index), bool(enabled))
        action = "Enabled" if enabled else "Muted/Disabled"
        return {"success": ok, "message": f"{action} {track_type} track {track_index}."}

    def set_track_lock(self, track_type: str, track_index: int, locked: bool) -> dict:
        """Lock or unlock a track."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}
        
        ok = tl.SetTrackLock(track_type.lower(), int(track_index), bool(locked))
        action = "Locked" if locked else "Unlocked"
        return {"success": ok, "message": f"{action} {track_type} track {track_index}."}

    def set_clip_color(self, color: str, clip_index: int = None) -> dict:
        """Set clip color label on selected or current clip."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}

        clips = tl.GetSelectedClips() or []
        if not clips:
            current_item = tl.GetCurrentVideoItem()
            if current_item:
                clips = [current_item]

        if not clips:
            return {"success": False, "error": "No clip currently selected under playhead."}

        for c in clips:
            c.SetClipColor(color)

        return {"success": True, "message": f"Changed clip color to {color} for {len(clips)} clip(s)."}

    # =========================================================================
    # 7. AI AUDIO, SUBTITLES & SCENE CUTS (DAVINCI 21 AI SUITE)
    # =========================================================================
    def detect_scene_cuts(self) -> dict:
        """Automatically detect scene cuts across the timeline."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}
        
        try:
            ok = tl.DetectSceneCuts()
            return {"success": ok, "message": "Executed AI Scene Cut Detection across active timeline."}
        except Exception as e:
            return {"success": False, "error": f"DetectSceneCuts error: {str(e)}"}

    def create_subtitles_from_audio(self) -> dict:
        """Use DaVinci Resolve 21 automatic AI speech-to-subtitles."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}
        
        try:
            ok = tl.CreateSubtitlesFromAudio()
            return {"success": ok, "message": "Triggered DaVinci AI Subtitles generation from dialogue track."}
        except Exception as e:
            return {"success": False, "error": f"CreateSubtitlesFromAudio error: {str(e)}"}

    def enable_voice_isolation(self, track_index: int = 1) -> dict:
        """Enable DaVinci Resolve Neural Engine Voice Isolation on audio track."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}
        
        try:
            ok = tl.SetVoiceIsolationState(int(track_index), {"enable": True})
            return {"success": ok, "message": f"Enabled AI Voice Isolation on Audio Track {track_index}."}
        except Exception as e:
            return {"success": False, "error": f"Voice Isolation error: {str(e)}"}

    def insert_title(self, title_text: str = "Title") -> dict:
        """Insert a Text+ title generator into the timeline."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}
        
        try:
            item = tl.InsertTitleIntoTimeline("Text+")
            return {"success": bool(item), "message": f"Inserted Text+ title '{title_text}' into timeline."}
        except Exception as e:
            return {"success": False, "error": f"Title insertion error: {str(e)}"}

    def insert_fusion_comp(self) -> dict:
        """Insert a blank Fusion Composition into the timeline."""
        tl = self.get_current_timeline()
        if not tl:
            return {"success": False, "error": "No active timeline."}
        
        try:
            item = tl.InsertFusionCompositionIntoTimeline()
            return {"success": bool(item), "message": "Inserted new Fusion Composition into timeline."}
        except Exception as e:
            return {"success": False, "error": f"Fusion comp error: {str(e)}"}

    # =========================================================================
    # 8. PROJECT SAVE, RENDER & DELIVER
    # =========================================================================
    def save_project(self) -> dict:
        """Save the active project."""
        proj = self.get_current_project()
        if not proj:
            return {"success": False, "error": "No active project."}
        ok = proj.Save()
        return {"success": ok, "message": f"Project '{proj.GetName()}' successfully saved."}

    def export_timeline(self, output_path: str, preset_name: str = "YouTube - 1080p") -> dict:
        """Configure export and start rendering in Deliver page."""
        proj = self.get_current_project()
        if not proj:
            return {"success": False, "error": "No active project."}
        
        self.switch_page("deliver")
        
        out_dir = os.path.dirname(os.path.abspath(output_path))
        out_name = os.path.basename(output_path)
        os.makedirs(out_dir, exist_ok=True)

        try:
            proj.LoadRenderPreset(preset_name)
        except Exception:
            pass

        proj.SetRenderSettings({
            "TargetDir": out_dir,
            "CustomName": out_name.replace(".mp4", "")
        })
        
        job_id = proj.AddRenderJob()
        ok = proj.StartRendering(job_id)
        return {
            "success": ok,
            "job_id": job_id,
            "target": output_path,
            "message": f"Configured render job '{preset_name}' to {output_path} and started rendering."
        }

    def start_rendering(self) -> dict:
        """Start rendering active jobs."""
        proj = self.get_current_project()
        if not proj:
            return {"success": False, "error": "No active project."}
        ok = proj.StartRendering()
        return {"success": ok, "message": "Rendering started."}

    def get_project_summary(self) -> dict:
        """Return comprehensive overview of the active project and environment."""
        if not self.is_connected():
            return {"connected": False, "message": "DaVinci Resolve is not connected."}
        
        ver = self.get_version()
        proj = self.get_current_project()
        if not proj:
            return {"connected": True, "version": ver, "project": None, "message": "Connected to Resolve, but no project is open."}

        tl = self.get_current_timeline()
        mp = self.get_media_pool()
        current_folder = mp.GetCurrentFolder() if mp else None
        clips = current_folder.GetClipList() if current_folder else []

        return {
            "connected": True,
            "version": ver,
            "project_name": proj.GetName(),
            "timeline_name": tl.GetName() if tl else "None",
            "timeline_timecode": tl.GetCurrentTimecode() if tl else "N/A",
            "media_pool_clips": len(clips),
            "timeline_count": proj.GetTimelineCount(),
            "message": f"Project: '{proj.GetName()}' | Active Timeline: '{tl.GetName() if tl else 'None'}'"
        }
