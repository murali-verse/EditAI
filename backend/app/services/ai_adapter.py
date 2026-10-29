import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from app.models.schemas import TimelineState, MediaMetadata, SceneSegment

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

class AIModelAdapter:
    @staticmethod
    def is_ollama_available() -> bool:
        """Checks if local Ollama server is responding."""
        try:
            req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags", headers={"User-Agent": "EditMind-AI"})
            with urllib.request.urlopen(req, timeout=1.0) as response:
                return response.status == 200
        except Exception:
            return False

    @classmethod
    def interpret_command_with_ollama(
        cls,
        prompt: str,
        timeline: TimelineState,
        media: Optional[MediaMetadata] = None,
        scenes: Optional[list] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Attempts to prompt Ollama local LLM to extract structured editing action.
        Returns typed action dictionary or None if Ollama fails/offline.
        """
        if not cls.is_ollama_available():
            return None

        # Prepare context description for LLM
        timeline_context = {
            "total_duration": timeline.total_duration,
            "clips_count": len(timeline.clips),
            "clips": [
                {"id": c.id, "name": c.name, "start": c.timeline_start, "end": c.timeline_end, "dur": c.duration}
                for c in timeline.clips[:6]
            ],
            "selection_range": timeline.selection_range,
            "selected_clip_id": timeline.selected_clip_id
        }

        system_instruction = (
            "You are EditMind AI, a precision video editor assistant. "
            "Convert the user natural-language video editing instruction into a JSON object matching this schema:\n"
            "{\n"
            '  "action": "play" | "pause" | "select" | "split" | "cut" | "delete" | "trim" | "undo" | "redo" | "show_scenes" | "export",\n'
            '  "target_clip_id": string or null,\n'
            '  "start_time": float or null (in seconds),\n'
            '  "end_time": float or null (in seconds),\n'
            '  "timeline_position": float or null (in seconds),\n'
            '  "track_id": "V1" or null,\n'
            '  "confirmation_required": boolean,\n'
            '  "explanation": "concise description of what edit will be executed"\n'
            "}\n"
            "Return ONLY the raw JSON string with no markdown fences, no formatting, and no extra text."
        )

        user_content = f"Timeline state: {json.dumps(timeline_context)}\nUser command: \"{prompt}\""

        try:
            payload = json.dumps({
                "model": OLLAMA_MODEL,
                "prompt": f"{system_instruction}\n\n{user_content}",
                "stream": False,
                "format": "json"
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{OLLAMA_HOST}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5.0) as res:
                res_data = json.loads(res.read().decode("utf-8"))
                llm_response = res_data.get("response", "").strip()
                parsed = json.loads(llm_response)
                return parsed
        except Exception as e:
            # Silently fall back to deterministic parser
            print(f"Ollama inference note: {e}")
            return None
