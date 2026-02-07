
import os
import sys
import time
import json
import sqlite3
from typing import Any, Optional

# Ensure we can import from project root
sys.path.append(os.getcwd())

from agi.utils.database import DatabaseManager

def test_logging():
    print("--- Starting Logging Verification ---")
    db = DatabaseManager()
    
    # 1. Test Perception Logging
    print("\n[1] Testing Perception Logging...")
    db.log_perception_execution(
        name="test_perception",
        input_data={"query": "test"},
        output_data={"result": "seen"},
        error=None,
        duration=0.123
    )
    
    logs = db.get_component_logs("perception", "test_perception")
    assert len(logs) >= 1
    latest = logs[0]
    assert latest['name'] == "test_perception"
    assert latest['input']['query'] == "test"
    assert latest['duration'] == 0.123
    print("✅ Perception Log Retrieval Passed")

    stats = db.get_component_stats("perception", "test_perception")
    assert stats['total_runs'] >= 1
    assert stats['avg_duration'] > 0
    print("✅ Perception Stats Passed")
    
    # 2. Test Reflex Logging
    print("\n[2] Testing Reflex Logging...")
    db.log_reflex_execution(
        name="test_reflex",
        input_data={"event": "ping"},
        output_data={"triggered": True},
        error=None,
        duration=0.456
    )
    
    logs = db.get_component_logs("reflex", "test_reflex")
    assert len(logs) >= 1
    latest = logs[0]
    assert latest['name'] == "test_reflex"
    assert latest['output']['triggered'] is True
    print("✅ Reflex Log Retrieval Passed")
    
    # 3. Test Error Logging
    print("\n[3] Testing Error Logging...")
    db.log_perception_execution(
        name="test_perception_fail",
        input_data={},
        output_data=None,
        error="Sensor disconnected",
        duration=0.01
    )
    
    stats_fail = db.get_component_stats("perception", "test_perception_fail")
    assert stats_fail['total_runs'] == 1
    assert stats_fail['success_rate'] == 0.0
    print("✅ Error Stats Passed")
    
    print("\n--- All Logging Tests Passed ---")

if __name__ == "__main__":
    try:
        test_logging()
    except AssertionError as e:
        print(f"❌ Assertion Failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
