"""
Transcription agent using OpenAI Whisper API.
Handles audio-to-text conversion with language detection.
"""
import os
import asyncio
import aiofiles
from typing import Dict, Any, Optional, Tuple
import openai
from pathlib import Path
import logging

from agents.base_agent import BaseAgent
from core.config import config

logger = logging.getLogger(__name__)


class TranscriptionAgent(BaseAgent):
    """Agent for transcribing audio files using OpenAI Whisper"""
    
    def __init__(self):
        super().__init__()
        self.name = "TranscriptionAgent"
        self.description = "Transcribes audio files to text using OpenAI Whisper API"
        self.client = openai.AsyncOpenAI(api_key=config.llm.openai_api_key)
        
        # Supported audio formats
        self.supported_formats = {
            'mp3', 'mp4', 'm4a', 'wav', 'webm', 'flac', 'oga', 'ogg'
        }
        
        # Maximum file size (25MB as per OpenAI limit)
        self.max_file_size = 25 * 1024 * 1024
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process audio file for transcription.
        
        Args:
            input_data: {
                "audio_file_path": str,
                "language": Optional[str],  # "en" or "es" or None for auto-detect
                "prompt": Optional[str]     # Optional prompt to guide transcription
            }
        
        Returns:
            {
                "transcription": str,
                "language": str,
                "confidence": float,
                "duration": float,
                "segments": List[Dict],  # Optional detailed segments
                "success": bool,
                "error": Optional[str]
            }
        """
        try:
            audio_file_path = input_data.get("audio_file_path")
            if not audio_file_path:
                return self._error_response("audio_file_path is required")
            
            # Validate file exists
            if not os.path.exists(audio_file_path):
                return self._error_response(f"Audio file not found: {audio_file_path}")
            
            # Validate file format
            file_extension = Path(audio_file_path).suffix.lower().lstrip('.')
            if file_extension not in self.supported_formats:
                return self._error_response(
                    f"Unsupported audio format: {file_extension}. "
                    f"Supported formats: {', '.join(self.supported_formats)}"
                )
            
            # Validate file size
            file_size = os.path.getsize(audio_file_path)
            if file_size > self.max_file_size:
                return self._error_response(
                    f"File too large: {file_size / (1024*1024):.1f}MB. "
                    f"Maximum allowed: {self.max_file_size / (1024*1024)}MB"
                )
            
            logger.info(f"Starting transcription for {audio_file_path} ({file_size} bytes)")
            
            # Perform transcription
            result = await self._transcribe_audio(
                audio_file_path=audio_file_path,
                language=input_data.get("language"),
                prompt=input_data.get("prompt")
            )
            
            logger.info(f"Transcription completed for {audio_file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return self._error_response(f"Transcription failed: {str(e)}")
    
    async def _transcribe_audio(
        self, 
        audio_file_path: str, 
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform the actual transcription using OpenAI Whisper API"""
        
        try:
            # Read audio file content into memory
            async with aiofiles.open(audio_file_path, 'rb') as audio_file:
                audio_content = await audio_file.read()
            
            # Use regular file opening for OpenAI API (which expects standard file objects)
            with open(audio_file_path, 'rb') as audio_file:
                # Prepare transcription parameters
                params = {
                    "model": "whisper-1",
                    "response_format": "verbose_json",  # Get detailed response with timestamps
                }
                
                # Add language if specified
                if language:
                    params["language"] = language
                
                # Add prompt if specified (helps with context and accuracy)
                if prompt:
                    params["prompt"] = prompt
                
                # Call OpenAI Whisper API
                logger.debug(f"Calling Whisper API with params: {params}")
                response = await self.client.audio.transcriptions.create(
                    file=audio_file,
                    **params
                )
                
                # Extract results
                transcription = response.text
                language_detected = getattr(response, 'language', 'unknown')
                duration = getattr(response, 'duration', 0.0)
                segments = getattr(response, 'segments', [])
                
                # Calculate confidence score (average of segment confidences if available)
                confidence = self._calculate_confidence(segments)
                
                logger.info(
                    f"Transcription successful: {len(transcription)} chars, "
                    f"language={language_detected}, confidence={confidence:.2f}"
                )
                
                return {
                    "transcription": transcription,
                    "language": language_detected,
                    "confidence": confidence,
                    "duration": duration,
                    "segments": segments,
                    "success": True,
                    "error": None
                }
                
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return self._error_response(f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during transcription: {e}")
            return self._error_response(f"Transcription error: {e}")
    
    def _calculate_confidence(self, segments: list) -> float:
        """Calculate average confidence from segments"""
        if not segments:
            return 0.8  # Default confidence if no segments available
        
        confidences = []
        for segment in segments:
            # Segments might have different confidence field names
            if hasattr(segment, 'avg_logprob'):
                # Convert log probability to confidence (rough approximation)
                confidence = min(1.0, max(0.0, (segment.avg_logprob + 1.0)))
                confidences.append(confidence)
            elif hasattr(segment, 'confidence'):
                confidences.append(segment.confidence)
        
        if confidences:
            return sum(confidences) / len(confidences)
        else:
            return 0.8  # Default confidence
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "transcription": "",
            "language": "unknown",
            "confidence": 0.0,
            "duration": 0.0,
            "segments": [],
            "success": False,
            "error": error_message
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities"""
        return {
            "name": self.name,
            "description": self.description,
            "supported_formats": list(self.supported_formats),
            "max_file_size_mb": self.max_file_size / (1024 * 1024),
            "supports_language_detection": True,
            "supported_languages": ["en", "es", "auto-detect"],
            "provides_timestamps": True,
            "provides_confidence_scores": True
        }
    
    async def health_check(self) -> bool:
        """Check if the agent is healthy and can process requests"""
        try:
            # Check if OpenAI API key is configured
            if not config.llm.openai_api_key:
                logger.error("OpenAI API key not configured")
                return False
            
            # Try a simple API call to verify connectivity
            # Note: This doesn't actually make a call to avoid charges
            # In production, you might want to implement a cheaper health check
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False