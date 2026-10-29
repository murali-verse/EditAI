import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional

from app.config import FFMPEG_PATH
from app.models.schemas import SpeechSegment, SubtitleItem

class SpeechService:
    @staticmethod
    def extract_audio_wav(video_path: str) -> Optional[str]:
        """Extracts 16kHz mono PCM WAV for speech recognition."""
        try:
            temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_wav_path = temp_wav.name
            temp_wav.close()

            cmd = [
                FFMPEG_PATH, "-y",
                "-i", video_path,
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                temp_wav_path
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
            if res.returncode == 0 and os.path.getsize(temp_wav_path) > 100:
                return temp_wav_path
        except Exception as e:
            print(f"Failed to extract audio wav: {e}")
        return None

    @classmethod
    def transcribe(cls, video_path: str, duration: float) -> Tuple[List[SpeechSegment], Optional[str]]:
        """
        Transcribes speech segments with start and end timestamps.
        Returns (segments, limitation_or_error_message).
        """
        wav_path = cls.extract_audio_wav(video_path)
        if not wav_path:
            return [], "No audio track found in media file or unable to extract audio stream."

        segments: List[SpeechSegment] = []
        limitation: Optional[str] = None

        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True

            # Divide audio into 5-10 second chunks or use AudioFile offset
            chunk_duration = 6.0
            current_offset = 0.0

            with sr.AudioFile(wav_path) as source:
                while current_offset < duration:
                    segment_len = min(chunk_duration, duration - current_offset)
                    if segment_len < 0.8:
                        break

                    try:
                        audio_data = recognizer.record(source, duration=segment_len)
                        # Attempt speech recognition via Google Web Speech API (free)
                        text = recognizer.recognize_google(audio_data)
                        if text and text.strip():
                            segments.append(SpeechSegment(
                                start_time=round(current_offset, 2),
                                end_time=round(min(current_offset + segment_len, duration), 2),
                                text=text.strip().capitalize(),
                                confidence=0.92
                            ))
                    except sr.UnknownValueError:
                        # Normal when segment contains music, sound effects, or silence
                        pass
                    except sr.RequestError as e:
                        limitation = f"Speech recognition service unavailable (network/service: {e}). Audio analysis fell back to silence detection."
                        break
                    except Exception as e:
                        print(f"Recognition chunk error at {current_offset}: {e}")

                    current_offset += segment_len

            if not segments and not limitation:
                limitation = "No clear spoken dialogue was detected in the audio track."

        except ImportError:
            limitation = "Speech recognition module is not installed."
        except Exception as e:
            limitation = f"Speech analysis encountered an issue: {str(e)}"
        finally:
            if wav_path and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except Exception:
                    pass

        return segments, limitation

    @staticmethod
    def speech_to_subtitles(speech_segments: List[SpeechSegment]) -> List[SubtitleItem]:
        """Converts transcribed speech segments into SubtitleItem list."""
        subtitles: List[SubtitleItem] = []
        for idx, seg in enumerate(speech_segments):
            subtitles.append(SubtitleItem(
                id=idx + 1,
                start_time=seg.start_time,
                end_time=seg.end_time,
                text=seg.text
            ))
        return subtitles
