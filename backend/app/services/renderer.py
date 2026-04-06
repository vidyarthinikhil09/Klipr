"""
Renderer Service - Video Rendering with pycaps CSS-styled Animated Captions.

Uses pycaps for professional viral-style captions with:
- Word-by-word highlighting (current word pops in accent color)
- CSS-based styling with animations
- Multiple preset templates (MrBeast, Hormozi, Minimalist)
- Keyword-based color highlighting
- Fallback to MoviePy if pycaps unavailable
"""
import subprocess
import json
import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Callable

try:
    import psutil
except Exception:
    psutil = None

# Try to import pycaps, fallback to MoviePy if not available
PYCAPS_AVAILABLE = False
PYCAPS_ERROR = None
try:
    from pycaps import CapsPipelineBuilder
    from pycaps.animation import PopIn, FadeIn
    from pycaps.common import EventType, ElementType
    # Test if we can actually create a builder (checks for ffmpeg/ffprobe)
    _test_builder = CapsPipelineBuilder()
    del _test_builder
    PYCAPS_AVAILABLE = True
    print("[Renderer] pycaps loaded and ready!")
except ImportError as e:
    PYCAPS_ERROR = f"ImportError: {e}"
    print(f"[Renderer] pycaps not installed: {e}")
except RuntimeError as e:
    # pycaps installed but ffmpeg/ffprobe missing
    PYCAPS_ERROR = str(e)
    print(f"[Renderer] pycaps installed but missing dependencies (ffmpeg/ffprobe)")
except Exception as e:
    PYCAPS_ERROR = str(e)
    print(f"[Renderer] pycaps error: {e}")

from moviepy import (
    VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip,
    TextClip, CompositeAudioClip, concatenate_videoclips, ColorClip
)


# ==================== CAPTION STYLE PRESETS ====================

# CSS templates for pycaps - using .word class for word-level styling
# Font sizes optimized for 1080x1920 portrait video
PYCAPS_CSS_TEMPLATES = {
    "mrbeast": """
        .segment {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 85%;
            gap: 12px;
        }
        .word {
            font-family: 'Impact', 'Arial Black', sans-serif;
            font-size: 58px;
            color: #FFFFFF;
            text-transform: uppercase;
            -webkit-text-stroke: 4px black;
            text-shadow: 4px 4px 0px #000000;
            letter-spacing: 2px;
            display: inline-block;
        }
        .word-being-narrated {
            color: #FF0000 !important;
            transform: scale(1.2);
        }
    """,
    "hormozi": """
        .segment {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 85%;
            gap: 12px;
        }
        .word {
            font-family: 'Arial Black', 'Helvetica', sans-serif;
            font-size: 55px;
            color: #FFFFFF;
            text-transform: uppercase;
            -webkit-text-stroke: 3px black;
            text-shadow: 3px 3px 0px #000000;
        }
        .word-being-narrated {
            color: #00FF00 !important;
            transform: scale(1.25);
        }
    """,
    "tiktok": """
        .segment {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 85%;
            gap: 12px;
        }
        .word {
            font-family: 'Arial Black', sans-serif;
            font-size: 55px;
            color: #FFFFFF;
            text-transform: uppercase;
            -webkit-text-stroke: 3px black;
            text-shadow: 3px 3px 0px #FF0050;
        }
        .word-being-narrated {
            color: #00F2EA !important;
            transform: scale(1.2);
            text-shadow: 3px 3px 0px #FF0050, 0 0 20px #00F2EA;
        }
    """,
    "karaoke": """
        .segment {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 85%;
            gap: 12px;
        }
        .word {
            font-family: 'Impact', sans-serif;
            font-size: 55px;
            color: #666666;
            text-transform: uppercase;
            -webkit-text-stroke: 3px black;
        }
        .word-being-narrated {
            color: #FFFF00 !important;
            text-shadow: 0 0 20px #FFFF00, 0 0 40px #FFFF00;
            transform: scale(1.15);
        }
    """,
    "minimalist": """
        .segment {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 85%;
            gap: 14px;
        }
        .word {
            font-family: 'Helvetica Neue', 'Arial', sans-serif;
            font-size: 52px;
            color: #FFFFFF;
            text-shadow: 2px 2px 5px rgba(0,0,0,0.9);
        }
        .word-being-narrated {
            color: #00BFFF !important;
            font-weight: bold;
            transform: scale(1.1);
        }
    """,
    "classic": """
        .segment {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 85%;
            gap: 12px;
        }
        .word {
            font-family: 'Impact', sans-serif;
            font-size: 58px;
            color: #FFFFFF;
            text-transform: uppercase;
            -webkit-text-stroke: 4px black;
            text-shadow: 4px 4px 0px #333333;
        }
        .word-being-narrated {
            color: #FF0000 !important;
            transform: scale(1.2);
        }
    """,
}

