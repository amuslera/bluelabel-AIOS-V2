"""
Simple translation agent for converting Spanish to English
"""
import logging
from typing import Dict, Any
import openai

from agents.base_agent import BaseAgent
from core.config import config

logger = logging.getLogger(__name__)


class TranslationAgent(BaseAgent):
    """Agent for translating text between languages"""
    
    def __init__(self):
        super().__init__()
        self.name = "TranslationAgent"
        self.description = "Translates text between Spanish and English"
        self.client = openai.AsyncOpenAI(api_key=config.llm.openai_api_key)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate text from Spanish to English
        
        Args:
            input_data: {
                "text": str,
                "source_language": str,  # "es" or "en"
                "target_language": str   # "es" or "en"
            }
        
        Returns:
            {
                "translation": str,
                "success": bool,
                "error": Optional[str]
            }
        """
        try:
            text = input_data.get("text", "").strip()
            if not text:
                return {"translation": "", "success": True, "error": None}
            
            source_lang = input_data.get("source_language", "es")
            target_lang = input_data.get("target_language", "en")
            
            # If source and target are the same, return original
            if source_lang == target_lang:
                return {"translation": text, "success": True, "error": None}
            
            # Translate using GPT
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"Translate from {source_lang} to {target_lang}. Return only the translation, no explanations."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            translation = response.choices[0].message.content.strip()
            
            return {
                "translation": translation,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {
                "translation": text,  # Return original on error
                "success": False,
                "error": str(e)
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "supported_languages": ["en", "es"],
            "supports_bidirectional": True
        }
    
    async def health_check(self) -> bool:
        return bool(config.llm.openai_api_key)