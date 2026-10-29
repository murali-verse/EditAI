import re
from typing import Optional, Tuple, List, Dict, Any

from app.models.schemas import (
    TimelineState,
    ChatbotCommandRequest,
    ChatbotCommandResponse,
    SceneSegment
)
from app.services.timeline_manager import TimelineManager
from app.services.ai_adapter import AIModelAdapter

class CommandParser:
    @staticmethod
    def parse_timecode(time_str: str) -> Optional[float]:
        """Converts MM:SS, HH:MM:SS, 15s, etc. into seconds."""
        time_str = time_str.strip().lower()

        # Format: HH:MM:SS or MM:SS or M:SS
        if ":" in time_str:
            parts = time_str.split(":")
            try:
                if len(parts) == 3:
                    h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
                    return h * 3600 + m * 60 + s
                elif len(parts) == 2:
                    m, s = float(parts[0]), float(parts[1])
                    return m * 60 + s
            except ValueError:
                return None

        # Format: 15s, 15 sec, 15 seconds
        sec_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:s|sec|secs|seconds?)", time_str)
        if sec_match:
            try:
                return float(sec_match.group(1))
            except ValueError:
                pass

        try:
            return float(time_str)
        except ValueError:
            return None

    @classmethod
    def extract_time_range(cls, text: str) -> Optional[Tuple[float, float]]:
        """Extracts start and end time from expressions."""
        text = text.lower()
        m = re.search(r"(?:from|between)\s+([0-9:.]+s?(?:econds?)?)\s+(?:to|and|-)\s+([0-9:.]+s?(?:econds?)?)", text)
        if m:
            t1 = cls.parse_timecode(m.group(1))
            t2 = cls.parse_timecode(m.group(2))
            if t1 is not None and t2 is not None:
                return (min(t1, t2), max(t1, t2))

        m = re.search(r"(\d+:\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+:\d+(?:\.\d+)?)", text)
        if m:
            t1 = cls.parse_timecode(m.group(1))
            t2 = cls.parse_timecode(m.group(2))
            if t1 is not None and t2 is not None:
                return (min(t1, t2), max(t1, t2))

        return None

    @classmethod
    def interpret_and_execute(
        cls,
        request: ChatbotCommandRequest,
        timeline_manager: TimelineManager
    ) -> ChatbotCommandResponse:
        """
        Parses user intent via local Ollama adapter (if active) or deterministic NLP engine,
        executing safe timeline mutations.
        """
        raw_cmd = request.prompt.strip()
        cmd = raw_cmd.lower()
        timeline = request.current_timeline

        # ----------------------------------------------------
        # 1. PLAYBACK CONTROLS
        # ----------------------------------------------------
        # "Seek to 00:30."
        m_seek = re.search(r"(?:seek to|go to|jump to)\s+([0-9:.]+s?(?:econds?)?)", cmd)
        if m_seek:
            seek_ts = cls.parse_timecode(m_seek.group(1))
            if seek_ts is not None:
                seek_ts = max(0.0, min(timeline.total_duration, seek_ts))
                new_tl = timeline.model_copy(deep=True)
                new_tl.playhead_time = seek_ts
                return ChatbotCommandResponse(
                    understood=True,
                    intent="seek",
                    message=f"Playhead jumped to {seek_ts:.2f}s.",
                    target_time=seek_ts,
                    updated_timeline=new_tl
                )

        # "Play from 00:15 to 00:25."
        m_play_range = re.search(r"play from\s+([0-9:.]+)\s+to\s+([0-9:.]+)", cmd)
        if m_play_range:
            t1 = cls.parse_timecode(m_play_range.group(1))
            t2 = cls.parse_timecode(m_play_range.group(2))
            if t1 is not None and t2 is not None:
                return ChatbotCommandResponse(
                    understood=True,
                    intent="play_selected",
                    message=f"Playing time range {t1:.2f}s to {t2:.2f}s.",
                    target_range=[t1, t2],
                    target_time=t1
                )

        if re.search(r"\b(play the selected clip|play selected|preview the selected clip|play clip)\b", cmd):
            if timeline.selection_range:
                start, end = timeline.selection_range
                return ChatbotCommandResponse(
                    understood=True,
                    intent="play_selected",
                    message=f"Playing selected time range ({start:.2f}s to {end:.2f}s).",
                    target_range=[start, end],
                    target_time=start
                )
            elif timeline.selected_clip_id:
                clip = next((c for c in timeline.clips if c.id == timeline.selected_clip_id), None)
                if clip:
                    return ChatbotCommandResponse(
                        understood=True,
                        intent="play_selected",
                        message=f"Playing clip '{clip.name}' ({clip.timeline_start:.2f}s - {clip.timeline_end:.2f}s).",
                        target_range=[clip.timeline_start, clip.timeline_end],
                        target_time=clip.timeline_start
                    )
            return ChatbotCommandResponse(
                understood=True,
                intent="play",
                message="Playing video sequence from playhead.",
                target_time=timeline.playhead_time
            )

        if re.search(r"\b(play the video|start video|resume|play video|play)\b", cmd):
            return ChatbotCommandResponse(
                understood=True,
                intent="play",
                message="Playing video.",
                target_time=timeline.playhead_time
            )

        if re.search(r"\b(pause the video|stop the video|pause playback|pause video|stop|pause)\b", cmd):
            return ChatbotCommandResponse(
                understood=True,
                intent="pause",
                message="Paused video playback.",
                target_time=timeline.playhead_time
            )

        # ----------------------------------------------------
        # 2. SELECTION
        # ----------------------------------------------------
        # "Clear the selection."
        if re.search(r"\b(clear the selection|clear selection|deselect)\b", cmd):
            new_tl = timeline.model_copy(deep=True)
            new_tl.selection_range = None
            new_tl.selected_clip_id = None
            return ChatbotCommandResponse(
                understood=True,
                intent="clear_selection",
                message="Cleared active selection.",
                updated_timeline=new_tl
            )

        # "Select the second clip" / "Select clip 2"
        m_nth_clip = re.search(r"select (?:the )?(first|second|third|fourth|1st|2nd|3rd|4th|clip\s*\d+)", cmd)
        if m_nth_clip:
            nth_map = {"first": 0, "1st": 0, "second": 1, "2nd": 1, "third": 2, "3rd": 2, "fourth": 3, "4th": 3}
            text_val = m_nth_clip.group(1).replace("clip", "").strip()
            idx = nth_map.get(text_val)
            if idx is None and text_val.isdigit():
                idx = int(text_val) - 1
            if idx is not None and 0 <= idx < len(timeline.clips):
                target_clip = timeline.clips[idx]
                new_tl, msg = timeline_manager.select_range(timeline, target_clip.timeline_start, target_clip.timeline_end)
                new_tl.selected_clip_id = target_clip.id
                return ChatbotCommandResponse(
                    understood=True,
                    intent="select",
                    message=f"Selected clip {idx + 1} '{target_clip.name}' ({target_clip.timeline_start:.2f}s - {target_clip.timeline_end:.2f}s).",
                    target_range=[target_clip.timeline_start, target_clip.timeline_end],
                    target_time=target_clip.timeline_start,
                    updated_timeline=new_tl
                )

        # "Select the first 10 seconds."
        m_first = re.search(r"select (?:the )?first\s+(\d+(?:\.\d+)?)\s*(?:s|sec|secs|seconds?)", cmd)
        if m_first:
            dur = float(m_first.group(1))
            updated_tl, msg = timeline_manager.select_range(timeline, 0.0, dur)
            return ChatbotCommandResponse(
                understood=True,
                intent="select",
                message=msg,
                target_range=[0.0, dur],
                target_time=0.0,
                updated_timeline=updated_tl
            )

        # "Select the clip from 00:15 to 00:30."
        if "select" in cmd:
            time_range = cls.extract_time_range(cmd)
            if time_range:
                t1, t2 = time_range
                updated_tl, msg = timeline_manager.select_range(timeline, t1, t2)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="select",
                    message=msg,
                    target_range=[t1, t2],
                    target_time=t1,
                    updated_timeline=updated_tl
                )

        # ----------------------------------------------------
        # 3. SPLIT OPERATIONS
        # ----------------------------------------------------
        # "Split the selected clip at its midpoint."
        if "midpoint" in cmd:
            selected_clip = None
            if timeline.selected_clip_id:
                selected_clip = next((c for c in timeline.clips if c.id == timeline.selected_clip_id), None)
            elif timeline.selection_range:
                s, e = timeline.selection_range
                mid = (s + e) / 2
                updated_tl, msg = timeline_manager.split_clip(timeline, mid)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="split",
                    message=msg,
                    target_time=mid,
                    updated_timeline=updated_tl,
                    action_proposal={"action": "split", "title": "Split at Midpoint", "time": f"{mid:.2f}s"}
                )

            if selected_clip:
                mid = selected_clip.timeline_start + (selected_clip.duration / 2)
                updated_tl, msg = timeline_manager.split_clip(timeline, mid)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="split",
                    message=f"Split clip '{selected_clip.name}' at midpoint ({mid:.2f}s).",
                    target_time=mid,
                    updated_timeline=updated_tl,
                    action_proposal={"action": "split", "title": "Split Clip at Midpoint", "time": f"{mid:.2f}s"}
                )

        # "Split the clip at the current playhead."
        if "playhead" in cmd:
            ph = timeline.playhead_time
            if 0 < ph < timeline.total_duration:
                updated_tl, msg = timeline_manager.split_clip(timeline, ph)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="split",
                    message=msg,
                    target_time=ph,
                    updated_timeline=updated_tl
                )

        # "Split the clip at 00:20" or "split at 18"
        if "split" in cmd:
            m_split = re.search(r"split\s*(?:the clip\s*)?(?:at\s*)?([0-9:.]+s?(?:econds?)?)", cmd)
            target_ts = None
            if m_split:
                target_ts = cls.parse_timecode(m_split.group(1))

            if target_ts is not None:
                updated_tl, msg = timeline_manager.split_clip(timeline, target_ts)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="split",
                    message=msg,
                    target_time=target_ts,
                    updated_timeline=updated_tl,
                    action_proposal={"action": "split", "title": "Split Clip", "time": f"{target_ts:.2f}s"}
                )
            else:
                return ChatbotCommandResponse(
                    understood=False,
                    intent="clarify",
                    message="Please specify the timestamp to split (e.g., 'Split at 00:18').",
                    prompt_for_clarification="Where should the clip be split?"
                )

        # ----------------------------------------------------
        # 4. DELETION AND CUTTING
        # ----------------------------------------------------
        # "Delete the second half of the selected clip."
        if "second half" in cmd:
            clip = None
            if timeline.selected_clip_id:
                clip = next((c for c in timeline.clips if c.id == timeline.selected_clip_id), None)
            if clip:
                mid = clip.timeline_start + (clip.duration / 2)
                end = clip.timeline_end
                updated_tl, msg = timeline_manager.delete_range(timeline, mid, end)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="delete",
                    message=f"Deleted second half of '{clip.name}' ({mid:.2f}s - {end:.2f}s).",
                    updated_timeline=updated_tl,
                    action_proposal={"action": "delete", "title": "Delete Second Half", "range": f"{mid:.2f}s - {end:.2f}s"}
                )

        # "Remove the first 10 seconds."
        m_del_first = re.search(r"(?:remove|delete|cut)\s+(?:the\s+)?first\s+(\d+(?:\.\d+)?)\s*(?:s|sec|secs|seconds?)", cmd)
        if m_del_first:
            dur = float(m_del_first.group(1))
            updated_tl, msg = timeline_manager.delete_range(timeline, 0.0, dur)
            return ChatbotCommandResponse(
                understood=True,
                intent="delete",
                message=msg,
                target_range=[0.0, dur],
                updated_timeline=updated_tl
            )

        # "Remove the section from 00:20 to 00:30."
        if any(w in cmd for w in ["delete", "remove", "cut"]):
            time_range = cls.extract_time_range(cmd)
            if time_range:
                t1, t2 = time_range
                is_cut = "cut" in cmd
                updated_tl, msg = timeline_manager.delete_range(timeline, t1, t2, is_cut=is_cut)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="cut" if is_cut else "delete",
                    message=msg,
                    target_range=[t1, t2],
                    updated_timeline=updated_tl,
                    action_proposal={"action": "delete", "title": f"{'Cut' if is_cut else 'Delete'} Range", "range": f"{t1:.2f}s - {t2:.2f}s"}
                )

        # "Cut the selected section."
        if re.search(r"\b(cut the selected section|cut selected|cut selection|cut)\b", cmd):
            if not timeline.selection_range and not timeline.selected_clip_id:
                return ChatbotCommandResponse(
                    understood=False,
                    intent="clarify",
                    message="No segment is currently selected to cut. Select a range or clip first."
                )
            updated_tl, msg = timeline_manager.cut_selection(timeline)
            return ChatbotCommandResponse(
                understood=True,
                intent="cut",
                message=msg,
                updated_timeline=updated_tl
            )

        # "Delete the selected segment."
        if re.search(r"\b(delete the selected segment|delete selected|delete clip|delete segment|remove selected)\b", cmd):
            if not timeline.selection_range and not timeline.selected_clip_id:
                return ChatbotCommandResponse(
                    understood=False,
                    intent="clarify",
                    message="No segment is currently selected to delete."
                )
            updated_tl, msg = timeline_manager.delete_selected_clip(timeline)
            return ChatbotCommandResponse(
                understood=True,
                intent="delete",
                message=msg,
                updated_timeline=updated_tl
            )

        # ----------------------------------------------------
        # 5. TRIM
        # ----------------------------------------------------
        if "trim" in cmd:
            time_range = cls.extract_time_range(cmd)
            if time_range:
                t1, t2 = time_range
                updated_tl, msg = timeline_manager.trim_timeline(timeline, t1, t2)
                return ChatbotCommandResponse(
                    understood=True,
                    intent="trim",
                    message=msg,
                    target_range=[t1, t2],
                    updated_timeline=updated_tl
                )

        # ----------------------------------------------------
        # 6. UNDO & REDO
        # ----------------------------------------------------
        if re.search(r"\b(undo the last edit|undo last|undo edit|undo)\b", cmd):
            updated_tl, msg = timeline_manager.undo(timeline)
            return ChatbotCommandResponse(understood=True, intent="undo", message=msg, updated_timeline=updated_tl)

        if re.search(r"\b(redo the last edit|redo last|redo edit|redo)\b", cmd):
            updated_tl, msg = timeline_manager.redo(timeline)
            return ChatbotCommandResponse(understood=True, intent="redo", message=msg, updated_timeline=updated_tl)

        # ----------------------------------------------------
        # 7. EXPORT COMMANDS
        # ----------------------------------------------------
        if "export" in cmd:
            aspect = "16:9"
            if "9:16" in cmd or "vertical" in cmd:
                aspect = "9:16"
            elif "1:1" in cmd or "square" in cmd:
                aspect = "1:1"

            res_mode = "1080p" if "1080p" in cmd else "720p" if "720p" in cmd else "original"
            return ChatbotCommandResponse(
                understood=True,
                intent="export",
                message=f"Opening Export configured for {aspect} aspect ratio ({res_mode}).",
                action_proposal={"action": "export", "aspect_ratio": aspect, "resolution": res_mode}
            )

        # ----------------------------------------------------
        # 8. SCENES & CLIPS
        # ----------------------------------------------------
        if re.search(r"\b(show all detected scenes|show scenes|detected scenes|list scenes)\b", cmd):
            count = len(request.scenes) if request.scenes else 0
            return ChatbotCommandResponse(
                understood=True,
                intent="show_scenes",
                message=f"Showing {count} detected scenes in the media analysis inspector."
            )

        # Fallback
        return ChatbotCommandResponse(
            understood=False,
            intent="unknown",
            message=f"Command '{raw_cmd}' unrecognized. Try: 'Select the clip from 00:10 to 00:25', 'Split at 00:18', 'Delete the selected segment', or 'Export as MP4'."
        )
