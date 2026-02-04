
import os
import tempfile
import subprocess
from typing import Any, Dict, List
from gtts import gTTS
from agi.skilldock.base import Skill, SkillMetadata
import asyncio

class SpeakSkill(Skill):
    """
    Skill to synthesize speech from text using Google Text-to-Speech (gTTS).
    """
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="speak",
            description="Converts text to speech and plays it locally.",
            category="output",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to speak"},
                    "lang": {"type": "string", "description": "Language code (default: 'en')", "default": "en"}
                },
                "required": ["text"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "file_path": {"type": "string"}
                }
            }
        )

    async def execute(self, **kwargs) -> Dict[str, Any]:
        text = kwargs.get("text")
        lang = kwargs.get("lang", "en")
        
        if not text:
             return {"error": "No text provided"}
             
        try:
            # 1. Generate Audio file
            tts = gTTS(text=text, lang=lang)
            
            # Create a temporary file
            # We use a fixed temp dir or system temp
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                temp_path = fp.name
                
            tts.save(temp_path)
            
            # 2. Play Audio (MacOS specific 'afplay')
            # For cross-platform, we'd check OS, but task specified mac.
            if self.agi_config and getattr(self.agi_config, 'verbose', False):
                print(f"[SpeakSkill] Playing audio: {text[:50]}...")
            
            # Set global speaking flag and notify listeners (for echo cancellation)
            if self.agi_config:
                self.agi_config.is_speaking = True
                if hasattr(self.agi_config, 'on_speak_callback') and self.agi_config.on_speak_callback:
                    try:
                        self.agi_config.on_speak_callback(text)
                    except:
                        pass
                
            try:
                process = await asyncio.create_subprocess_exec("afplay", temp_path)
                await process.wait()
            finally:
                if self.agi_config:
                    self.agi_config.is_speaking = False
            
            # Clean up? Maybe keep for a bit or return path.
            # We'll return path and let system clean up or user handle it.
            
            return {
                "status": "success",
                "file_path": temp_path,
                "message": "Audio played successfully"
            }
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}
