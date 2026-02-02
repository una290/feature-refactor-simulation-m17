import sys
import os
import time

# Add parent directory to sys.path to allow importing dae_p1
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dae_p1.M13_fp_lite import ProofCardGenerator

def test_proofcard_event_population():
    print("Testing ProofCardGenerator event_type population...")
    
    gen = ProofCardGenerator()
    
    # Mock Metric Data (Need enough to pass MIN_SAMPLES=10 check of BASE profile)
    mock_metrics = []
    for i in range(12):
        mock_metrics.append({
            "ts": time.time() - i*10,
            "latency_ms": 10.0,
            "loss_pct": 0.0
        })
        
    # Mock Events
    mock_events = [
        {"event_type": "wifi_loss_spike", "ts": time.time()},
        {"event_type": "channel_switch", "ts": time.time() - 5},
        {"event_type": "wifi_loss_spike", "ts": time.time() - 10} # Duplicate type, should be deduped
    ]
    
    result = gen.generate(
        window_data=mock_metrics,
        profile_ref="BASE",
        window_ref_str="test_win_01",
        events=mock_events
    )
    
    print(f"Resulting ProofCard: {result['proof_card_ref']}")
    print(f"Event Types Found: {result['event_type']}")
    
    expected = ["channel_switch", "wifi_loss_spike"]
    expected.sort()
    
    actual = result.get('event_type', [])
    actual.sort()
    
    if actual == expected:
        print("SUCCESS: event_type population verified.")
        sys.exit(0)
    else:
        print(f"FAILURE: Expected {expected}, got {actual}")
        sys.exit(1)

if __name__ == "__main__":
    test_proofcard_event_population()
