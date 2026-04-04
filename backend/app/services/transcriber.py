"""
Transcriber Service - Audio/Video Transcription using faster-whisper.
Uses CTranslate2 backend for 4x speed improvement over openai-whisper.
"""
from pathlib import Path
from typing import Optional
import time


class Transcriber:
    """
    Transcribes audio using faster-whisper (CTranslate2 backend).
    4x faster than openai-whisper, uses less memory.
    """
    
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        """
        Initialize transcriber.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v3)
            device: "cpu" or "cuda" (GPU)
            compute_type: "int8" (fast) or "float16" (GPU) or "float32"
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
    
    def _load_model(self):
        """Lazy-load the faster-whisper model."""
        if self.model is None:
            from faster_whisper import WhisperModel
            import os
            
            cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
            model_folder = f"models--Systran--faster-whisper-{self.model_size}"
            is_cached = os.path.exists(os.path.join(cache_dir, model_folder))
            
            if not is_cached:
                print(f"Downloading faster-whisper model: {self.model_size}")
            
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
        
        return self.model
    
    def transcribe(self, audio_path: str, language: str = "en") -> dict:
        """
        Transcribe audio/video file to text with timestamps.
        
        Args:
            audio_path: Path to audio/video file
            language: Language code (e.g., "en", "es", "fr")
        
        Returns:
            dict with text, segments, words, language, duration
        """
        model = self._load_model()
        
        start_time = time.time()
        
        # Transcribe with word-level timestamps
        segments_generator, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            word_timestamps=True
        )
        
        segments = []
        words_list = []
        full_text_parts = []
        
        for segment in segments_generator:
            seg_data = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            }
            
            if hasattr(segment, 'words') and segment.words:
                seg_data["words"] = [
                    {
                        "word": w.word.strip(),
                        "start": w.start,
                        "end": w.end
                    }
                    for w in segment.words
                ]
                words_list.extend(seg_data["words"])
            
            segments.append(seg_data)
            full_text_parts.append(segment.text.strip())
        
        full_text = " ".join(full_text_parts)
        elapsed = time.time() - start_time
        
        return {
            "text": full_text,
            "segments": segments,
            "words": words_list,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration
        }
    
    def get_key_moments(self, transcript: dict, min_duration: float = 2.0) -> list:
        """Identify key moments from transcript for highlights."""
        key_moments = []
        
        for seg in transcript.get("segments", []):
            text = seg["text"]
            duration = seg["end"] - seg["start"]
            
            score = 0
            
            if "!" in text:
                score += 2
            if "?" in text:
                score += 1
            if duration >= min_duration:
                score += 1
            
            engagement_words = ["oh", "wow", "no way", "what", "insane", "crazy", "let's go", "omg"]
            if any(word in text.lower() for word in engagement_words):
                score += 2
            
            if score > 0:
                key_moments.append({**seg, "score": score})
        
        key_moments.sort(key=lambda x: x["score"], reverse=True)
        return key_moments