# Keywords that trigger special colors (used in CSS tagging)
HIGHLIGHT_KEYWORDS = {
    "yellow": ["insane", "crazy", "what", "omg", "wow", "bro", "dude", "no", "way", "actually", "literally"],
    "red": ["dead", "killed", "destroyed", "rip", "failed", "lost", "died", "banned", "cancel"],
    "green": ["won", "win", "clutch", "perfect", "god", "goat", "legend", "best", "epic", "let's", "go", "money"]
}

# MoviePy fallback settings
MOVIEPY_STYLES = {
    "mrbeast": {
        "font": "C:/Windows/Fonts/impact.ttf",
        "font_size": 110,
        "stroke_width": 8,
        "shadow_offset": 6,
        "color_rotation": ["#FFFFFF", "#FF0000", "#00FF00"],
        "words_per_group": 3,
        "y_position": 0.50,
    },
    "hormozi": {
        "font": "C:/Windows/Fonts/arialbd.ttf",
        "font_size": 105,
        "stroke_width": 7,
        "shadow_offset": 5,
        "color_rotation": ["#FFFFFF", "#00FF00", "#FFFFFF"],
        "words_per_group": 3,
        "y_position": 0.50,
    },
    "tiktok": {
        "font": "C:/Windows/Fonts/arialbd.ttf",
        "font_size": 105,
        "stroke_width": 7,
        "shadow_offset": 5,
        "color_rotation": ["#FFFFFF", "#00F2EA", "#FF0050"],
        "words_per_group": 3,
        "y_position": 0.50,
    },
    "karaoke": {
        "font": "C:/Windows/Fonts/impact.ttf",
        "font_size": 105,
        "stroke_width": 6,
        "shadow_offset": 5,
        "color_rotation": ["#666666", "#FFFF00", "#666666"],
        "words_per_group": 3,
        "y_position": 0.50,
    },
    "minimalist": {
        "font": "C:/Windows/Fonts/arial.ttf",
        "font_size": 95,
        "stroke_width": 5,
        "shadow_offset": 4,
        "color_rotation": ["#FFFFFF", "#00BFFF", "#FFFFFF"],
        "words_per_group": 3,
        "y_position": 0.50,
    },
    "classic": {
        "font": "C:/Windows/Fonts/impact.ttf",
        "font_size": 110,
        "stroke_width": 8,
        "shadow_offset": 6,
        "color_rotation": ["#FFFFFF", "#FF0000", "#00FF00"],
        "words_per_group": 3,
        "y_position": 0.50,
    },
}


