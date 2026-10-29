import os
import json
import re
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List

from app.models.schemas import TimelineState, MediaMetadata, SceneSegment

DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

class AIModelAdapter:
    """
    Multi-Provider Frontier LLM Adapter supporting:
    1. Claude Fable 5.1 (Anthropic Messages API / OpenRouter claude-fable-5-1)
    2. Google Gemini API (gemini-1.5-flash, gemini-2.0-flash, gemini-2.5-flash)
    3. OpenAI / Groq / OpenRouter API
    4. Local Ollama (dynamic model detection e.g. llama3.2:1b)
    """

    @classmethod
    def call_fable_anthropic(
        cls,
        user_prompt: str,
        system_instruction: str,
        api_key: str,
        model: str = "claude-fable-5-1",
        base_url: str = "https://api.anthropic.com/v1"
    ) -> Optional[Dict[str, Any]]:
        """
        Invokes Claude Fable 5.1 via Anthropic Messages REST API.
        Extracts structured JSON response.
        """
        if not api_key:
            return None

        clean_key = api_key.strip()
        url = f"{base_url.rstrip('/')}/messages"
        payload = {
            "model": model or "claude-fable-5-1",
            "max_tokens": 4096,
            "system": system_instruction,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }

        headers = {
            "Content-Type": "application/json",
            "x-api-key": clean_key,
            "anthropic-version": "2023-06-01",
            "User-Agent": "EditMind-AI/Claude-Fable"
        }

        # If key looks like an OpenAI/OpenRouter bearer token, support fallback header
        if clean_key.startswith("sk-or-") or "openrouter" in base_url:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {clean_key}",
                "HTTP-Referer": "https://editmind.ai",
                "X-Title": "EditMind AI"
            }
            url = f"{base_url.rstrip('/')}/chat/completions"
            payload = {
                "model": "anthropic/claude-fable-5-1" if "openrouter" in base_url else (model or "claude-fable-5-1"),
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2
            }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=15.0) as res:
                res_data = json.loads(res.read().decode("utf-8"))
                
                # Check Anthropic format
                if "content" in res_data and isinstance(res_data["content"], list):
                    for item in res_data["content"]:
                        if item.get("type") == "text":
                            raw_text = item.get("text", "").strip()
                            return cls._clean_and_parse_json(raw_text)

                # Check OpenAI / OpenRouter format
                choices = res_data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "").strip()
                    return cls._clean_and_parse_json(content)
        except Exception as e:
            print(f"Claude Fable 5.1 API note: {e}")
            return None
        return None

    @classmethod
    def _clean_and_parse_json(cls, raw_text: str) -> Optional[Dict[str, Any]]:
        """Cleans and extracts JSON object from LLM response text."""
        if not raw_text:
            return None
        
        # 1. Direct parse
        try:
            return json.loads(raw_text)
        except Exception:
            pass

        # 2. Extract from markdown code fences ```json ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
        if fence_match:
            try:
                return json.loads(fence_match.group(1).strip())
            except Exception:
                pass

        # 3. Find outermost braces { ... }
        brace_match = re.search(r"(\{[\s\S]*\})", raw_text)
        if brace_match:
            try:
                return json.loads(brace_match.group(1).strip())
            except Exception:
                pass

        return None

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
        fable_key = config.get("fable_api_key") or config.get("anthropic_api_key") or os.environ.get("FABLE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
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
            "You are EditMind AI, powered by Claude Fable 5.1 precision reasoning. "
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

        # 1. Claude Fable 5.1 (Top Priority for precision reasoning)
        if (provider in ["fable", "claude", "auto"]) and fable_key:
            res = cls.call_fable_anthropic(user_content, system_instruction, fable_key, custom_model or "claude-fable-5-1")
            if res:
                res["llm_provider"] = "Claude Fable 5.1"
                return res

        # 2. Try Gemini if configured or API key present
        if (provider in ["gemini", "auto"]) and api_key:
            res = cls.call_gemini(user_content, system_instruction, api_key, custom_model or "gemini-1.5-flash")
            if res:
                res["llm_provider"] = "Google Gemini"
                return res

        # 3. Try OpenAI / Groq if configured
        if (provider in ["openai", "groq", "auto"]) and openai_key:
            base_url = "https://api.groq.com/openai/v1" if (provider == "groq" or "gsk_" in openai_key) else "https://api.openai.com/v1"
            model = custom_model or ("llama-3.3-70b-versatile" if "groq" in base_url else "gpt-4o-mini")
            res = cls.call_openai_compatible(user_content, system_instruction, openai_key, base_url, model)
            if res:
                res["llm_provider"] = "Groq / OpenAI"
                return res

        # 4. Try Ollama when explicitly selected by user
        if provider == "ollama":
            ollama_models = cls.get_ollama_models()
            if ollama_models:
                res = cls.call_ollama(user_content, system_instruction, DEFAULT_OLLAMA_HOST, custom_model)
                if res:
                    res["llm_provider"] = "Ollama Local"
                    return res

        return None

    @classmethod
    def synthesize_story_with_llm(
        cls,
        clip_analyses: List[Any],
        style: str = "narrative",
        user_prompt: Optional[str] = None,
        target_duration: Optional[float] = None,
        llm_config: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Synthesizes a master narrative sequence from multi-clip source footage using Claude Fable 5.1.
        """
        config = llm_config or {}
        provider = config.get("provider", "auto").lower()
        fable_key = config.get("fable_api_key") or config.get("anthropic_api_key") or os.environ.get("FABLE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        api_key = config.get("api_key") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        openai_key = config.get("openai_api_key") or os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY")
        custom_model = config.get("model")

        # Compile rich footage catalog
        footage_manifest = []
        clip_by_name = {}
        for c in clip_analyses:
            clip_by_name[c.filename] = c
            footage_manifest.append({
                "filename": c.filename,
                "duration": round(c.duration, 2),
                "resolution": f"{c.width}x{c.height}",
                "category": c.primary_category,
                "motion_level": c.motion_level,
                "content_tags": c.content_tags,
                "speech_summary": c.speech_summary,
                "quality_score": c.quality_score,
                "scene_count": len(c.scenes)
            })

        system_instruction = (
            "You are Claude Fable 5.1, the world-class Lead Video Director and Film Editor for EditMind AI. "
            "You are assembling raw multi-source video footage into an engaging, cohesive final video sequence.\n\n"
            "Editing Objectives:\n"
            "1. Hook / Opening: Grab audience attention within the first 3-5 seconds using high-clarity dialogue or kinetic action.\n"
            "2. Visual Pacing & B-Roll: Interleave dynamic B-roll to complement spoken dialogue and keep momentum.\n"
            "3. Informational Core: Deliver the central thesis or keynote information cleanly.\n"
            "4. Climax & Closure: Provide satisfying visual closure and outro.\n\n"
            "You must return ONLY a valid JSON object with this exact structure:\n"
            "{\n"
            '  "story_title": "Creative Title of Assembled Sequence",\n'
            '  "style_rationale": "High-level directorial explanation of pacing and sequence structure",\n'
            '  "segments": [\n'
            "    {\n"
            '      "source_filename": "exact filename matching one in footage manifest",\n'
            '      "source_in": 0.0,\n'
            '      "source_out": 4.5,\n'
            '      "role": "Hook / Opening Narrative" | "Dynamic Action B-Roll" | "Core Content Exposition" | "Scenic Finale / Outro",\n'
            '      "rationale": "Professional editorial reason for selecting this exact segment",\n'
            '      "trimmed_reason": "What was cut or trimmed to maintain pacing",\n'
            '      "confidence": 0.96,\n'
            '      "caption_text": "Short synchronized caption or title card"\n'
            "    }\n"
            "  ],\n"
            '  "discarded_summary": [\n'
            '    {"clip": "filename", "range": "start - end", "reason": "why omitted"}\n'
            "  ],\n"
            '  "audio_sync_note": "How dialogue audio and b-roll ambient sound are harmonized"\n'
            "}\n\n"
            "Constraints:\n"
            "- source_in must be >= 0.0 and < source_out.\n"
            "- source_out must be <= that source clip's duration.\n"
            "- Include between 3 and 6 carefully timed segments.\n"
            "- Ensure the segments create a continuous narrative arc."
        )

        user_content = (
            f"Production Style: {style}\n"
            f"Target Total Duration: {target_duration or 'Optimal (12s - 25s)'}\n"
            f"User Directorial Request: {user_prompt or 'Create a balanced, engaging multi-clip narrative cut.'}\n\n"
            f"Source Footage Manifest:\n{json.dumps(footage_manifest, indent=2)}"
        )

        raw_result = None
        director_label = "Claude Fable 5.1"

        # 1. Claude Fable 5.1 (Anthropic frontier)
        if (provider in ["fable", "claude", "auto"]) and fable_key:
            raw_result = cls.call_fable_anthropic(user_content, system_instruction, fable_key, custom_model or "claude-fable-5-1")
            director_label = "Claude Fable 5.1"

        # 2. Gemini fallback
        if not raw_result and (provider in ["gemini", "auto"]) and api_key:
            raw_result = cls.call_gemini(user_content, system_instruction, api_key, custom_model or "gemini-1.5-flash")
            director_label = "Google Gemini"

        # 3. OpenAI / Groq fallback
        if not raw_result and (provider in ["openai", "groq", "auto"]) and openai_key:
            base_url = "https://api.groq.com/openai/v1" if (provider == "groq" or "gsk_" in openai_key) else "https://api.openai.com/v1"
            model = custom_model or ("llama-3.3-70b-versatile" if "groq" in base_url else "gpt-4o-mini")
            raw_result = cls.call_openai_compatible(user_content, system_instruction, openai_key, base_url, model)
            director_label = "OpenAI / Groq"

        if not raw_result or not isinstance(raw_result, dict):
            return None

        # Validate and clamp segment bounds against real source clips
        segments = raw_result.get("segments", [])
        if not segments or not isinstance(segments, list):
            return None

        validated_segments = []
        for seg in segments:
            fn = seg.get("source_filename")
            if fn not in clip_by_name:
                # Attempt to find best match
                for valid_fn in clip_by_name:
                    if fn and (fn in valid_fn or valid_fn in fn):
                        fn = valid_fn
                        break
                else:
                    continue

            clip_meta = clip_by_name[fn]
            dur = clip_meta.duration
            sin = max(0.0, float(seg.get("source_in", 0.0)))
            sout = min(dur, float(seg.get("source_out", dur)))
            if sout <= sin:
                sout = min(dur, sin + 3.0)
            if sin >= dur:
                sin = 0.0
                sout = min(dur, 4.0)

            validated_segments.append({
                "source_filename": fn,
                "source_filepath": clip_meta.filepath,
                "source_in": round(sin, 2),
                "source_out": round(sout, 2),
                "duration": round(sout - sin, 2),
                "role": seg.get("role") or "Narrative Segment",
                "rationale": seg.get("rationale") or f"Curated by {director_label} for visual impact.",
                "trimmed_reason": seg.get("trimmed_reason"),
                "confidence": float(seg.get("confidence", 0.95)),
                "caption_text": seg.get("caption_text")
            })

        if not validated_segments:
            return None

        raw_result["segments"] = validated_segments
        raw_result["director_label"] = director_label
        return raw_result
