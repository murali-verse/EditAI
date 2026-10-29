import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.services.ai_adapter import AIModelAdapter
from app.services.assembly_service import AssemblyService
from app.models.schemas import TimelineState, Clip, SourceClipAnalysis

def test_fable_json_parser():
    print("--- TEST 1: Fable JSON Extraction & Cleaning ---")
    raw_markdown = """Here is your editing plan:
```json
{
  "action": "split",
  "split_time": 14.5,
  "explanation": "Midpoint split executed by Claude Fable 5.1.",
  "editorial_reason": "Prepares the clip for B-roll insertion."
}
```
Direct cut applied."""
    res = AIModelAdapter._clean_and_parse_json(raw_markdown)
    assert res is not None
    assert res["action"] == "split"
    assert res["split_time"] == 14.5
    print(f"[OK] Parsed markdown-wrapped JSON: action='{res['action']}', split_time={res['split_time']}")

def test_fable_chatbot_command_mock():
    print("\n--- TEST 2: Chatbot Command with Claude Fable 5.1 Provider ---")
    mock_fable_response = {
        "action": "trim",
        "start_time": 0.0,
        "end_time": 4.0,
        "explanation": "Claude Fable 5.1 trimmed first 4 seconds of pre-roll silence.",
        "editorial_reason": "Immediate hook placement."
    }

    client = TestClient(app)
    with patch.object(AIModelAdapter, "call_fable_anthropic", return_value=mock_fable_response):
        res = client.post("/api/chatbot/command", json={
            "prompt": "Remove the initial 4 seconds pre-roll",
            "current_timeline": {
                "clips": [
                    {
                        "id": "c1",
                        "source_file": "sample.mp4",
                        "source_filename": "sample.mp4",
                        "source_start": 0.0,
                        "source_end": 20.0,
                        "timeline_start": 0.0,
                        "timeline_end": 20.0,
                        "duration": 20.0,
                        "name": "Interview"
                    }
                ],
                "total_duration": 20.0,
                "playhead_time": 0.0
            },
            "llm_config": {
                "provider": "fable",
                "fable_api_key": "sk-ant-test-fable-key-12345"
            }
        })
        assert res.status_code == 200
        data = res.json()
        print(f"[OK] Chatbot Response: {data['message']}")
        print(f"[OK] LLM Provider Tag: {data['llm_provider']}")
        assert data["llm_provider"] == "Claude Fable 5.1"
        assert "[Claude Fable 5.1]" in data["message"]

def test_fable_auto_assembly_mock():
    print("\n--- TEST 3: Multi-Video AI Assembly with Claude Fable 5.1 Director ---")
    mock_storyboard = {
        "story_title": "Kinetic Showcase Cut",
        "style_rationale": "High-impact narrative flow beginning with conversational hook and transitioning to dynamic kinetic cuts.",
        "segments": [
            {
                "source_filename": "clip1_interview.mp4",
                "source_in": 0.0,
                "source_out": 4.0,
                "role": "Hook / Opening Narrative",
                "rationale": "Clear conversational opening by speaker.",
                "trimmed_reason": "Trimmed subsequent monologue for fast pacing.",
                "confidence": 0.98,
                "caption_text": "The frontier of AI automated video editing."
            },
            {
                "source_filename": "clip2_action_broll.mp4",
                "source_in": 1.0,
                "source_out": 5.5,
                "role": "Dynamic Action B-Roll",
                "rationale": "Peak kinetic motion segment.",
                "trimmed_reason": "Omitted static intro.",
                "confidence": 0.95,
                "caption_text": "High frame-rate kinetic cutaway."
            }
        ],
        "discarded_summary": [
            {"clip": "clip1_interview.mp4", "range": "4.0s - 12.0s", "reason": "Trimmed monologue"}
        ],
        "audio_sync_note": "Harmonized by Claude Fable 5.1 with speech priority."
    }

    client = TestClient(app)
    # Load demo clips
    res_pack = client.post("/api/assembly/sample-pack")
    pack_data = res_pack.json()
    clip_paths = pack_data["clip_paths"]

    with patch.object(AIModelAdapter, "call_fable_anthropic", return_value=mock_storyboard):
        res_asm = client.post("/api/assembly/analyze-and-assemble", json={
            "media_files": clip_paths,
            "style": "narrative",
            "user_prompt": "Create a high energy cut opening with interview and action b-roll.",
            "llm_config": {
                "provider": "fable",
                "fable_api_key": "sk-ant-test-fable-key-12345"
            }
        })
        assert res_asm.status_code == 200
        asm_data = res_asm.json()
        print(f"[OK] Assembly Style: '{asm_data['style']}'")
        print(f"[OK] Segments Count: {len(asm_data['segments'])}")
        print(f"[OK] Audio Sync Note: {asm_data['audio_sync_note']}")
        assert "Claude Fable 5.1" in asm_data["style"]
        assert len(asm_data["segments"]) == 2
        assert asm_data["segments"][0]["caption_text"] == "The frontier of AI automated video editing."
        assert len(asm_data["timeline_state"]["clips"]) == 2

    print("\n============================================")
    print("  CLAUDE FABLE 5.1 INTEGRATION VERIFIED!   ")
    print("============================================")

if __name__ == "__main__":
    test_fable_json_parser()
    test_fable_chatbot_command_mock()
    test_fable_auto_assembly_mock()
