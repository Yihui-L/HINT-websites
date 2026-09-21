"""Read-only, complete step-50 figure export using installed HINT-debug APIs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

os.environ.update(MPLBACKEND="Agg", JAX_ENABLE_X64="true",
                  XLA_PYTHON_CLIENT_PREALLOCATE="false")
os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "8")
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import hint_debug
from hint_debug_plotting import HintPlots
from hint_debug_plotting.data import complete_indices
from hint_debug_plotting.variables import FIELDS, METRICS

CASE = Path('/root/LYH-HINT/cases/ncsx-debug')
RUN = (CASE / 'run').resolve()
OUT = RUN / 'postprocess-step050-complete'
FIG = OUT / 'figures'
FIG.mkdir(parents=True, exist_ok=True)
START = time.monotonic()
SURFACES = [0, .25, .5, .75, 1]
SEED_S = np.unique(np.r_[np.geomspace(1e-4, .02, 16), np.linspace(.02, .98, 161),
                         1 - np.geomspace(1e-4, .02, 16)])


def log(event, **values):
    row = dict(event=event, elapsed_s=time.monotonic()-START, **values)
    print(json.dumps(row), flush=True)
    with (OUT / 'progress.jsonl').open('a') as f:
        f.write(json.dumps(row) + '\n')


def save(result, name):
    axes = np.atleast_1d(result.axes)
    result.figure.set_size_inches(9.5, (4.6 if name.startswith('section_') else 3.7)*len(axes)+.7)
    if name.startswith(('section_', 'profile_')):
        legends = [axis.get_legend() for axis in axes]
        if legends[0] is not None:
            handles = legends[0].legend_handles
            labels = [text.get_text() for text in legends[0].get_texts()]
            for legend in legends:
                if legend is not None:
                    legend.remove()
            result.figure.legend(handles, labels, loc='outside lower center', ncol=3, fontsize=8)
    old_title = result.figure._suptitle.get_text() if result.figure._suptitle else name
    result.figure.suptitle('NCSX | HINT-debug 2.2.0 | outer 50 | VMEC / unscaled\n' + old_title,
                          fontsize=12)
    result.save(FIG / (name + '.png'), dpi=300)
    plt.close(result.figure)
    log('figure', name=name)


def frame():
    assert hint_debug.__version__ == '2.2.0'
    p = HintPlots(RUN/'hint_debug_ncsx_vmec.nc', outer_step=50,
                  wout=CASE/'inputs/wout_ncsx_c09r00_free_nonnegative.nc', backend='gpu', engine='jax')
    config = p.store.load_solver_configuration(p.record)
    assert p.state.outer_step == 50 and config['scale_after'] is False
    assert p.backend.magnetic_interpolation == 'component'
    return p


def sections(p):
    for quantity in FIELDS:
        scale = 'auto' if quantity in {'force_residual','pressure_gradient','lorentz_force',
                                      'current_density','speed','velocity_change_rate'} else 'linear'
        if quantity.startswith('divergence_b') and quantity.endswith('_abs'):
            scale = 'symlog'
        save(p.sections(quantity, scale=scale, levels=50, contour_lines=12,
                        vmec_surfaces=SURFACES, compare_vmec=p.vmec_available(quantity)),
             'section_'+quantity)


def static(p):
    sections(p)
    for quantity in ('pressure','toroidal_current_density','speed','force_residual',
                     'force_residual_relative','field_strength'):
        for coordinate in ('s','rho','R','Z','phi'):
            options = {'r_m':1.57} if coordinate in {'Z','phi'} else {}
            save(p.profiles(quantity, coordinate=coordinate, bins=64, z_m=0,
                            compare_vmec=p.vmec_available(quantity), **options),
                 f'profile_{quantity}_{coordinate}')
    for coordinate in ('s','rho'):
        save(p.profiles('toroidal_current', coordinate=coordinate, bins=80),
             f'profile_enclosed_toroidal_current_{coordinate}')
    history, _ = p.history(last_inner=True)
    magnetic_history = p.magnetic_history()
    available = [key for key in METRICS if key in history or key in magnetic_history]
    ordinary = [key for key in available if not key.startswith('divb_ad_')]
    for index in range(0, len(ordinary), 4):
        save(p.time_series(ordinary[index:index+4], ramp_end=0),
             f'convergence_stepb_{index//4+1:02d}')
    for field in ('vacuum','response','total'):
        keys = [f'divb_ad_{field}_{suffix}' for suffix in ('mean_abs','mean_normalized','rms','max')]
        keys = [key for key in keys if key in magnetic_history]
        if keys:
            save(p.time_series(keys, ramp_end=0), f'convergence_ad_{field}')
    log('stored_diagnostics', available=available, missing=sorted(set(METRICS)-set(available)))


def summary(p):
    history, _ = p.history(last_inner=True)
    available = [key for key in METRICS if key in history or key in p.magnetic_history()]
    events = [json.loads(line) for line in (RUN/'progress.jsonl').read_text().splitlines()]
    rows = [dict(r, outer_step=r['diagnostic']['outer_step']) for r in events
            if r['event']=='outer_complete' and r['diagnostic']['outer_step']<=50]
    assert len(rows) == 50 and any(r['event']=='finished' for r in events)
    fig, axes = plt.subplots(3,1,figsize=(9.5,10),layout='constrained')
    for axis, key in zip(axes, ['Step-A','Step-B','outer_elapsed_s'], strict=True):
        values = [r[key] if key=='outer_elapsed_s' else r['stage_seconds'][key] for r in rows]
        axis.plot([r['outer_step'] for r in rows], values, '.-',ms=3)
        axis.set(xlabel='Completed outer iteration',ylabel='Wall-clock time [s]',title=key)
        axis.grid(alpha=.25)
    fig.suptitle('NCSX | initial VMEC | scale_after=false | 50 completed outer iterations')
    fig.savefig(FIG/'convergence_wall_clock_timings.png',dpi=300)
    plt.close(fig)
    (OUT/'run_summary.json').write_text(json.dumps(dict(
        version=hint_debug.__version__, outer_step=50, record=int(p.record),
        source=str(p.path), initialization=[r for r in events if r['event']=='initialization_complete'],
        last=rows[-1], finished=[r for r in events if r['event']=='finished'],
        wall_clock_steps=rows, fields=list(FIELDS), metrics=available,
    ),indent=2)+'\n')


def histories(p):
    weights = np.broadcast_to(p.grid.r[:,None,None],p.grid.shape)
    names = ['speed','force_residual','force_residual_relative','pressure','field_strength',
             'response_field_strength','velocity_change_rate','speed_change_rate']
    with nc.Dataset(p.path) as ds:
        indices = complete_indices(ds['equilibrium'],'record_complete','time')
    assert len(indices)==51
    cached=OUT/'checkpoint_reductions.json'
    rows=json.loads(cached.read_text()) if cached.exists() else []
    if rows:
        assert [r['outer'] for r in rows]==list(range(51))
    for n,index in enumerate([] if rows else indices):
        item = p if index==p.record else p._frame(int(index))
        row={'outer':int(item.state.outer_step)}
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
        rows.append(row)
        log('history_progress', outer=row['outer'])
    (OUT/'checkpoint_reductions.json').write_text(json.dumps(rows,indent=2)+'\n')
    for title,quantities,mode in [
        ('means',['speed','force_residual','force_residual_relative'],'mean'),
        ('rms',['speed','force_residual','force_residual_relative'],'rms'),
        ('peaks',['pressure','field_strength','response_field_strength','speed'],'max'),
        ('field_means',['pressure','field_strength','response_field_strength'],'mean'),
        ('velocity_change_rate',['velocity_change_rate','speed_change_rate'],'rms'),
    ]:
        fig,axes=plt.subplots(len(quantities),1,figsize=(9.5,3.2*len(quantities)),
                              squeeze=False,layout='constrained')
        for axis,name in zip(axes[:,0],quantities,strict=True):
            for scope,color in [('wall','#176b91'),('plasma','#bf4b28')]:
                values=[r[f'{name}_{scope}_{mode}'] for r in rows]
                axis.plot([r['outer'] for r in rows],values,color=color,lw=1.2,
                          label='Inside first wall' if scope=='wall' else 'Inside wall, evolving 0<=s<1')
            if name.startswith('force_'):
                axis.set_yscale('log')
            axis.set(xlabel='Completed outer iteration',
                     ylabel=f'{FIELDS[name].label}\n[{FIELDS[name].units}]',title=mode.upper())
            axis.grid(which='both',alpha=.2)
            axis.legend(fontsize=8)
        fig.suptitle(f'NCSX | outer 0-50 | scale_after=false | volume weights R | {title}')
        fig.savefig(FIG/f'convergence_checkpoint_{title}.png',dpi=300)
        plt.close(fig)


def iota(p):
    rows=[]
    for phi in p.angles():
        log('iota_start',phi_degrees=float(np.degrees(phi)),seeds=len(SEED_S))
        row=p.rotational_transform_data(angles=[phi],seed_s=SEED_S,crossings=512,
              toroidal_steps=128,chunk_crossings=32,rtol=1e-8,atol=1e-10,
              convergence_tolerance=.002,surface_tolerance=.02)[0]
        rows.append(row)
        finite=np.isfinite(row['iota'])
        resolved=finite&row['converged']&row['surface_resolved']
        log('iota_done',phi_degrees=float(np.degrees(phi)),finite=int(finite.sum()),
            resolved=int(resolved.sum()),requested=len(SEED_S),axis_closure_m=float(row['axis_closure_m']))
    np.savez_compressed(OUT/'iota_data.npz',seed_s_initial=SEED_S,**{
        f'section_{i}_{key}':row[key] for i,row in enumerate(rows)
        for key in ('phi','seeds','seed_s','iota','half_window_difference','converged',
                    'surface_resolved','status','axis_closure_m')})
    for coordinate in ('s','rho','R','Z'):
        save(p.rotational_transform(data=rows,coordinate=coordinate),
             f'profile_rotational_transform_{coordinate}')
    fig,axes=plt.subplots(3,1,figsize=(9.5,11.4),layout='constrained')
    for axis,row in zip(axes,rows,strict=True):
        finite=np.isfinite(row['iota']); good=finite&row['converged']&row['surface_resolved']
        axis.errorbar(SEED_S[good],row['iota'][good],yerr=row['half_window_difference'][good],
                      fmt='o',ms=2.5,label='HINT resolved winding')
        uncertain=finite&~good
        axis.scatter(SEED_S[uncertain],row['iota'][uncertain],s=13,facecolors='none',
                     edgecolors='0.5',label='Finite; convergence/surface unresolved')
        vs,vi=p.vmec.iota; orientation,offset=p.vmec.winding_convention
        axis.plot(vs,orientation*vi+offset,'--',color='C3',label='Initial VMEC geometric winding')
        axis.set(xlim=(0,1),xlabel='Initial VMEC normalized toroidal flux s at launch',
                 ylabel='Geometric R-Z winding [1]',title=f'phi = {np.degrees(row["phi"]):.1f} deg')
        axis.grid(alpha=.25); axis.legend(fontsize=8)
    fig.suptitle('HINT-debug outer 50 | dense initial-VMEC-s scan | component interpolation')
    fig.savefig(FIG/'profile_rotational_transform_initial_vmec_s.png',dpi=300)
    plt.close(fig)


def existing(p):
    final=RUN/'final-poincare-step050-wall-coverage'
    initial=RUN/'initial-poincare-component'
    for old,new in [('final_poincare_wall_coverage','poincare_final_three_sections'),
                    *[(f'final_poincare_phi_{v:03d}',f'poincare_final_phi_{v:03d}') for v in (0,30,60)]]:
        shutil.copy2(final/(old+'.png'),FIG/(new+'.png'))
    for old,new in [('initial_poincare_domain','poincare_initial_three_sections'),
                    *[(f'initial_poincare_domain_phi_{v:03d}',f'poincare_initial_phi_{v:03d}') for v in (0,30,60)]]:
        shutil.copy2(initial/(old+'.png'),FIG/(new+'.png'))
    for origin,name in [(final/'plot_metadata.json','poincare_final_metadata.json'),
                        (initial/'plot_metadata.json','poincare_initial_metadata.json')]:
        shutil.copy2(origin,OUT/name)
    log('existing_poincare_copied')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=['all','remaining','static','sections','histories','iota','existing','summary'])
    args=parser.parse_args()
    p=frame()
    log('loaded',version=hint_debug.__version__,outer=50,record=int(p.record))
    phases = ['existing','static','summary','histories','iota'] if args.phase=='all' else (
        ['summary','histories','iota'] if args.phase=='remaining' else [args.phase])
    for phase in phases:
        globals()[phase](p)
        p.check_stable()
        log('phase_complete',phase=phase)
    log('complete',figures=len(list(FIG.glob('*.png'))))
