#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
import copy, json, sys
from pathlib import Path
root = Path(sys.argv[1])
base = json.loads((root / 'profiles/bettor-arena-runtime-local.json').read_text())
tech = json.loads((root / 'profiles/bettor-arena-tech-lead-local.json').read_text())
assert tech['schema'] == 'runtime-env/profile/v1'
assert tech['id'] == 'bettor-arena-tech-lead-local'
assert len(tech['modules']) == len(set(tech['modules'])), 'duplicate module in Tech Lead profile'
expected = set(base['modules']) | {'multi-worker-scheduler'}
assert set(tech['modules']) == expected, (set(tech['modules']) ^ expected)
assert tech['modules'].count('multi-worker-scheduler') == 1

def admits(candidate):
    modules = candidate.get('modules', [])
    return len(modules) == len(set(modules)) and set(modules) == expected and modules.count('multi-worker-scheduler') == 1

controls = []
missing = copy.deepcopy(tech); missing['modules'].remove('multi-worker-scheduler'); controls.append(('missing scheduler', missing))
duplicate = copy.deepcopy(tech); duplicate['modules'].append('multi-worker-scheduler'); controls.append(('duplicate scheduler', duplicate))
extra = copy.deepcopy(tech); extra['modules'].append('git-town-user-toolchain'); controls.append(('unadmitted extra module', extra))
for name, candidate in controls:
    assert not admits(candidate), f'planted control did not turn red: {name}'
print('PASS: Bettor Tech Lead profile is exact base + bounded scheduler; 3 planted controls refused')
PY
