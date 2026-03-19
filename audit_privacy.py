import sys
sys.path.insert(0, 'c:/Users/ubee2/Downloads/DAE/DAE')
from dae_p1.M22_privacy_governance import PrivacyGovernance, BYUSE_RULES

pg = PrivacyGovernance()

print('='*60)
print('AUDIT-1: check_base_validity')
print('='*60)

class OkAttempt:
    class observability:
        missing_refs = []

class BadAttempt:
    class observability:
        missing_refs = ['window_policy']

class NoObsAttempt:
    pass

v, m, r = pg.check_base_validity(OkAttempt())
print(f'  CaseA (no missing): valid={v}, missing={m}, ref_types={list(r.keys())}')

v2, m2, r2 = pg.check_base_validity(BadAttempt())
print(f'  CaseB (has missing): valid={v2}, missing={m2}, refs={r2}')

try:
    v3, m3, r3 = pg.check_base_validity(NoObsAttempt())
    print(f'  CaseC (no observability): valid={v3} -> OK (handled)')
except Exception as e:
    print(f'  CaseC (no observability): [BUG] Exception: {e}')

print()
print('='*60)
print('AUDIT-2: project_view')
print('='*60)

sample = {'refs': {'disclosure': 'tok_scope_isp_support'}, 'payload': {'x': 1}}

for scope, label in [('isp-support', 'isp-support'), ('admin_override', 'admin_override'),
                      (None, 'None'), ('unknown_xyz', 'unknown_scope')]:
    result = pg.project_view(sample, scope)
    ercpt = result.get('egress_receipt_ref')
    payload_intact = result.get('payload') is not None
    print(f'  scope={str(label):<18}: egress_receipt={str(bool(ercpt)):<6} payload_intact={payload_intact}')

try:
    r5 = pg.project_view({}, 'isp-support')
    print(f'  empty card:           egress_receipt={str(bool(r5.get("egress_receipt_ref"))):<6} -> OK')
except Exception as e:
    print(f'  empty card: [BUG] {e}')

print()
print('='*60)
print('AUDIT-3: evaluate_closure_grade - case matrix')
print('='*60)

full_refs  = {'refs': {'policy': 'tok', 'retention': 'tok', 'disclosure': 'tok'}}
partial    = {'refs': {'policy': 'tok'}}
empty_refs = {'refs': {}}

contexts = [None, 'SUPPORT_CLOSURE', 'DISPUTE', 'dispute', 'COMPLIANCE_AUDIT', 'unknown_ctx']

for ctx in contexts:
    for is_signed in [False, True]:
        for card, clabel in [(full_refs, 'full'), (partial, 'partial'), (empty_refs, 'empty')]:
            grade, req = pg.evaluate_closure_grade(card, ctx, is_signed)
            flag = ''
            if grade not in ['DELIVERY_GRADE','CLOSURE_GRADE','NOT_CLOSURE_GRADE','PARTIAL_RELIANCE']:
                flag = ' <- [UNKNOWN GRADE]'
            print(f'  ctx={str(ctx):<22} signed={is_signed} refs={clabel:<8}: {grade:<22} req={str(req)}{flag}')

print()
print('='*60)
print('AUDIT-4: Case Sensitivity Bug Check (M12 vs M22)')
print('='*60)
print(f'  BYUSE_RULES keys: {list(BYUSE_RULES.keys())}')
print(f'  M12 uses: byuse_context_ref and "dispute" in byuse_context_ref (lowercase)')
print(f'  Frontend sends: null or "dispute" (lowercase)')
print(f'  M22 looks up: context_ref.upper() -> "DISPUTE"')

grade_lower, req_lower = pg.evaluate_closure_grade(full_refs, 'dispute')
grade_upper, req_upper = pg.evaluate_closure_grade(full_refs, 'DISPUTE')
print(f'  evaluate_closure_grade("dispute"): {grade_lower}')
print(f'  evaluate_closure_grade("DISPUTE"): {grade_upper}')
if grade_lower == grade_upper:
    print('  -> Case handling: OK (upper() conversion works)')
else:
    print('  -> [BUG] Case mismatch - "dispute" and "DISPUTE" produce different grades!')

print()
print('='*60)
print('AUDIT-5: M12 is_dispute flag vs M22 BYUSE_RULES alignment')
print('='*60)
print('  M12 retrieve_bundle line 189:')
print('    is_dispute = byuse_context_ref and "dispute" in byuse_context_ref')
print()
print('  This catches: "dispute", "DISPUTE", "dispute_escalation", "pre-dispute"')
test_cases = ['dispute', 'DISPUTE', 'dispute_escalation', 'support_closure', None, 'SUPPORT_CLOSURE']
for tc in test_cases:
    is_d = bool(tc and 'dispute' in tc)
    in_rules = tc.upper() in BYUSE_RULES if tc else False
    match = 'OK' if (is_d == in_rules or tc is None) else '[MISMATCH]'
    print(f'  context={str(tc):<24}: is_dispute M12={is_d}, in BYUSE_RULES={in_rules}  {match}')

print()
print('ALL AUDITS COMPLETE')
