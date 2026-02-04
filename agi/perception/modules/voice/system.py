
import speech_recognition as sr
from typing import Any, Dict, Optional
from agi.perception.base import PerceptionModule, PerceptionMetadata

class VoicePerception(PerceptionModule):
    """
    Senses voice commands using the Microphone and SpeechRecognition library.
    """
    
    @property
    def metadata(self) -> PerceptionMetadata:
        return PerceptionMetadata(
            name="voice_listener",
            description="Listens for speech and converts it to text.",
            version="1.0.0"
        )
        
    def __init__(self, config):
        super().__init__(config)
        self.recognizer = sr.Recognizer()
        self.microphone = None

    async def connect(self) -> bool:
        try:
            # Check if microphone is available
            self.microphone = sr.Microphone()
            # We don't enter the context manager here, we do it per perceive call
            # or keep it open if streaming. For now, perceive will open it.
            self.connected = True
            return True
        except Exception as e:
            if self.config.verbose:
                print(f"[VoicePerception] Failed to connect to microphone: {e}")
            self.connected = False
            return False

    async def perceive(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Listens for a single sentence/command.
        
        Args:
            timeout (int): Seconds to wait for speech start.
            phrase_time_limit (int): Max seconds for a phrase.
        """
        if not self.connected:
            await self.connect()
            if not self.connected:
                return {"error": "Microphone not available"}
        
        timeout = kwargs.get("timeout", 5)
        phrase_time_limit = kwargs.get("phrase_time_limit", 10)
        
        try:
            with self.microphone as source:
                if self.config.verbose:
                    print("[VoicePerception] Adjusting for ambient noise... (Speak now)")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                if self.config.verbose:
                    print("[VoicePerception] Listening...")
                
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                
                if self.config.verbose:
                    print("[VoicePerception] Processing audio...")
                
                # Recognize speech using Google Web Speech API
                text = self.recognizer.recognize_google(audio)
                
                if self.config.verbose:
                    print(f"[VoicePerception] Heard: '{text}'")
                
                return {
                    "text": text,
                    "provider": "google",
                    "status": "success"
                }
                
        except sr.WaitTimeoutError:
            return {"status": "timeout", "text": ""}
        except sr.UnknownValueError:
            return {"status": "unintelligible", "text": ""}
        except sr.RequestError as e:
            return {"status": "error", "error": f"API unavailable: {e}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
