from __future__ import annotations
from dataclasses import dataclass
import datetime as dt
from typing import Dict, Tuple
from .types import WindowRef

@dataclass
class WindowManager:
    window_seconds: int = 300  # 5 min default

    def window_for(self, ts: dt.datetime) -> WindowRef:
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.timezone.utc)
        epoch = int(ts.timestamp())
        start_epoch = epoch - (epoch % self.window_seconds)
        end_epoch = start_epoch + self.window_seconds
        start = dt.datetime.fromtimestamp(start_epoch, tz=dt.timezone.utc)
        end = dt.datetime.fromtimestamp(end_epoch, tz=dt.timezone.utc)
        wid = f"W{start_epoch}_{self.window_seconds}"
        return WindowRef(window_id=wid, start_ts=start, end_ts=end)
