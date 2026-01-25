from __future__ import annotations
import datetime as dt
from collections import defaultdict
from typing import Dict, List, Tuple
from .types import Observation, WindowRef
from .windowing import WindowManager

class WindowAggregator:
    def __init__(self, window_mgr: WindowManager):
        self.wm = window_mgr
        self._by_device_window: Dict[Tuple[str,str], List[Observation]] = defaultdict(list)

    def add(self, obs: Observation) -> WindowRef:
        w = self.wm.window_for(obs.ts)
        self._by_device_window[(obs.device_id, w.window_id)].append(obs)
        return w

    def get(self, device_id: str, window_id: str) -> List[Observation]:
        return list(self._by_device_window.get((device_id, window_id), []))

    def summarize(self, obs_list: List[Observation]) -> Dict[str, float]:
        # Simple aggregation; extend freely (open set).
        sums = defaultdict(float)
        counts = defaultdict(int)
        for o in obs_list:
            for k,v in o.metrics.items():
                if isinstance(v, (int,float)) and v is not None:
                    sums[k]+=float(v)
                    counts[k]+=1
        avg = {k: (sums[k]/counts[k]) for k in sums if counts[k]>0}
        # event counts
        ev = defaultdict(int)
        for o in obs_list:
            for e in o.events:
                ev[f"event_{e.get('type','unknown')}"] += 1
        for k,v in ev.items():
            avg[k]=float(v)
        # domain counts
        dom = defaultdict(int)
        for o in obs_list:
            dom[f"domain_{o.domain}"] += 1
        for k,v in dom.items():
            avg[k]=float(v)
        return dict(avg)
