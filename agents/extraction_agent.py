"""
Data extraction agent using LLM to parse meeting transcripts.
Extracts structured data from voice memo transcriptions.
"""
import json
import logging
from typing import Dict, Any, Optional
import openai
from datetime import datetime

from agents.base_agent import BaseAgent
from core.config import config

logger = logging.getLogger(__name__)


class ExtractionAgent(BaseAgent):
    """Agent for extracting structured data from meeting transcripts"""
    
    def __init__(self):
        super().__init__()
        self.name = "ExtractionAgent"
        self.description = "Extracts structured data from meeting transcripts using LLM"
        self.client = openai.AsyncOpenAI(api_key=config.llm.openai_api_key)
        
        # Extraction prompts for different languages
        self.extraction_prompts = {
            "en": self._get_english_prompt(),
            "es": self._get_spanish_prompt(),
            "default": self._get_english_prompt()
        }
    
    def _get_english_prompt(self) -> str:
        """English extraction prompt template"""
        return """
You are an AI assistant that extracts structured information from meeting transcripts. 
Extract the following information from this voice memo recorded after a client meeting:

Required fields:
- Name: Person's full name
- Company: Company or organization name  
- Position: Their role, title, or position
- Discussion: Brief summary of what was discussed (2-3 sentences)
- Contact Type: Must be exactly "Prospective" or "Existing"
- Priority: Must be exactly "High", "Medium", or "Low" 
- Action Items: List of specific follow-up actions or next steps

Instructions:
1. Extract information exactly as mentioned in the transcript
2. If information is not clearly stated, use "Not specified" 
3. For Contact Type, if unclear, infer from context (new leads = "Prospective", existing relationships = "Existing")
4. For Priority, infer from urgency indicators, deal size mentions, or importance cues
5. Action Items should be specific, actionable tasks
6. Return ONLY valid JSON with exact field names as shown below

Expected JSON format:
{{
  "name": "string",
  "company": "string", 
  "position": "string",
  "discussion": "string",
  "contact_type": "Prospective" or "Existing",
  "priority": "High" or "Medium" or "Low",
  "action_items": ["action 1", "action 2"]
}}

Transcript to analyze:
{transcript}
"""
    
    def _get_spanish_prompt(self) -> str:
        """Spanish extraction prompt template"""
        return """
Eres un asistente de IA que extrae información estructurada de transcripciones de reuniones.
Extrae la siguiente información de esta nota de voz grabada después de una reunión con un cliente:

Campos requeridos:
- Name: Nombre completo de la persona
- Company: Nombre de la empresa u organización
- Position: Su rol, título o posición
- Discussion: Resumen breve de lo que se discutió (2-3 oraciones)
- Contact Type: Debe ser exactamente "Prospective" o "Existing" 
- Priority: Debe ser exactamente "High", "Medium", o "Low"
- Action Items: Lista de acciones específicas de seguimiento o próximos pasos

Instrucciones:
1. Extrae información exactamente como se menciona en la transcripción
2. Si la información no está claramente indicada, usa "Not specified"
3. Para Contact Type, si no está claro, infiere del contexto (nuevos prospectos = "Prospective", relaciones existentes = "Existing")
4. Para Priority, infiere de indicadores de urgencia, menciones de tamaño del negocio, o señales de importancia
5. Action Items deben ser tareas específicas y accionables
6. Devuelve SOLO JSON válido con los nombres de campos exactos como se muestra abajo

Formato JSON esperado:
{{
  "name": "string",
  "company": "string",
  "position": "string", 
  "discussion": "string",
  "contact_type": "Prospective" or "Existing",
  "priority": "High" or "Medium" or "Low",
  "action_items": ["acción 1", "acción 2"]
}}

Transcripción a analizar:
{transcript}
"""
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from transcript.
        
        Args:
            input_data: {
                "transcription": str,
                "language": Optional[str],  # "en", "es", or auto-detect
                "context": Optional[str]   # Additional context if available
            }
        
        Returns:
            {
                "extracted_data": Dict[str, Any],
                "confidence": float,
                "language_used": str,
                "success": bool,
                "error": Optional[str]
            }
        """
        try:
            transcription = input_data.get("transcription", "").strip()
            if not transcription:
                return self._error_response("transcription is required")
            
            language = input_data.get("language", "en").lower()
            context = input_data.get("context", "")
            
            logger.info(f"Starting data extraction for {len(transcription)} chars in {language}")
            
            # Perform extraction
            result = await self._extract_data(
                transcription=transcription,
                language=language,
                context=context
            )
            
            logger.info(f"Data extraction completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            return self._error_response(f"Data extraction failed: {str(e)}")
    
    async def _extract_data(
        self, 
        transcription: str, 
        language: str = "en",
        context: str = ""
    ) -> Dict[str, Any]:
        """Perform the actual data extraction using LLM"""
        
        try:
            # Select appropriate prompt based on language
            prompt_template = self.extraction_prompts.get(language, self.extraction_prompts["default"])
            
            # Add context if provided
            full_transcript = transcription
            if context:
                full_transcript = f"Context: {context}\n\nTranscript: {transcription}"
            
            # Format the prompt
            prompt = prompt_template.format(transcript=full_transcript)
            
            logger.debug(f"Using prompt for language: {language}")
            
            # Use simpler prompt for better JSON compliance
            simple_prompt = f"""Extract contact information from this meeting transcript and return ONLY valid JSON.