class Renderer:
    """Renders viral YouTube Shorts with animated word-by-word captions."""
    
    def __init__(
        self,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
        bitrate: str = "4M",
        caption_style: str = "mrbeast"
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.bitrate = bitrate
        self.caption_style = caption_style
        self.caption_time_offset = -0.12
        
        # Load MoviePy fallback style
        self.moviepy_style = MOVIEPY_STYLES.get(caption_style, MOVIEPY_STYLES["classic"])


def get_memory_mb() -> Optional[int]:
    """Return current process RSS in MB if psutil available."""
    if psutil:
        try:
            return int(psutil.Process().memory_info().rss / (1024 * 1024))
        except Exception:
            return None
    return None
    
    def resize_clip_to_fill(self, clip, target_width: int, target_height: int):
        """Resize clip to fill target dimensions (crop excess)."""
        clip_ratio = clip.w / clip.h
        target_ratio = target_width / target_height
        
        if clip_ratio > target_ratio:
            new_height = target_height
            new_width = int(clip_ratio * new_height)
        else:
            new_width = target_width
            new_height = int(new_width / clip_ratio)
        
        resized = clip.resized(new_size=(new_width, new_height))
        
        x1 = (new_width - target_width) // 2
        y1 = (new_height - target_height) // 2
        x2 = x1 + target_width
        y2 = y1 + target_height
        
        return resized.cropped(x1=x1, y1=y1, x2=x2, y2=y2)
    
    def get_keyword_color(self, word: str) -> Optional[str]:
        """Check if word should have a special keyword color."""
        word_lower = word.lower().strip(".,!?\"'")
        for color, keywords in HIGHLIGHT_KEYWORDS.items():
            if word_lower in keywords:
                if color == "yellow":
                    return "#FFD700"
                elif color == "red":
                    return "#FF4444"
                elif color == "green":
                    return "#00FF00"
        return None
    
    def _run_pycaps_pipeline(
        self,
        clip_path: str,
        css_path: str,
        transcript_path: str,
        output_path: str
    ) -> str:
        """
        Run pycaps pipeline in isolation (called from thread to avoid asyncio conflict).
        Playwright sync API doesn't work in asyncio event loops, so this must run in a thread.
        """
        from pycaps import CapsPipelineBuilder
        from pycaps.animation import PopIn
        from pycaps.common import EventType, ElementType
        
        print(f"[pycaps] Building pipeline for style: {self.caption_style}")
        
        builder = CapsPipelineBuilder()
        builder.with_input_video(clip_path)
        builder.with_output_video(output_path)
        builder.add_css(css_path)
        builder.with_transcription_file(transcript_path)
        
        # Add word-level pop animation on narration
        builder.add_animation(
            animation=PopIn(duration=0.15),
            when=EventType.ON_NARRATION_STARTS,
            what=ElementType.WORD
        )
        
        print(f"[pycaps] Running render pipeline...")
        
        pipeline = builder.build()
        pipeline.run()
        
        print(f"[pycaps] Render complete: {output_path}")
        return output_path
    
    def render_with_pycaps(
        self,
        clip_path: str,
        transcript: dict,
        output_path: str,
        progress_callback: Callable[[float], None] = None
    ) -> str:
        """Render video using pycaps for professional CSS-styled captions."""
        import concurrent.futures
        
        # Create temp directory for pycaps work
        temp_dir = tempfile.mkdtemp(prefix="pycaps_")
        css_path = os.path.join(temp_dir, "style.css")
        transcript_path = os.path.join(temp_dir, "transcript.json")
        portrait_video_path = os.path.join(temp_dir, "portrait_input.mp4")
        
        try:
            # Step 1: Convert landscape video to portrait (9:16) first
            print(f"[pycaps] Converting video to portrait 9:16...")
            if progress_callback:
                progress_callback(5)

            mem_before = get_memory_mb()
            if mem_before:
                print(f"[pycaps] Memory before portrait conversion: {mem_before} MB")

            self._convert_to_portrait(clip_path, portrait_video_path)

            mem_after_conv = get_memory_mb()
            if mem_after_conv:
                print(f"[pycaps] Memory after portrait conversion: {mem_after_conv} MB")
            
            if progress_callback:
                progress_callback(15)
            
            # Write CSS style
            css_content = PYCAPS_CSS_TEMPLATES.get(self.caption_style, PYCAPS_CSS_TEMPLATES["mrbeast"])
            
            # Add keyword highlight rules
            css_content += """
                .word.keyword-yellow { color: #FFD700 !important; }
                .word.keyword-red { color: #FF4444 !important; }
                .word.keyword-green { color: #00FF00 !important; }
            """
            
            with open(css_path, "w", encoding="utf-8") as f:
                f.write(css_content)
            
            # Convert Whisper transcript to pycaps format (whisper_json compatible)
            pycaps_transcript = self._convert_transcript_for_pycaps(transcript)
            with open(transcript_path, "w", encoding="utf-8") as f:
                json.dump(pycaps_transcript, f)
            
            if progress_callback:
                progress_callback(20)
            
            # Run pycaps in a separate thread to avoid Playwright/asyncio conflict
            # Playwright sync API cannot run in asyncio event loop (FastAPI)
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                if progress_callback:
                    progress_callback(25)

                mem_before_pycaps = get_memory_mb()
                if mem_before_pycaps:
                    print(f"[pycaps] Memory before pycaps pipeline: {mem_before_pycaps} MB")

                future = executor.submit(
                    self._run_pycaps_pipeline,
                    portrait_video_path,  # Use portrait version
                    css_path,
                    transcript_path,
                    output_path
                )
                result = future.result(timeout=300)  # 5 min timeout

                mem_after_pycaps = get_memory_mb()
                if mem_after_pycaps:
                    print(f"[pycaps] Memory after pycaps pipeline: {mem_after_pycaps} MB")
            
            if progress_callback:
                progress_callback(100)
            
            return result
            
        except Exception as e:
            print(f"[pycaps] Error during render: {e}")
            raise
            
        finally:
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _convert_to_portrait(self, input_path: str, output_path: str):
        """
        Convert any video to portrait 9:16 (1080x1920) format.
        Crops and scales to fill the frame (no black bars).
        """
        clip = VideoFileClip(input_path)
        
        # Limit duration to 55 seconds for Shorts
        final_duration = min(clip.duration, 55)
        clip = clip.subclipped(0, final_duration)
        
        # Resize and crop to fill portrait frame
        portrait_clip = self.resize_clip_to_fill(clip, self.width, self.height)
        
        # Write to temp file (use low-memory ffmpeg preset)
        print(f"[renderer] Writing portrait file to {output_path} (preset=ultrafast, threads=1)")
        portrait_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=self.fps,
            bitrate=self.bitrate,
            threads=1,
            preset="ultrafast",
            logger=None
        )
        
        # Cleanup
        portrait_clip.close()
        clip.close()
        print(f"[pycaps] Portrait conversion complete: {self.width}x{self.height}")
    
    def _convert_transcript_for_pycaps(self, whisper_transcript: dict) -> dict:
        """
        Convert Whisper transcript format to pycaps format.
        
        Rules:
        - Max 3 words per segment
        - Respects natural pauses (if gap > 0.3s between words, start new segment)
        - Only shows words as they're being spoken (not future words)
        """
        MAX_WORDS_PER_SEGMENT = 3
        PAUSE_THRESHOLD = 0.3  # seconds - if gap > this, start new segment
        
        segments = whisper_transcript.get("segments", [])
        pycaps_segments = []
        
        for seg in segments:
            if "words" in seg and seg["words"]:
                words = seg["words"]
                current_chunk = []
                
                for i, word in enumerate(words):
                    # Check if there's a pause before this word
                    if current_chunk:
                        last_word_end = current_chunk[-1].get("end", 0)
                        current_word_start = word.get("start", 0)
                        gap = current_word_start - last_word_end
                        
                        # If there's a significant pause OR we hit max words, flush chunk
                        if gap > PAUSE_THRESHOLD or len(current_chunk) >= MAX_WORDS_PER_SEGMENT:
                            # Save current chunk
                            if current_chunk:
                                pycaps_segments.append(self._create_pycaps_segment(current_chunk))
                            current_chunk = []
                    
                    current_chunk.append(word)
                
                # Don't forget the last chunk
                if current_chunk:
                    pycaps_segments.append(self._create_pycaps_segment(current_chunk))
            else:
                # No word timing - split text by words and estimate timing
                text = seg.get("text", "").strip()
                words = text.split()
                seg_start = seg.get("start", 0)
                seg_end = seg.get("end", seg_start + 1)
                total_duration = seg_end - seg_start
                
                if words:
                    time_per_word = total_duration / len(words)
                    
                    for i in range(0, len(words), MAX_WORDS_PER_SEGMENT):
                        chunk = words[i:i + MAX_WORDS_PER_SEGMENT]
                        chunk_start = seg_start + (i * time_per_word)
                        chunk_end = chunk_start + (len(chunk) * time_per_word)
                        
                        pycaps_seg = {
                            "start": chunk_start,
                            "end": chunk_end,
                            "text": " ".join(chunk),
                        }
                        pycaps_segments.append(pycaps_seg)
        
        print(f"[pycaps] Converted transcript: {len(pycaps_segments)} segments (respects pauses, max {MAX_WORDS_PER_SEGMENT} words)")
        return {"segments": pycaps_segments}
    
    def _create_pycaps_segment(self, words: list) -> dict:
        """Create a pycaps segment from a list of word dicts."""
        chunk_text = " ".join(w.get("word", "").strip() for w in words)
        chunk_start = words[0].get("start", 0)
        chunk_end = words[-1].get("end", chunk_start + 0.5)
        
        return {
            "start": chunk_start,
            "end": chunk_end,
            "text": chunk_text.strip(),
            "words": [
                {
                    "word": w.get("word", "").strip(),
                    "start": w.get("start", 0),
                    "end": w.get("end", 0)
                }
                for w in words
            ]
        }

    def _seconds_to_ass_time(self, seconds: float) -> str:
        """Format seconds to ASS time H:MM:SS.cc"""
        if seconds is None:
            seconds = 0.0
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:05.2f}"

    def _write_ass_subs(self, transcript: dict, ass_path: str):
        """Write a minimal ASS subtitle file from the transcript segments."""
        segments = transcript.get("segments", [])

        with open(ass_path, "w", encoding="utf-8") as f:
            f.write("[Script Info]\n")
            f.write("ScriptType: v4.00+\n")
            f.write(f"PlayResX: {self.width}\n")
            f.write(f"PlayResY: {self.height}\n")
            f.write("\n")
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            # Use Impact/Arial fallback and reasonable outline/shadow for visibility
            f.write("Style: Default,Impact,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,4,2,8,10,10,50,1\n")
            f.write("\n")
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

            for seg in segments:
                start = seg.get("start", 0) + self.caption_time_offset
                end = seg.get("end", start + 0.5)
                text = seg.get("text", "")

                # If words present, prefer combined words
                if "words" in seg and seg["words"]:
                    text = " ".join(w.get("word", "") for w in seg["words"]).strip()

                if not text:
                    continue

                # ASS requires \N for newlines
                text = text.replace("\n", "\\N")

                start_ts = self._seconds_to_ass_time(max(0.0, start))
                end_ts = self._seconds_to_ass_time(max(start + 0.01, end))

                # Write the dialogue line
                line = f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{text}\n"
                f.write(line)

    def render_with_ffmpeg_ass(
        self,
        clip_path: str,
        transcript: dict,
        output_path: str,
        progress_callback: Callable[[float], None] = None
    ) -> str:
        """Render by creating ASS subtitles and burning them in with ffmpeg (low Python memory)."""
        temp_dir = tempfile.mkdtemp(prefix="ffmpegsubs_")
        portrait_video_path = os.path.join(temp_dir, "portrait_input.mp4")
        ass_path = os.path.join(temp_dir, "subs.ass")

        try:
            # Step 1: Convert to portrait (ffmpeg scale+crop) and limit duration to 55s
            if progress_callback:
                progress_callback(5)

            print(f"[ffmpeg] Converting to portrait: {clip_path} -> {portrait_video_path}")

            scale_filter = (
                f"scale=iw*max({self.width}/iw\,{self.height}/ih):ih*max({self.width}/iw\,{self.height}/ih),crop={self.width}:{self.height}"
            )

            cmd_convert = [
                "ffmpeg", "-y",
                "-i", clip_path,
                "-vf", scale_filter,
                "-t", "55",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-b:v", self.bitrate,
                "-c:a", "aac",
                portrait_video_path
            ]

            proc = subprocess.run(cmd_convert, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode != 0:
                print(f"[ffmpeg] Portrait convert failed: {proc.stderr.decode('utf-8', errors='ignore')}")
                raise RuntimeError("ffmpeg portrait conversion failed")

            if progress_callback:
                progress_callback(30)

            # Step 2: Write ASS subtitles
            self._write_ass_subs(transcript, ass_path)

            if progress_callback:
                progress_callback(50)

            # Step 3: Burn subtitles with libass
            print(f"[ffmpeg] Burning ASS subtitles: {ass_path} -> {output_path}")
            cmd_burn = [
                "ffmpeg", "-y",
                "-i", portrait_video_path,
                "-vf", f"ass={ass_path}",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-b:v", self.bitrate,
                "-c:a", "aac",
                output_path
            ]

            proc2 = subprocess.run(cmd_burn, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc2.returncode != 0:
                print(f"[ffmpeg] Burn subtitles failed: {proc2.stderr.decode('utf-8', errors='ignore')}")
                raise RuntimeError("ffmpeg burn subtitles failed")

            if progress_callback:
                progress_callback(100)

            return output_path

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def render_with_moviepy(
        self,
        clip_path: str,
        transcript: dict,
        output_path: str,
        progress_callback: Callable[[float], None] = None
    ) -> str:
        """Fallback render using MoviePy (when pycaps unavailable)."""
        
        style = self.moviepy_style
        
        clip = VideoFileClip(clip_path)
        final_duration = min(clip.duration, 55)
        
        clip = clip.subclipped(0, final_duration)
        clip = self.resize_clip_to_fill(clip, self.width, self.height)
        
        layers = [clip]
        
        # Add captions
        segments = transcript.get("segments", [])
        if segments:
            caption_clips = self._create_moviepy_captions(segments, final_duration, style)
            layers.extend(caption_clips)
        
        if progress_callback:
            progress_callback(50)

        mem_before_comp = get_memory_mb()
        if mem_before_comp:
            print(f"[moviepy] Memory before composing clips: {mem_before_comp} MB")

        final = CompositeVideoClip(layers, size=(self.width, self.height))
        
        if clip.audio:
            final = final.with_audio(clip.audio)
        
        final = final.with_duration(final_duration)
        
        print(f"[moviepy] Writing final video to {output_path} (preset=ultrafast, threads=1)")
        final.write_videofile(
            output_path,
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            bitrate=self.bitrate,
            preset="ultrafast",
            threads=1,
            logger=None
        )
        
        clip.close()
        final.close()
        
        if progress_callback:
            progress_callback(100)
        
        return output_path
    
    def _create_moviepy_captions(
        self,
        segments: List[Dict],
        video_duration: float,
        style: dict
    ) -> List:
        """Create captions using MoviePy (fallback method)."""
        
        all_words = []
        for seg in segments:
            if "words" in seg and seg["words"]:
                all_words.extend(seg["words"])
        
        if all_words:
            return self._create_realtime_captions(all_words, video_duration, style)
        
        # Fallback to segment-level timing
        return self._create_segment_captions(segments, video_duration, style)
    
    def _create_realtime_captions(
        self,
        words: List[Dict],
        video_duration: float,
        style: dict
    ) -> List:
        """Create REAL-TIME captions using word-level timestamps."""
        if not words:
            return []
        
        all_clips = []
        y_position = int(self.height * style["y_position"])
        words_per_group = style["words_per_group"]
        
        i = 0
        group_index = 0
        
        while i < len(words):
            group = words[i:i + words_per_group]
            if not group:
                break
            
            group_start = max(0, group[0]["start"] + self.caption_time_offset)
            group_end = max(0, group[-1]["end"] + self.caption_time_offset)
            
            if group_start >= video_duration:
                break
            
            group_end = min(group_end, video_duration)
            group_duration = group_end - group_start
            
            if group_duration <= 0:
                i += words_per_group
                continue
            
            # Calculate width for centering
            temp_clips = []
            total_width = 0
            text_height = int(style["font_size"] * 1.5)
            
            for w in group:
                temp = TextClip(
                    text=w["word"].upper() + " ",
                    font_size=style["font_size"],
                    color="white",
                    font=style["font"],
                    size=(None, text_height),
                    method="label"
                )
                temp_clips.append((w["word"], temp, temp.w))
                total_width += temp.w
            
            start_x = (self.width - total_width) // 2
            x_offset = start_x
            
            for idx, (word, temp, width) in enumerate(temp_clips):
                word_clips = self._create_word_clip(
                    word,
                    duration=group_duration,
                    start_time=group_start,
                    x_position=x_offset,
                    y_position=y_position,
                    word_index=group_index * words_per_group + idx,
                    style=style
                )
                all_clips.extend(word_clips)
                x_offset += width
                temp.close()
            
            group_index += 1
            i += words_per_group
        
        return all_clips
    
    def _create_segment_captions(
        self,
        segments: List[Dict],
        video_duration: float,
        style: dict
    ) -> List:
        """Create captions from segment-level timing (fallback)."""
        all_clips = []
        y_position = int(self.height * style["y_position"])
        words_per_group = style["words_per_group"]
        global_word_index = 0
        
        for segment in segments:
            start_time = max(0, segment.get("start", 0) + self.caption_time_offset)
            end_time = max(0, segment.get("end", 0) + self.caption_time_offset)
            text = segment.get("text", "").strip()
            
            if start_time >= video_duration:
                continue
            
            end_time = min(end_time, video_duration)
            duration = end_time - start_time
            
            if duration <= 0 or not text:
                continue
            
            words = text.split()
            if not words:
                continue
            
            time_per_word = duration / len(words)
            
            for i in range(0, len(words), words_per_group):
                group = words[i:i + words_per_group]
                group_start = start_time + (i * time_per_word)
                group_duration = time_per_word * len(group)
                
                if group_start >= video_duration:
                    break
                group_duration = min(group_duration, video_duration - group_start)
                
                temp_clips = []
                total_width = 0
                
                for word in group:
                    temp = TextClip(
                        text=word.upper() + " ",
                        font_size=style["font_size"],
                        color="white",
                        font=style["font"],
                        method="label"
                    )
                    temp_clips.append((word, temp, temp.w))
                    total_width += temp.w
                
                start_x = (self.width - total_width) // 2
                x_offset = start_x
                
                for word, temp, width in temp_clips:
                    word_clips = self._create_word_clip(
                        word,
                        duration=group_duration,
                        start_time=group_start,
                        x_position=x_offset,
                        y_position=y_position,
                        word_index=global_word_index,
                        style=style
                    )
                    all_clips.extend(word_clips)
                    x_offset += width
                    global_word_index += 1
                    temp.close()
        
        return all_clips
    
    def _create_word_clip(
        self,
        word: str,
        duration: float,
        start_time: float,
        x_position: int,
        y_position: int,
        word_index: int,
        style: dict
    ) -> List:
        """Create a single word clip with shadow and dynamic color."""
        word_upper = word.upper()
        
        # Get color - keyword override or rotation
        keyword_color = self.get_keyword_color(word)
        if keyword_color:
            color = keyword_color
        else:
            color = style["color_rotation"][word_index % len(style["color_rotation"])]
        
        clips = []
        text_height = int(style["font_size"] * 1.5)
        
        # Shadow
        if style["shadow_offset"] > 0:
            shadow = TextClip(
                text=word_upper,
                font_size=style["font_size"],
                color="#333333",
                font=style["font"],
                size=(None, text_height),
                method="label"
            )
            shadow = shadow.with_duration(duration)
            shadow = shadow.with_start(start_time)
            shadow = shadow.with_position((
                x_position + style["shadow_offset"],
                y_position + style["shadow_offset"]
            ))
            clips.append(shadow)
        
        # Main text
        main_text = TextClip(
            text=word_upper,
            font_size=style["font_size"],
            color=color,
            stroke_color="black",
            stroke_width=style["stroke_width"],
            font=style["font"],
            size=(None, text_height),
            method="label"
        )
        main_text = main_text.with_duration(duration)
        main_text = main_text.with_start(start_time)
        main_text = main_text.with_position((x_position, y_position))
        clips.append(main_text)
        
        return clips
    
    def render(
        self,
        clip_path: str,
        transcript: dict,
        output_path: str,
        progress_callback: Callable[[float], None] = None
    ) -> str:
        """
        Render complete video with animated captions.
        
        Uses pycaps if available for CSS-styled animations,
        falls back to MoviePy otherwise.
        
        Args:
            clip_path: Path to Twitch clip
            transcript: Whisper transcription dict with segments
            output_path: Where to save the rendered video
            progress_callback: Optional callback(0-100) for progress updates
        
        Returns:
            Path to rendered video
        """
        if PYCAPS_AVAILABLE:
            print(f"[Renderer] Using pycaps with style: {self.caption_style}")
            try:
                return self.render_with_pycaps(
                    clip_path, transcript, output_path, progress_callback
                )
            except Exception as e:
                print(f"[Renderer] pycaps failed, falling back to MoviePy: {e}")
        else:
            if PYCAPS_ERROR:
                print(f"[Renderer] pycaps unavailable: {PYCAPS_ERROR}")
            print(f"[Renderer] Using MoviePy fallback with style: {self.caption_style}")

        # Prefer ffmpeg ASS subtitle pipeline when available (lower Python memory)
        try:
            if shutil.which("ffmpeg"):
                print("[Renderer] Attempting ffmpeg ASS subtitle render (low-memory)")
                return self.render_with_ffmpeg_ass(clip_path, transcript, output_path, progress_callback)
        except Exception as e:
            print(f"[Renderer] ffmpeg ASS render failed, falling back: {e}")

        # Final fallback to MoviePy
        return self.render_with_moviepy(
            clip_path, transcript, output_path, progress_callback
        )
