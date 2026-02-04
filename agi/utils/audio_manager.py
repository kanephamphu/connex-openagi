
import asyncio
import threading
import time
from typing import Optional, Callable, Awaitable

class AudioManager:
    """
    Central manager for audio I/O to prevent simultaneous listening and speaking.
    Handles a queue for speech requests.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AudioManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config=None):
        if self._initialized:
            return
        self.config = config
        self.speak_queue = asyncio.Queue()
        self._is_speaking = False
        self._processing_task = None
        self._initialized = True
        self._loop = None

    def set_loop(self, loop):
        self._loop = loop
        if self._processing_task is None:
            self._processing_task = self._loop.create_task(self._process_speak_queue())

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    async def speak(self, text: str, play_fn: Callable[[str], Awaitable[None]]):
        """
        Queue a text to be spoken. Returns when it has been played.
        """
        future = asyncio.get_event_loop().create_future()
        await self.speak_queue.put((text, play_fn, future))
        return await future

    async def _process_speak_queue(self):
        while True:
            text, play_fn, future = await self.speak_queue.get()
            try:
                # Wait if user is currently speaking (Ear is active)
                while self.config and self.config.is_listening:
                    await asyncio.sleep(0.3)
                
                self._is_speaking = True
                if self.config:
                    self.config.is_speaking = True
                
                await play_fn(text)
                
                future.set_result(True)
            except Exception as e:
                print(f"[AudioManager] Error playing speech: {e}")
                future.set_exception(e)
            finally:
                self._is_speaking = False
                if self.config:
                    self.config.is_speaking = False
                self.speak_queue.task_done()

audio_manager = AudioManager()
