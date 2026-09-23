"""Resume-safe export of the verified zero-start run, records 0 through 70."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

RUN = Path('/root/autodl-tmp/HINT/ncsx-debug-zero-b-2.3.0-component-20260921T094915Z')
CASE = Path('/root/LYH-HINT/cases/ncsx-debug-zero')
TOOLS = Path(__file__).resolve().parent
OUT = RUN / 'postprocess-step070-complete'
STATE = OUT / 'export_state.json'
COMMIT = '0495705cb52feb85e8db2f31f0cc91034197a01b'


def main():
    import hint_debug
    import netCDF4
    import numpy as np
    from hint_debug_plotting.data import complete_indices
    assert hint_debug.__version__ == '2.3.0'
    assert (CASE / 'run').resolve() == RUN
    assert subprocess.check_output(['git', '-C', '/root/LYH-HINT/source/HINT-docs', 'rev-parse', 'HEAD'], text=True).strip() == COMMIT
    events = [json.loads(line) for file in (RUN/'progress.jsonl', RUN/'follow-to070/progress.jsonl') for line in file.read_text().splitlines()]
    assert events[-1]['event'] == 'finished'
    assert [e['diagnostic']['outer_step'] for e in events if e['event']=='outer_complete'] == list(range(1, 71))
    with netCDF4.Dataset(RUN/'hint_debug_ncsx_zero.nc') as ds:
        group = ds.groups['equilibrium']
        indices = complete_indices(group, 'record_complete', 'time')
        assert indices.tolist() == list(range(71))
        assert np.array_equal(group['outer_step'][indices], np.arange(71))
        assert int(group['pressure_ramp_step'][70]) == 20
    OUT.mkdir(exist_ok=True)
    state = json.loads(STATE.read_text()) if STATE.exists() else dict(run=str(RUN), version='2.3.0', source_commit=COMMIT, completed=[])
    assert state['run'] == str(RUN)
    jobs = [('initial_poincare', 'poincare_zero70.py', ['0']),
            ('final_poincare', 'poincare_zero70.py', ['70']),
            ('static', 'postprocess_zero70.py', ['static']),
            ('summary', 'postprocess_zero70.py', ['summary']),
            ('precision', 'precision_zero70.py', []),
            ('history_iota', 'history_zero70.py', []),
            ('existing', 'postprocess_zero70.py', ['existing'])]
    for phase, script, args in jobs:
        if phase in state['completed']:
            continue
        state.update(phase=phase, status='running', updated_utc=datetime.now(timezone.utc).isoformat())
        STATE.write_text(json.dumps(state, indent=2)+'\n')
        print(json.dumps(state), flush=True)
        with (OUT/f'{phase}.log').open('a') as log:
            result = subprocess.run([sys.executable, '-u', str(TOOLS/script), *args], cwd=TOOLS,
                                    stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            state.update(status='failed', returncode=result.returncode)
            STATE.write_text(json.dumps(state, indent=2)+'\n')
            raise RuntimeError(f'Export phase {phase} failed')
        state['completed'].append(phase)
    state.update(status='complete', updated_utc=datetime.now(timezone.utc).isoformat())
    STATE.write_text(json.dumps(state, indent=2)+'\n')
    print(json.dumps(state), flush=True)


if __name__ == '__main__':
    if sys.argv[1:] == ['launch']:
        OUT.mkdir(exist_ok=True)
        pidfile = OUT/'pid'
        if pidfile.exists() and Path('/proc/'+pidfile.read_text().strip()).exists():
            raise RuntimeError('Export already running')
        env = os.environ.copy()
        env.update(MPLBACKEND='Agg', JAX_ENABLE_X64='true', XLA_PYTHON_CLIENT_PREALLOCATE='false',
                   OMP_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', CUDA_VISIBLE_DEVICES='0',
                   JAX_COMPILATION_CACHE_DIR=str(RUN/'post-jax-cache'), JAX_USE_SIMPLIFIED_JAXPR_CONSTANTS='true')
        env.pop('JAX_PLATFORMS', None)
        with (OUT/'export.log').open('a') as log:
            child = subprocess.Popen([sys.executable, '-u', str(Path(__file__).resolve())], cwd=TOOLS,
                                     env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
        pidfile.write_text(str(child.pid)+'\n')
        print('EXPORT_PID', child.pid, flush=True)
    else:
        main()
