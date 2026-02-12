
import json
import sys
from dae_p1.M13_fp_lite import ProofCardGenerator
from dae_p1.M22_privacy_governance import EvidenceGrade
from dataclasses import asdict

def test_grade_serialization():
    print("--- Testing Evidence Grade Serialization ---")
    
    # 1. Create Generator
    gen = ProofCardGenerator()
    
    # 2. Generate a dummy card
    # We pass empty metrics which might trigger INSUFFICIENT_SAMPLES but should still have a grade
    card = gen.generate(
        metrics=[], 
        events=[], 
        snapshots=[], 
        profile_ref="WIFI78_INSTALL_ACCEPT"
    )
    
    # 3. Check Object Field
    print(f"Object Grade: {card.pc_min.evidence_grade} (Type: {type(card.pc_min.evidence_grade)})")
    
    # 4. Check Serialization (asdict)
    # This simulates what M12/M00 does
    card_dict = asdict(card)
    min_dict = card_dict['pc_min']
    
    print(f"Serialized Grade: {min_dict.get('evidence_grade')}")
    
    # 5. Check if it matches Enum string
    if min_dict.get('evidence_grade') == EvidenceGrade.DELIVERY_GRADE.value:
        print("PASS: Grade matches Enum value")
    elif isinstance(min_dict.get('evidence_grade'), EvidenceGrade):
         print("WARN: Grade is still Enum object, might fail JSON dump if not handled")
    else:
        print(f"FAIL: Grade is {min_dict.get('evidence_grade')}")
        
    # 6. JSON Dump Test
    try:
        json_str = json.dumps(min_dict)
        print("JSON Dump success")
        print(json_str)
    except TypeError as e:
        print(f"JSON Dump FAIL: {e}")

if __name__ == "__main__":
    test_grade_serialization()
