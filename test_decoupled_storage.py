import sys
import os
import time
import pickle
sys.path.insert(0, 'c:/Users/ubee2/Downloads/DAE/DAE')

from dae_p1.M12_obh_controller import OBHController
from dae_p1.M11_bundle_exporter import BundleExporter
from dae_p1.M00_common import EpisodeRecognition, ObservabilityResult

def run_test():
    # Setup
    out_dir = './test_out'
    os.makedirs(out_dir, exist_ok=True)
    exporter = BundleExporter()
    ctrl = OBHController(exporter)

    # Clean old test files
    for f in [ctrl.ledger_path, ctrl.vault_path]:
        if os.path.exists(f): 
            try:
                os.remove(f)
            except:
                pass

    # Mock Data
    rec = EpisodeRecognition(
        episode_id='test-ep-001',
        episode_start=time.time(),
        worst_window_ref='W-TEST',
        diagnosis_code='UNKNOWN',
        confidence=1.0,
        evidence_refs=['ref1'],
        observability=ObservabilityResult('SUFFICIENT', False)
    )
    metrics = [{'ts': time.time(), 'val': 1.0}]

    # 1. Run OBH (Triggers Generation + Storage Split)
    print('Step 1: Running OBH...')
    ctrl.run(out_dir, rec, metrics, [], [])

    # 2. Verify File System Separation
    print('Step 2: Verifying Ledger/Vault files...')
    ledger_exists = os.path.exists(ctrl.ledger_path)
    vault_exists = os.path.exists(ctrl.vault_path)
    print(f'  Ledger exists: {ledger_exists}')
    print(f'  Vault exists:  {vault_exists}')

    with open(ctrl.ledger_path, 'rb') as f: ledger_data = pickle.load(f)
    with open(ctrl.vault_path, 'rb') as f: vault_data = pickle.load(f)

    card = ledger_data.get('test-ep-001')
    payload = vault_data.get('test-ep-001')

    print(f'  Ledger card payload is None? {card.payload is None}')
    print(f'  Vault has payload? {payload is not None}')
    print(f'  Vault has timeline? {"timeline" in payload if payload else False}')

    # 3. Test Retrieval Reconstruction
    print('Step 3: Testing retrieval reconstruction...')
    # Mock some data for BYUSE to pass
    card.refs = {'policy': 'tok', 'retention': 'tok', 'disclosure': 'tok'}
    ctrl.ledger['test-ep-001'] = card
    
    bundle = ctrl.retrieve_bundle('test-ep-001', byuse_context_ref='SUPPORT_CLOSURE')
    print(f'  Retrieved bundle has pc_min? {bundle.get("pc_min") is not None}')
    print(f'  Retrieved bundle has pc_priv? {bundle.get("pc_priv") is not None}')
    print(f'  Evidence Grade: {bundle.get("evidence_grade")}') # Expect READY

    print('Verification Complete!')

if __name__ == "__main__":
    run_test()
