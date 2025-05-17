"""Audio transcription service.

Transcribes audio from various sources including:
- Audio files (mp3, wav, m4a, etc.)
- Video files (extracting audio)
- Voice messages

Uses OpenAI's Whisper model for transcription.
"""

import asyncio
import os
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

# Import optional libraries with graceful fallback
try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


class AudioTranscriber:
    """Transcribes audio using OpenAI's Whisper model."""
    
    def __init__(self, model_size: str = "base"):
        """Initialize the audio transcriber.
        
        Args:
            model_size: Whisper model size - "tiny", "base", "small", "medium", "large"
        """
        self.model_size = model_size
        self.model = None
        self._check_dependencies()
        self._load_model()
    
    def _check_dependencies(self):
        """Check available dependencies and warn about missing ones."""
        missing = []
        
        if not HAS_WHISPER:
            missing.append("openai-whisper")
        if not HAS_PYDUB:
            missing.append("pydub")
        if not HAS_TORCH:
            missing.append("torch")
            
        if missing:
            print(f"Warning: Missing dependencies: {', '.join(missing)}")
            print("Install them for audio transcription capabilities:")
            print(f"pip install {' '.join(missing)}")
            if 'pydub' in missing:
                print("Note: pydub also requires ffmpeg to be installed on your system")
    
    def _load_model(self):
        """Load the Whisper model."""
        if not HAS_WHISPER:
            print("Whisper not available. Cannot load model.")
            return
            
        try:
            # Check if GPU is available
            device = "cuda" if HAS_TORCH and torch.cuda.is_available() else "cpu"
            print(f"Loading Whisper model '{self.model_size}' on {device}...")
            
            self.model = whisper.load_model(self.model_size, device=device)
            print(f"Whisper model loaded successfully on {device}")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            self.model = None
    
    def _convert_audio_format(self, audio_path: str) -> Optional[str]:
        """Convert audio to a format Whisper can handle (16kHz mono WAV)."""
        if not HAS_PYDUB:
            print("pydub not available. Cannot convert audio format.")
            return None
            
        try:
            # Load audio
            audio = AudioSegment.from_file(audio_path)
            
            # Convert to mono if stereo
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # Set sample rate to 16kHz
            audio = audio.set_frame_rate(16000)
            
            # Export as WAV
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
                audio.export(tmp_path, format="wav")
                return tmp_path
                
        except Exception as e:
            print(f"Error converting audio format: {e}")
            return None
    
    def _extract_audio_from_video(self, video_path: str) -> Optional[str]:
        """Extract audio from video file."""
        if not HAS_PYDUB:
            print("pydub not available. Cannot extract audio from video.")
            return None
            
        try:
            # Load video and extract audio
            video = AudioSegment.from_file(video_path)
            
            # Export as WAV
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
                video.export(tmp_path, format="wav")
                return tmp_path
                
        except Exception as e:
            print(f"Error extracting audio from video: {e}")
            return None
    
    def _get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from audio file."""
        metadata = {
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
            "file_extension": Path(file_path).suffix.lower()
        }
        
        if HAS_PYDUB:
            try:
                audio = AudioSegment.from_file(file_path)
                metadata.update({
                    "duration_seconds": len(audio) / 1000.0,
                    "channels": audio.channels,
                    "sample_rate": audio.frame_rate,
                    "bits_per_sample": audio.sample_width * 8
                })
            except Exception as e:
                print(f"Error extracting audio metadata: {e}")
                
        return metadata
    
    async def transcribe(self, 
                        file_path: str,
                        language: Optional[str] = None,
                        task: str = "transcribe") -> Dict[str, Any]:
        """Transcribe audio file using Whisper.
        
        Args:
            file_path: Path to audio or video file
            language: Language code (e.g., "en", "es"). None for auto-detection
            task: "transcribe" or "translate" (to English)
            
        Returns:
            Dict with transcription results
        """
        result = {
            "file_path": file_path,
            "transcribed_at": datetime.utcnow().isoformat(),
            "metadata": self._get_file_metadata(file_path),
            "transcription": {},
            "status": "pending"
        }
        
        if not self.model:
            result["status"] = "error"
            result["error"] = "Whisper model not loaded"
            return result
        
        try:
            # Check if file is video and extract audio
            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
            if any(file_path.lower().endswith(ext) for ext in video_extensions):
                print("Extracting audio from video...")
                audio_path = self._extract_audio_from_video(file_path)
                if not audio_path:
                    raise Exception("Failed to extract audio from video")
                temp_file = audio_path
            else:
                # Convert audio to proper format
                audio_path = self._convert_audio_format(file_path)
                if not audio_path:
                    # Try to use original file
                    audio_path = file_path
                temp_file = audio_path if audio_path != file_path else None
            
            # Transcribe using Whisper
            print(f"Transcribing audio{' (language: ' + language + ')' if language else ''}...")
            
            options = {
                "task": task,
                "language": language,
                "fp16": False  # Disable FP16 for compatibility
            }
            
            # Run transcription
            transcription = self.model.transcribe(audio_path, **options)
            
            # Extract results
            result["transcription"] = {
                "text": transcription.get("text", "").strip(),
                "language": transcription.get("language", ""),
                "segments": []
            }
            
            # Add segment-level information if available
            if "segments" in transcription:
                for segment in transcription["segments"]:
                    result["transcription"]["segments"].append({
                        "id": segment.get("id"),
                        "start": segment.get("start"),
                        "end": segment.get("end"),
                        "text": segment.get("text", "").strip(),
                        "confidence": segment.get("confidence")
                    })
            
            result["status"] = "completed"
            result["metadata"]["detected_language"] = transcription.get("language", "")
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"Error during transcription: {e}")
        
        finally:
            # Clean up temporary file
            if 'temp_file' in locals() and temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        
        return result
    
    def transcribe_sync(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Synchronous version of transcribe for compatibility."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.transcribe(file_path, **kwargs))
        finally:
            loop.close()
    
    async def batch_transcribe(self, 
                              file_paths: List[str],
                              **kwargs) -> List[Dict[str, Any]]:
        """Transcribe multiple audio files in batch."""
        tasks = [self.transcribe(path, **kwargs) for path in file_paths]
        return await asyncio.gather(*tasks)
    
    def get_available_models(self) -> List[str]:
        """Get list of available Whisper model sizes."""
        return ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages for transcription."""
        if not HAS_WHISPER:
            return []
            
        # This is a subset of Whisper's supported languages
        return [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr",
            "pl", "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi",
            "he", "uk", "el", "ms", "cs", "ro", "da", "hu", "ta", "no",
            "th", "ur", "hr", "bg", "lt", "la", "mi", "ml", "cy", "sk",
            "te", "fa", "lv", "bn", "sr", "az", "sl", "kn", "et", "mk",
            "br", "eu", "is", "hy", "ne", "mn", "bs", "kk", "sq", "sw",
            "gl", "mr", "pa", "si", "km", "sn", "yo", "so", "af", "oc",
            "ka", "be", "tg", "sd", "gu", "am", "yi", "lo", "uz", "fo",
            "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my", "bo", "tl",
            "mg", "as", "tt", "haw", "ln", "ha", "ba", "jw", "su"
        ]


# Example usage
if __name__ == "__main__":
    transcriber = AudioTranscriber(model_size="base")
    
    # Test with a sample audio file
    test_file = "sample_audio.mp3"  # Replace with actual file
    
    # Check supported features
    print(f"Available models: {transcriber.get_available_models()}")
    print(f"Supported languages: {len(transcriber.get_supported_languages())} languages")
    
    # Transcribe if file exists
    if os.path.exists(test_file):
        # Async usage
        async def test_async():
            result = await transcriber.transcribe(test_file)
            print(f"Status: {result['status']}")
            if result['status'] == 'completed':
                print(f"Text: {result['transcription']['text'][:200]}...")
                print(f"Language: {result['transcription']['language']}")
        
        # Sync usage
        result = transcriber.transcribe_sync(test_file)
        print(f"\nSync transcription - Status: {result['status']}")
        
        # Run async test
        asyncio.run(test_async())
    else:
        print(f"Test file '{test_file}' not found")