Transcript: {full_transcript}

IMPORTANT: 
- Return ONLY the JSON object, no additional text
- Use proper JSON formatting with double quotes
- No newlines within string values
- All text in English, even if transcript is in Spanish
- If there are multiple people mentioned, return an array of contacts
- If only one person is mentioned, still return an array with one contact

JSON format for multiple contacts:
{{
  "contacts": [
    {{
      "name": "person full name",
      "company": "company name",
      "position": "job title",
      "discussion": "brief summary in one sentence about this person",
      "contact_type": "Prospective",
      "priority": "Medium",
      "action_items": ["specific action 1", "specific action 2"]
    }},
    {{
      "name": "another person full name",
      "company": "company name",
      "position": "job title",
      "discussion": "brief summary in one sentence about this person",
      "contact_type": "Existing",
      "priority": "High",
      "action_items": ["specific action 3", "specific action 4"]
    }}
  ]
}}"""

            # Call LLM API
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use more reliable model for JSON
                messages=[
                    {
                        "role": "system", 
                        "content": "Return only valid JSON. No additional text or explanations."
                    },
                    {
                        "role": "user", 
                        "content": simple_prompt
                    }
                ],
                temperature=0.0,  # Deterministic output
                max_tokens=500,
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            
            # Extract and parse the JSON response
            raw_response = response.choices[0].message.content
            logger.debug(f"Raw LLM response: {repr(raw_response)}")
            
            # Clean and parse JSON
            try:
                # Try to parse JSON directly first
                extracted_data = json.loads(raw_response)
            except json.JSONDecodeError as e:
                # If direct parsing fails, try to clean the response
                logger.warning(f"Direct JSON parsing failed: {e}")
                cleaned_response = self._clean_json_response(raw_response)
                logger.debug(f"Cleaned LLM response: {repr(cleaned_response)}")
                extracted_data = json.loads(cleaned_response)
            
            # Validate and clean the extracted data
            cleaned_data = self._validate_and_clean_data(extracted_data)
            
            # Calculate confidence based on data completeness
            confidence = self._calculate_extraction_confidence(cleaned_data, transcription)
            
            logger.info(f"Data extraction successful with confidence: {confidence:.2f}")
            
            return {
                "extracted_data": cleaned_data,
                "confidence": confidence,
                "language_used": language,
                "success": True,
                "error": None
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Raw response was: {repr(raw_response)}")
            # Try to provide a fallback with basic extraction
            try:
                fallback_data = self._extract_fallback_data(transcription)
                return {
                    "extracted_data": fallback_data,
                    "confidence": 0.3,  # Low confidence for fallback
                    "language_used": language,
                    "success": True,
                    "error": f"JSON parsing failed, used fallback extraction: {e}"
                }
            except Exception as fallback_error:
                logger.error(f"Fallback extraction also failed: {fallback_error}")
                return self._error_response(f"Both JSON parsing and fallback extraction failed: {e}")
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return self._error_response(f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during extraction: {e}")
            return self._error_response(f"Extraction error: {e}")
    
    def _validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted data"""
        # Check if data contains multiple contacts
        if "contacts" in data and isinstance(data["contacts"], list):
            # Handle multiple contacts format
            cleaned_contacts = []
            for contact in data["contacts"]:
                cleaned_contact = self._clean_single_contact(contact)
                if cleaned_contact:  # Only add if we have valid data
                    cleaned_contacts.append(cleaned_contact)
            
            return {"contacts": cleaned_contacts}
        else:
            # Handle single contact format (backward compatibility)
            cleaned_contact = self._clean_single_contact(data)
            if cleaned_contact:
                return {"contacts": [cleaned_contact]}  # Convert to array format
            else:
                return {"contacts": []}
    
    def _clean_single_contact(self, contact_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Clean and validate a single contact"""
        cleaned = {}
        
        # Required string fields
        string_fields = ["name", "company", "position", "discussion"]
        for field in string_fields:
            value = contact_data.get(field, "").strip()
            cleaned[field] = value if value and value.lower() != "not specified" else None
        
        # Contact type validation
        contact_type = contact_data.get("contact_type", "").strip()
        if contact_type in ["Prospective", "Existing"]:
            cleaned["contact_type"] = contact_type
        else:
            cleaned["contact_type"] = None
        
        # Priority validation
        priority = contact_data.get("priority", "").strip()
        if priority in ["High", "Medium", "Low"]:
            cleaned["priority"] = priority
        else:
            cleaned["priority"] = "Medium"  # Default to medium if unclear
        
        # Action items validation
        action_items = contact_data.get("action_items", [])
        if isinstance(action_items, list):
            cleaned["action_items"] = [item.strip() for item in action_items if item.strip()]
        else:
            cleaned["action_items"] = []
        
        # Only return contact if we have at least a name
        if cleaned.get("name"):
            return cleaned
        else:
            return None
    
    def _clean_json_response(self, response: str) -> str:
        """Clean and fix common JSON formatting issues"""
        import re
        
        # Remove any content before the first {
        if '{' in response:
            start_idx = response.find('{')
            response = response[start_idx:]
        
        # Remove any content after the last }
        if '}' in response:
            end_idx = response.rfind('}')
            response = response[:end_idx + 1]
        
        # Fix common issues
        response = response.strip()
        
        # Remove potential markdown code block markers
        response = re.sub(r'^```json\s*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'\s*```$', '', response)
        
        # Fix newlines in JSON values that break parsing
        # Replace newlines within quoted strings with spaces
        response = re.sub(r'"([^"]*?)\n([^"]*?)"', r'"\1 \2"', response)
        
        # Remove standalone newlines that might break JSON structure
        response = re.sub(r'\n\s*"', r' "', response)
        response = re.sub(r'"\s*\n', r'" ', response)
        
        # Fix escaped quotes if needed
        response = response.replace('\\"', '"')
        
        # Ensure proper spacing around colons and commas
        response = re.sub(r'"\s*:\s*', r'": ', response)
        response = re.sub(r',\s*"', r', "', response)
        
        return response

    def _extract_fallback_data(self, transcription: str) -> Dict[str, Any]:
        """Simple fallback extraction when JSON parsing fails"""
        # Extract basic information using simple text parsing
        fallback_contact = {
            "name": None,
            "company": None,
            "position": None,
            "discussion": transcription[:200] + "..." if len(transcription) > 200 else transcription,
            "contact_type": "Prospective",  # Default
            "priority": "Medium",  # Default
            "action_items": []
        }
        
        # Simple name extraction (look for common patterns)
        import re
        
        # Look for "con [Name]" pattern in Spanish
        name_match = re.search(r'con\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', transcription)
        if name_match:
            fallback_contact["name"] = name_match.group(1)
        
        # Look for CEO, CTO, etc.
        if "CEO" in transcription:
            fallback_contact["position"] = "CEO"
        elif "CTO" in transcription:
            fallback_contact["position"] = "CTO"
        
        # Look for company names (capitalized words)
        company_match = re.search(r'proyecto\s+([A-Z][A-Z]+)', transcription)
        if company_match:
            fallback_contact["company"] = company_match.group(1)
        
        return {"contacts": [fallback_contact]}

    def _calculate_extraction_confidence(self, data: Dict[str, Any], transcript: str) -> float:
        """Calculate confidence score based on data completeness and quality"""
        
        # Base confidence
        confidence = 0.5
        
        # Handle multiple contacts format
        contacts = data.get("contacts", [])
        if not contacts:
            return 0.0
        
        # Calculate average confidence across all contacts
        total_confidence = 0.0
        for contact in contacts:
            contact_confidence = self._calculate_single_contact_confidence(contact, transcript)
            total_confidence += contact_confidence
        
        # Average confidence across contacts
        confidence = total_confidence / len(contacts)
        
        # Bonus for successfully extracting multiple contacts
        if len(contacts) > 1:
            confidence += 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_single_contact_confidence(self, contact: Dict[str, Any], transcript: str) -> float:
        """Calculate confidence score for a single contact"""
        confidence = 0.5
        
        # Check for presence of key fields
        key_fields = ["name", "company", "discussion"]
        filled_fields = sum(1 for field in key_fields if contact.get(field))
        confidence += (filled_fields / len(key_fields)) * 0.3
        
        # Check for specific required fields
        if contact.get("contact_type"):
            confidence += 0.1
        if contact.get("priority"):
            confidence += 0.05
        if contact.get("action_items"):
            confidence += 0.05
        
        # Penalize very short extractions
        if contact.get("discussion") and len(contact["discussion"]) < 20:
            confidence -= 0.1
        
        # Bonus for longer, detailed transcripts (indicates more information)
        if len(transcript) > 200:
            confidence += 0.05
        
        return confidence
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "extracted_data": {},
            "confidence": 0.0,
            "language_used": "unknown",
            "success": False,
            "error": error_message
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities"""
        return {
            "name": self.name,
            "description": self.description,
            "supported_languages": ["en", "es"],
            "extracted_fields": [
                "name", "company", "position", "discussion", 
                "contact_type", "priority", "action_items"
            ],
            "confidence_scoring": True,
            "structured_output": True
        }
    
    async def health_check(self) -> bool:
        """Check if the agent is healthy and can process requests"""
        try:
            # Check if OpenAI API key is configured
            if not config.llm.openai_api_key:
                logger.error("OpenAI API key not configured")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False