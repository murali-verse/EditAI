import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List

from app.models.schemas import TimelineState, MediaMetadata, SceneSegment

DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

class AIModelAdapter:
    """
    Multi-Provider LLM Adapter supporting:
    1. Google Gemini API (gemini-1.5-flash, gemini-2.0-flash, gemini-2.5-flash)
    2. OpenAI / Groq / OpenRouter API
    3. Local Ollama (with dynamic model detection e.g. llama3.2:1b)
    """

    @classmethod
    def get_ollama_models(cls, host: str = DEFAULT_OLLAMA_HOST) -> List[str]:
        """Queries local Ollama to list available installed models."""
        try:
            req = urllib.request.Request(f"{host}/api/tags", headers={"User-Agent": "EditMind-AI"})
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                    return models
        except Exception:
            pass
        return []

    @classmethod
    def call_gemini(
        cls,
        user_prompt: str,
        system_instruction: str,
        api_key: str,
        model: str = "gemini-1.5-flash"
    ) -> Optional[Dict[str, Any]]:
        """Invokes Google Gemini REST API with structured JSON output."""
        if not api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_instruction}\n\nTask:\n{user_prompt}"}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2
            }
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10.0) as res:
                res_data = json.loads(res.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        text = parts[0].get("text", "").strip()
                        return json.loads(text)
        except Exception as e:
            print(f"Gemini API call note: {e}")
            return None
        return None

    @classmethod
    def call_openai_compatible(
        cls,
        user_prompt: str,
        system_instruction: str,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini"
    ) -> Optional[Dict[str, Any]]:
        """Invokes OpenAI or Groq / OpenRouter compatible REST API."""
        if not api_key:
            return None

        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
            )
            with urllib.request.urlopen(req, timeout=10.0) as res:
                res_data = json.loads(res.read().decode("utf-8"))
                choices = res_data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "").strip()
                    return json.loads(content)
        except Exception as e:
            print(f"OpenAI-compatible API note: {e}")
            return None
        return None

    @classmethod
    def call_ollama(
        cls,
        user_prompt: str,
        system_instruction: str,
        host: str = DEFAULT_OLLAMA_HOST,
        model: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Invokes local Ollama with auto-detected installed model."""
        installed_models = cls.get_ollama_models(host)
        if not installed_models:
            return None

        # Pick best available model
        chosen_model = model
        if not chosen_model or chosen_model not in installed_models:
            # prefer llama3.2, llama3, mistral, or the first available completion model
            for candidate in ["llama3.2:1b", "llama3.2", "llama3:latest", "llama3", "mistral"]:
                if candidate in installed_models:
                    chosen_model = candidate
                    break
            if not chosen_model:
                chosen_model = installed_models[0]

        payload = {
            "model": chosen_model,
            "prompt": f"{system_instruction}\n\n{user_prompt}",
            "stream": False,
            "format": "json"
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{host}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=12.0) as res:
                res_data = json.loads(res.read().decode("utf-8"))
                response_str = res_data.get("response", "").strip()
                return json.loads(response_str)
        except Exception as e:
            print(f"Ollama call note: {e}")
            return None

    @classmethod
    def interpret_command_with_llm(
        cls,
        prompt: str,
        timeline: TimelineState,
        media: Optional[MediaMetadata] = None,
        scenes: Optional[list] = None,
        llm_config: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Attempts to interpret generic editing instruction using the best configured LLM.
        """
        config = llm_config or {}
        provider = config.get("provider", "auto").lower()
        api_key = config.get("api_key") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        openai_key = config.get("openai_api_key") or os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY")
        custom_model = config.get("model")

        # Prepare rich timeline context
        timeline_context = {
            "total_duration": timeline.total_duration,
            "clips_count": len(timeline.clips),
            "clips": [
                {
                    "id": c.id,
                    "name": c.name,
                    "start": c.timeline_start,
                    "end": c.timeline_end,
                    "dur": c.duration,
                    "speed": c.speed or 1.0,
                    "role": getattr(c, "role", None),
                    "source_filename": getattr(c, "source_filename", "")
                }
                for c in timeline.clips
            ],
            "selected_clip_id": timeline.selected_clip_id,
            "selection_range": timeline.selection_range,
            "playhead_time": timeline.playhead_time
        }

        scenes_summary = []
        if scenes:
            for s in scenes[:10]:
                scenes_summary.append({
                    "id": getattr(s, "scene_id", 0),
                    "start": getattr(s, "start_time", 0.0),
                    "end": getattr(s, "end_time", 0.0),
                    "motion": getattr(s, "motion_score", 0.0),
                    "low_activity": getattr(s, "is_low_activity", False)
                })

        system_instruction = (
            "You are EditMind AI, an intelligent, precision video editor. "
            "Analyze the user's natural-language video editing request in the context of the active timeline and scenes. "
            "Convert their intent into an actionable JSON object with this exact structure:\n"
            "{\n"
            '  "action": "play" | "pause" | "seek" | "select" | "split" | "cut" | "delete" | "trim" | "change_speed" | "change_volume" | "undo" | "redo" | "show_scenes" | "export",\n'
            '  "target_clip_id": string or null,\n'
            '  "start_time": float or null (in timeline seconds),\n'
            '  "end_time": float or null (in timeline seconds),\n'
            '  "split_time": float or null (in timeline seconds),\n'
            '  "speed": float or null (e.g. 1.5, 2.0, 0.5),\n'
            '  "volume": float or null (0.0 to 1.0),\n'
            '  "aspect_ratio": "16:9" | "9:16" | "1:1" | null,\n'
            '  "confirmation_required": boolean,\n'
            '  "explanation": "friendly, clear explanation of what edit is executed and why",\n'
            '  "editorial_reason": "why this cut or change improves the video"\n'
            "}\n"
            "Rules:\n"
            "- If the user asks to split a clip in half, calculate its midpoint (start + dur/2).\n"
            "- If user asks to remove the second half or first half of a clip, specify start_time and end_time accordingly.\n"
            "- If user asks to trim or delete the intro/first N seconds, set start_time=0.0 and end_time=N.\n"
            "- If user asks to delete the last N seconds, set start_time=total_duration - N and end_time=total_duration.\n"
            "- Return ONLY valid JSON, no markdown formatting."
        )

        user_content = (
            f"Active Timeline: {json.dumps(timeline_context)}\n"
            f"Detected Scenes: {json.dumps(scenes_summary)}\n"
            f"User Command: \"{prompt}\""
        )

        # 1. Try Gemini if configured or API key present
        if (provider in ["gemini", "auto"]) and api_key:
            res = cls.call_gemini(user_content, system_instruction, api_key, custom_model or "gemini-1.5-flash")
            if res:
                res["llm_provider"] = "Google Gemini"
                return res

        # 2. Try OpenAI / Groq if configured
        if (provider in ["openai", "groq", "auto"]) and openai_key:
            base_url = "https://api.groq.com/openai/v1" if (provider == "groq" or "gsk_" in openai_key) else "https://api.openai.com/v1"
            model = custom_model or ("llama-3.3-70b-versatile" if "groq" in base_url else "gpt-4o-mini")
            res = cls.call_openai_compatible(user_content, system_instruction, openai_key, base_url, model)
            if res:
                res["llm_provider"] = "Groq / OpenAI"
                return res

        # 3. Try Ollama when explicitly selected by user
        if provider == "ollama":
            ollama_models = cls.get_ollama_models()
            if ollama_models:
                res = cls.call_ollama(user_content, system_instruction, DEFAULT_OLLAMA_HOST, custom_model)
                if res:
                    res["llm_provider"] = "Ollama Local"
                    return res

        return None
