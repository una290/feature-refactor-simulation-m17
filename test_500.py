import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dae_p1.M12_obh_controller import OBHController
from dae_p1.M11_bundle_exporter import BundleExporter

try:
    exporter = BundleExporter()
    obh = OBHController(exporter)
    print("Keys in db:", list(obh.saved_full_cards.keys()))
    if not obh.saved_full_cards:
        print("No cards saved.")
        sys.exit(0)
    
    first_key = list(obh.saved_full_cards.keys())[0]
    print(f"Retrieving {first_key}...")
    bundle = obh.retrieve_bundle(first_key, authority_scope_ref="isp-support")
    print("Success!")
except Exception as e:
    import traceback
    traceback.print_exc()
