import threading
import time
import json
import os
import logging
from datetime import datetime
from typing import Callable, Dict, Any, List, Optional

class TimeSensor:
    """
    A'Time' sensor for the AGI. Background sensor that monitors scheduled events 
    and deadlines, triggering the reflex layer when events occur.
    """
    def __init__(self, config, on_event_callback: Callable[[Dict[str, Any]], Any]):
        self.config = config
        self.on_event = on_event_callback
        self.running = False
        self._thread: Optional[threading.Thread] = None
        
        # Path to the events database
        self.data_path = os.path.join(getattr(self.config, 'data_dir', 'data'), 'time_events.json')
        self.processed_events = set()
        
        if self.config.verbose:
            print(f"[TimeSensor] Initialized with data path: {self.data_path}")

    def _check_events_loop(self):
        print("[TimeSensor] Background monitoring started.")
        
        while self.running:
            try:
                self._poll_and_check()
                # Check every 30 seconds for higher precision in demo
                time.sleep(30)
            except Exception as e:
                if self.running:
                    print(f"[TimeSensor] Error in monitoring loop: {e}")
                    time.sleep(5)

    def _poll_and_check(self):
        """Read events from JSON and check if any should trigger."""
        if not os.path.exists(self.data_path):
            return

        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
                events = data.get('events', [])
        except Exception as e:
            print(f"[TimeSensor] Could not read events: {e}")
            return

        now = datetime.now()
        
        for event in events:
            event_id = event.get('id')
            if event_id in self.processed_events:
                continue

            trigger_time_str = event.get('trigger_time')
            if not trigger_time_str:
                continue

            try:
                # Assuming ISO format: 2026-02-05T12:10:00+07:00
                # Python 3.7+ fromisoformat handles offsets
                trigger_time = datetime.fromisoformat(trigger_time_str)
                
                # Check if it's time to trigger (within a small window or past)
                # But we don't want to trigger events from the far past on startup
                if trigger_time <= now:
                    diff = (now - trigger_time).total_seconds()
                    # Only trigger if it's within the last 5 minutes to avoid spamming old events
                    if diff < 300:
                        self._trigger_event(event)
                        self.processed_events.add(event_id)
            except Exception as e:
                print(f"[TimeSensor] Error parsing time for event {event_id}: {e}")

    def _trigger_event(self, event: Dict[str, Any]):
        """Emit the event to the AGI."""
        print(f"[TimeSensor] >>> TRIGGERED: {event.get('description')} ({event.get('type')})")
        
        agi_event = {
            "type": "time_event",
            "source": "sensor_time",
            "payload": {
                "event_id": event.get("id"),
                "event_type": event.get("type"),
                "description": event.get("description"),
                "data": event.get("payload", {}),
                "timestamp": time.time()
            }
        }
        self.on_event(agi_event)

    def start(self):
        if self.running:
            return
            
        self.running = True
        self._thread = threading.Thread(target=self._check_events_loop, name="TimeSensorThread", daemon=True)
        self._thread.start()
        print("[TimeSensor] Background monitoring activated.")

    def stop(self):
        if not self.running:
            return
            
        print("[TimeSensor] Stopping...")
        self.running = False
        if self._thread:
            self._thread = None
