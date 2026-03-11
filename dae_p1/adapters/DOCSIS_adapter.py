from __future__ import annotations
import time
import re
import random
from typing import List, Tuple, Optional
from .base_adapter import DomainAdapter
from ..M00_common import MetricSample, ChangeEventCard, PreChangeSnapshot, VersionRefs
from ..M01_windowing import Windowing
from ..M03_metrics_collector import MetricsCollector
from ..M04_change_event_logger import ChangeEventLogger
from ..M05_snapshot_manager import SnapshotManager
from ..M17_demo_simulator import DemoSimulator

class DOCSISAdapter(DomainAdapter):
    """
    DOCSIS (Cable) adapter: parses mock CLI outputs to generate MetricSample.
    Acts as a bridge template for C/Linux firmware developers.
    """
    def __init__(self, version_refs: VersionRefs = VersionRefs(fw="unknown", driver="unknown", agent="dae_p1")):
        self.windowing = Windowing()
        self.collector = MetricsCollector(self.windowing)
        self.event_logger = ChangeEventLogger(self.windowing, version_refs)
        self.snap = SnapshotManager()
        self.sim = DemoSimulator()
        self.overrides = {}
        
    @property
    def domain(self) -> str:
        if hasattr(self, 'overrides') and 'domain' in self.overrides:
            return self.overrides['domain']['value']
        return "CABLE"

    def _run_docsis_cli(self) -> str:
        """
        Simulates executing a CLI command on a Cable gateway (e.g. 'docsisctl show phy').
        In a real deployment, replace this with actual subprocess calls or SDK API bindings.
        """
        # Base realistic values
        mer = 38.5
        t3 = 1
        t4 = 0
        corr = 1250
        uncorr = 40
        lat = 15.2
        loss = 0.0

        # Inject simulated degradation if requested via Demo Controls
        if self.overrides and 'simulation_type' in self.overrides:
            now = time.time()
            ov = self.overrides['simulation_type']
            if ov.get('until', 0) > now:
                sim_type = ov['value']
                # Map generic simulation types to specific DOCSIS impairments
                if sim_type == 'latency':
                    lat += random.uniform(80, 150)
                elif sim_type == 'retry' or sim_type == 'oscillating': 
                    # retry maps to T3/T4 bursts on cable
                    t3 += random.randint(5, 15)
                    loss += random.uniform(1.0, 5.0)
                elif sim_type == 'complex' or sim_type == 'degrading':
                    # Complex plant impairment
                    mer -= random.uniform(6.0, 12.0)
                    t3 += random.randint(2, 10)
                    corr += random.randint(5000, 20000)
                    uncorr += random.randint(100, 500)
                    lat += random.uniform(30, 80)

        # Generate a fake terminal string simulating what a C program/CLI would dump
        mock_cli_output = f'''
CM> docsisctl show phy
---------------------------------------------------------
Downstream Channel 1:
  Frequency: 651000000 Hz
  Modulation: 256QAM
  Power Level: -1.2 dBmV
  Signal to Noise Ratio (MER): {mer:.1f} dB
  Corrected FEC: {int(corr)}
  Uncorrectable FEC: {int(uncorr)}

Upstream Channel 1:
  Frequency: 30400000 Hz
  Power Level: 45.0 dBmV

MAC Counters:
  T3 Timeouts: {int(t3)}
  T4 Timeouts: {int(t4)}

Ping CMTS (Latency to ISP Gateway):
  rtt min/avg/max/mdev = {max(1.0, lat-2):.1f}/{lat:.1f}/{lat+5:.1f}/1.1 ms
  packet loss: {loss:.1f}%
---------------------------------------------------------
'''
        return mock_cli_output

    def collect_metric_sample(self) -> MetricSample:
        # 1. Capture the raw text output from the "modem"
        raw_output = self._run_docsis_cli()
        
        # 2. Parse the text using Regular Expressions (Regex)
        # This translates arbitrary logs into exact measurements
        mer_db = 38.5
        fec_corr = 0
        fec_uncorr = 0
        t3_count = 0
        t4_count = 0
        us_lat = 15.0
        us_loss = 0.0

        try:
            m1 = re.search(r"Signal to Noise Ratio \(MER\):\s*([\d\.]+)\s*dB", raw_output)
            if m1: mer_db = float(m1.group(1))

            m2 = re.search(r"Corrected FEC:\s*(\d+)", raw_output)
            if m2: fec_corr = int(m2.group(1))

            m3 = re.search(r"Uncorrectable FEC:\s*(\d+)", raw_output)
            if m3: fec_uncorr = int(m3.group(1))

            m4 = re.search(r"T3 Timeouts:\s*(\d+)", raw_output)
            if m4: t3_count = int(m4.group(1))

            m5 = re.search(r"T4 Timeouts:\s*(\d+)", raw_output)
            if m5: t4_count = int(m5.group(1))

            m6 = re.search(r"avg/max/mdev = [\d\.]+?/([\d\.]+?)/", raw_output)
            if m6: us_lat = float(m6.group(1))

            m7 = re.search(r"packet loss:\s*([\d\.]+)%", raw_output)
            if m7: us_loss = float(m7.group(1))
            
        except Exception as e:
            print(f"Failed to parse DOCSIS output: {e}")

        # 3. Pack the securely extracted types into the unified Engine schema
        return self.collector.collect(
            domain=self.domain,
            ofdm_mer_db=mer_db,
            fec_corrected=fec_corr,
            fec_uncorrected=fec_uncorr,
            t3_count=t3_count,
            t4_count=t4_count,
            us_latency_p95_ms=us_lat,
            us_loss_pct=us_loss,
            # Fallback/Generic mappings
            latency_p95_ms=us_lat,
            loss_pct=us_loss
        )

    def collect_change_events_and_snapshots(self) -> Tuple[List[ChangeEventCard], List[PreChangeSnapshot]]:
        return [], []
