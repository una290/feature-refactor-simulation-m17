import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dae_p1.M20_install_verify import verify_install
from dae_p1.adapters.windows_wifi_adapter import WindowsWifiAdapter
from dae_p1.adapters.DOCSIS_adapter import DOCSISAdapter
from dae_p1.M03_metrics_collector import MetricsCollector
from dae_p1.M01_windowing import Windowing

def test_wifi():
    print("Testing WIFI...")
    win = WindowsWifiAdapter()
    samples = [win.collect_metric_sample() for _ in range(15)]
    res = verify_install(samples)
    print("Domain:", res.system_info.get("domain"))
    print("Profile threshold:", res.thresholds)

def test_cable():
    print("Testing CABLE...")
    cab = DOCSISAdapter()
    samples = [cab.collect_metric_sample() for _ in range(15)]
    res = verify_install(samples)
    print("Domain:", res.system_info.get("domain"))
    print("Profile threshold:", res.thresholds)

if __name__ == "__main__":
    test_wifi()
    test_cable()
