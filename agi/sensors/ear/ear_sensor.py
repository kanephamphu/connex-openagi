import threading
import time
import logging
from typing import Callable, Optional, Dict, Any

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

class VoiceEar:
    """
    The 'Ear' of the AGI. Continuous background sensor that listens for 
    voice commands and triggers the reflex layer.
    """
    def __init__(self, config, on_event_callback: Callable[[Dict[str, Any]], Any]):
        self.config = config
        self.on_event = on_event_callback
        self.running = False
        self._thread: Optional[threading.Thread] = None
        
        # Debounce Settings
        self.debounce_wait = 1.5 # Seconds of silence to wait before processing
        self.phrase_buffer = []
        self.last_speech_time = 0
        
        if SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 350 # Slightly higher to ignore faint noise
            self.recognizer.dynamic_energy_threshold = True
            # Wait 0.8s of silence before finishing an individual chunk
            self.recognizer.pause_threshold = 0.8 
            
            try:
                self.microphone = sr.Microphone()
            except Exception as e:
                print(f"[Ear] Microphone error: {e}")
                self.microphone = None
        else:
            self.recognizer = None
            self.microphone = None

    def _listen_loop(self):
        if not SPEECH_RECOGNITION_AVAILABLE or self.microphone is None:
            print("[Ear] CRITICAL: Ear is deaf (mic or lib missing).")
            return

        print("[Ear] Sensory module 'Ear' activated. Adjusting for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
            
        print(f"[Ear] Always listening (Debounce: {self.debounce_wait}s)...")
        
        while self.running:
            try:
                # 1. Check if we should flush due to timeout even BEFORE listening
                # This handles cases where we are just starting the loop
                if self.phrase_buffer and (time.time() - self.last_speech_time) >= self.debounce_wait:
                    self._flush_buffer()

                with self.microphone as source:
                    # Listen for a chunk. timeout=1 means if 0 sound for 1s, raise WaitTimeoutError
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=15)
                    
                if not self.running:
                    break
                
                try:
                    text = self.recognizer.recognize_google(audio).strip()
                    if text:
                        print(f"[Ear] Captured chunk: \"{text}\"")
                        self.phrase_buffer.append(text)
                        self.last_speech_time = time.time()
                    else:
                        # Empty but successful transcription? Check debounce
                        if self.phrase_buffer and (time.time() - self.last_speech_time) >= self.debounce_wait:
                            self._flush_buffer()
                except sr.UnknownValueError:
                    # Noise/unintelligible - if silent, check debounce
                    if self.phrase_buffer and (time.time() - self.last_speech_time) >= self.debounce_wait:
                         self._flush_buffer()
                except Exception as e:
                    print(f"[Ear] Transcription error: {e}")

            except sr.WaitTimeoutError:
                # Absolute silence for 'timeout' seconds
                if self.phrase_buffer and (time.time() - self.last_speech_time) >= self.debounce_wait:
                    self._flush_buffer()
                continue
                
            except Exception as e:
                if self.running:
                    print(f"[Ear] Loop error: {e}")
                    time.sleep(1)

    def _flush_buffer(self):
        """Join all captured chunks and emit as a single goal."""
        if not self.phrase_buffer:
            return
            
        full_text = " ".join(self.phrase_buffer)
        self.phrase_buffer = []
        
        # Ignore very short or echo-like commands if needed
        if len(full_text) < 3:
            return

        print(f"[Ear] >>> DEBOUNCE COMPLETE: \"{full_text}\"")
        
        event = {
            "type": "voice_input",
            "source": "sensor_ear",
            "payload": {
                "text": full_text,
                "status": "success",
                "timestamp": time.time()
            }
        }
        self.on_event(event)

    def start(self):
        if self.running:
            return
            
        if not SPEECH_RECOGNITION_AVAILABLE:
            print("[Ear] Cannot start Ear: speech_recognition is missing.")
            return
            
        self.running = True
        self._thread = threading.Thread(target=self._listen_loop, name="VoiceEarThread", daemon=True)
        self._thread.start()
        print("[Ear] Background listener started.")

    def stop(self):
        if not self.running:
            return
            
        print("[Ear] Stopping Ear...")
        self.running = False
        if self._thread:
            self._thread = None
