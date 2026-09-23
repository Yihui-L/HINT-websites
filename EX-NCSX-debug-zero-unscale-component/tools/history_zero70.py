"""Four independent read-only checkpoint reductions; identical plotting API/formulas."""
import os
from pathlib import Path
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

ROOT=Path('/root/LYH-HINT/cases/ncsx-debug-zero/run/postprocess-step070-complete')


def worker(lane):
    cpus=sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0,cpus[lane*6:lane*6+6])
    os.environ.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4')
    import numpy as np
    import postprocess_zero70 as api
    p=api.frame(backend='cpu', engine='native')
    weights=np.broadcast_to(p.grid.r[:,None,None],p.grid.shape)
    names=['speed','force_residual','force_residual_relative','pressure','field_strength',
           'response_field_strength','velocity_change_rate','speed_change_rate']
    records=[]
    for index in range(lane,71,4):
        item=p if index==p.record else p._frame(index)
        row={'outer':int(item.state.outer_step)}
        assert row['outer']==index
        for name in names:
            values=item.field(name,scope='wall')
            for scope in ('wall','plasma'):
                mask=np.isfinite(values)
                if scope=='plasma':
                    mask &= (item.state.norm_s>=0)&(item.state.norm_s<1)
                v,w=values[mask],weights[mask]
                for mode in ('mean','rms','max'):
                    number=np.nan if not v.size else (np.max(v) if mode=='max' else
                        np.sqrt(np.average(v*v,weights=w)) if mode=='rms' else np.average(v,weights=w))
                    row[f'{name}_{scope}_{mode}']=float(number) if np.isfinite(number) else None
        records.append(row)
        (ROOT/f'checkpoint_lane_{lane}.json').write_text(json.dumps(records)+'\n')
        print(json.dumps(dict(lane=lane,outer=index)),flush=True)
    p.check_stable()
    return records


if __name__=='__main__':
    with ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn')) as pool:
        rows=[row for block in pool.map(worker,range(4)) for row in block]
    rows.sort(key=lambda r:r['outer'])
    assert [row['outer'] for row in rows]==list(range(71))
    (ROOT/'checkpoint_reductions.json').write_text(json.dumps(rows,indent=2)+'\n')
    os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:6])
    import postprocess_zero70 as api
    p=api.frame()
    api.histories(p)
    api.log('phase_complete',phase='histories')
    api.iota(p)
    p.check_stable()
    api.log('phase_complete',phase='iota')
    api.log('complete',figures=len(list(api.FIG.glob('*.png'))))
