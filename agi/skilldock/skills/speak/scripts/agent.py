
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
            category="communication",
            sub_category="voice",
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
            from agi.utils.audio_manager import audio_manager
            
            async def play_audio(txt):
                # 1. Generate Audio file
                tts = gTTS(text=txt, lang=lang)
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                    p = fp.name
                tts.save(p)
                
                # 2. Play Audio (MacOS afplay)
                if self.agi_config and getattr(self.agi_config, 'verbose', False):
                    print(f"[SpeakSkill] Playing audio: {txt[:50]}...")
                
                try:
                    process = await asyncio.create_subprocess_exec("afplay", p)
                    await process.wait()
                finally:
                    try:
                        os.remove(p)
                    except:
                        pass

            # Use the manager to queue and speak
            await audio_manager.speak(text, play_audio)
            
            return {
                "status": "success",
                "message": "Audio played successfully"
            }
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}
