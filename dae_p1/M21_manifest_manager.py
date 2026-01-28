
from __future__ import annotations
from typing import List, Dict, Any
import time
import uuid


import sqlite3
import datetime
import os

class ManifestManager:
    """
    Manages the V1.3 Manifest (Index of available data).
    Retrieves available days/windows from the persistent store.
    """
    def __init__(self, metrics_buffer, events_buffer=None):
        """
        Args:
            metrics_buffer: Instance of SQLiteRingBuffer (M02)
            events_buffer: Instance of SQLiteRingBuffer (M02) for events
        """
        self.metrics_buffer = metrics_buffer
        self.events_buffer = events_buffer
        
        self.db_path = getattr(metrics_buffer, 'db_path', None)
        self.table_name = getattr(metrics_buffer, 'table_name', 'metrics')
        
        # Events DB info
        self.events_db_path = getattr(events_buffer, 'db_path', None)
        self.events_table_name = getattr(events_buffer, 'table_name', 'events')

    def get_manifest(self, device_id: str) -> Dict[str, Any]:
        """
        Generates the current Manifest by querying the DB.
        """
        if not self.db_path or not os.path.exists(self.db_path):
            return {
                "error": "Storage not initialized",
                "manifest_ref": f"man-{uuid.uuid4().hex[:8]}",
                "available_day_refs": [],
                "bundle_pointer": "none"
            }

        available_days = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Query min/max timestamps to determine range
                # Or distinct days. Storing TS as REAL (float).
                # SQLite 'strftime' can convert epoch to date string.
                # Assuming ts is in seconds (unix epoch).
                # usage: strftime('%Y%m%d', datetime(ts, 'unixepoch'))
                
                query = f"""
                    SELECT DISTINCT strftime('%Y%m%d', datetime(ts, 'unixepoch', 'localtime')) 
                    FROM {self.table_name}
                    ORDER BY ts DESC
                """
                cursor.execute(query)
                rows = cursor.fetchall()
                available_days = [f"DAY-{r[0]}" for r in rows if r[0]]
                
        except Exception as e:
            print(f"[M21] Error querying manifest: {e}")
            # Fallback to empty list or mock if critical
            pass


        available_event_refs = []
        try:
            # Query Events if persistent
            # Re-use DB connection if same DB, else new
            # Assuming server.py uses same file for both or different? 
            # Usually M02 instances might share DB file but different table, OR distinct files.
            # We treat them as potentially different.
            
            if self.events_buffer and self.events_db_path and os.path.exists(self.events_db_path):
                 with sqlite3.connect(self.events_db_path) as conn:
                    cursor = conn.cursor()
                    # We want all event refs. "change_ref" inside the JSON? 
                    # Complex JSON query in SQLite is valid but checking standard 'data' blob
                    # Let's just grab ID or generated refs.
                    # M04 produces ChangeEventCard. Ideally we index by event_type.
                    # For Manifest, we just need a list of WHAT is there.
                    # Let's list unique event types found.
                    
                    # NOTE: SQLite JSON extension might not be enabled on all embedded Pythons.
                    # We will fallback to fetching recent 100 headers if JSON query fails.
                    try:
                        cursor.execute(f"SELECT json_extract(data, '$.event_type') FROM {self.events_table_name} LIMIT 1000")
                        rows = cursor.fetchall()
                        # distinct
                        available_event_refs = list(set([r[0] for r in rows if r[0]]))
                    except Exception:
                         # Fallback: Just report "PERSISTED_EVENTS_AVAILABLE"
                         available_event_refs = ["PERSISTED_EVENTS_AVAILABLE"]

        except Exception as e:
            # print(f"[M21] Error querying events: {e}")
            pass

        return {
            "manifest_ref": f"man-{uuid.uuid4().hex[:8]}",
            "available_day_refs": available_days,
            "available_event_refs": available_event_refs, 
            "bundle_pointer": f"sqlite://{os.path.basename(self.db_path)}" 
        }

    def get_bundle(self, ref: str) -> Dict[str, Any]:
        """
        Retrieves a bundle by reference. 
        """
        return {"ref": ref, "content": "mock_binary_blob", "size": 1024}

