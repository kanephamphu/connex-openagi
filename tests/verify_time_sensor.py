import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from agi.config import AGIConfig
from agi.sensors.time.time_sensor import TimeSensor

async def test_time_sensor():
    print("Starting TimeSensor verification test...")
    
    # Setup dummy config
    config = AGIConfig.from_env()
    config.verbose = True
    config.data_dir = "tests/data"
    os.makedirs(config.data_dir, exist_ok=True)
    
    events_file = os.path.join(config.data_dir, "time_events.json")
    
    # Create test events
    now = datetime.now()
    trigger_time = (now + timedelta(seconds=5)).isoformat()
    
    test_data = {
        "events": [
            {
                "id": "test_event_1",
                "type": "calendar",
                "trigger_time": trigger_time,
                "description": "Verification Test Event",
                "payload": {"info": "test"}
            }
        ]
    }
    
    with open(events_file, "w") as f:
        json.dump(test_data, f)
        
    triggered_events = []
    
    def on_event(event):
        print(f"Callback received event: {event['type']}")
        triggered_events.append(event)

    sensor = TimeSensor(config, on_event_callback=on_event)
    sensor.start()
    
    print("Waiting 10 seconds for sensor to trigger...")
    await asyncio.sleep(10)
    
    sensor.stop()
    
    if len(triggered_events) > 0:
        print("SUCCESS: TimeSensor triggered correctly.")
        print(f"Event details: {triggered_events[0]}")
    else:
        print("FAILURE: TimeSensor did not trigger.")

if __name__ == "__main__":
    asyncio.run(test_time_sensor())
