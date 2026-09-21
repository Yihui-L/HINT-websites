"""Final-field interpolant divergence, with independent extended-precision derivatives."""
import json
import os
from pathlib import Path
os.environ.update(MPLBACKEND='Agg',JAX_ENABLE_X64='true',XLA_PYTHON_CLIENT_PREALLOCATE='false')
import matplotlib.pyplot as plt
import numpy as np
from hint_debug_plotting import HintPlots
from hint_debug.interpolation import FieldSampler, interpolation_probe_points, magnetic_divergence_statistics

CASE=Path('/root/LYH-HINT/cases/ncsx-debug')
OUT=(CASE/'run/postprocess-step050-complete').resolve()
p=HintPlots(CASE/'run/hint_debug_ncsx_vmec.nc',outer_step=50,backend='gpu',engine='jax')
assert p.backend.magnetic_interpolation=='component'
g=p.grid
ids=np.flatnonzero(p.prepared.wall.mask)
ids=ids[np.unique(np.linspace(0,len(ids)-1,min(32768,len(ids)),dtype=int))]
i,j,k=np.unravel_index(ids,g.shape)
points={'nodes_wall':np.column_stack((g.r[i],g.z[j],g.phi[k])),
        'offgrid_wall':interpolation_probe_points(g,p.prepared.wall,maximum=32768)}
result={'outer_step':50,'interpolation':'component','derivative':'float64 JAX jacfwd',
        'units':'T/m','independent_precision_bits':int(np.finfo(np.longdouble).nmant+1),
        'meaning':'Derivatives of the actual component interpolant; not continuous source-field divergence.',
        'fields':{}}


def independent(payload,pts):
    data,origin,spacing,bounds,background=payload
    shape=data.shape[:3]
    scaled=(np.asarray(pts,dtype=np.longdouble)-np.asarray(origin,dtype=np.longdouble))/np.asarray(spacing,dtype=np.longdouble)
    indices=[]; weights=[]; derivatives=[]
    for axis in range(3):
        x=scaled[:,axis]
        if axis==2:
            x=x%shape[axis]
        start=np.floor(x).astype(int)-1
        if axis!=2:
            start=np.clip(start,0,shape[axis]-4)
        t=x-start
        weights.append(np.stack((-(t-1)*(t-2)*(t-3)/6,t*(t-2)*(t-3)/2,
                                 -t*(t-1)*(t-3)/2,t*(t-1)*(t-2)/6),axis=-1))
        derivatives.append(np.stack((-(3*t*t-12*t+11)/6,(3*t*t-10*t+6)/2,
                                      -(3*t*t-8*t+3)/2,(3*t*t-6*t+2)/6),axis=-1)/spacing[axis])
        ix=start[:,None]+np.arange(4)
        indices.append(ix%shape[axis] if axis==2 else ix)
    local=np.asarray(data[indices[0][:,:,None,None],indices[1][:,None,:,None],
                          indices[2][:,None,None,:],:],dtype=np.longdouble)
    def contraction(w):
        return np.einsum('nijkc,ni,nj,nk->nc',local,*w)
    b=contraction(weights)
    jac=[]
    for axis in range(3):
        w=list(weights);w[axis]=derivatives[axis];jac.append(contraction(w))
    return jac[0][:,0]+b[:,0]/pts[:,0]+jac[2][:,1]/pts[:,0]+jac[1][:,2]


for name,field in [('vacuum',p.prepared.vacuum_field_t),
                   ('response',p.state.total_field-p.prepared.vacuum_field_t),
                   ('total',p.state.total_field)]:
    sampler=FieldSampler(g,p.prepared.wall,field,backend=p.backend,hardware='gpu')
    record={}
    for scope,pts in points.items():
        b,div=sampler.magnetic.values_and_divergence(pts)
        b,div=np.asarray(b),np.asarray(div)
        record[scope]=magnetic_divergence_statistics(g,pts,b,div)
        record[scope]['minimum_abs_t_per_m']=float(np.min(np.abs(div)))
        if scope=='offgrid_wall':
            subset=np.arange(0,len(pts),max(1,len(pts)//2048))[:2048]
            reference=independent(sampler.magnetic.representation.payload,pts[subset])
            error=np.abs(np.asarray(div[subset],dtype=np.longdouble)-reference)
            record['independent_polynomial_check']={
                'samples':len(subset),'mean_abs_difference_t_per_m':float(error.mean()),
                'max_abs_difference_t_per_m':float(error.max()),
                'reference_mean_abs_t_per_m':float(np.abs(reference).mean()),
                'reference_max_abs_t_per_m':float(np.abs(reference).max()),
            }
    result['fields'][name]=record
    print(json.dumps({name:record}),flush=True)
p.check_stable()
(OUT/'final_ad_precision.json').write_text(json.dumps(result,indent=2)+'\n')
fig,axes=plt.subplots(3,1,figsize=(9,10),layout='constrained')
x=np.arange(3)
for axis,key,label in zip(axes,['divergence_relative_mean','divergence_mean_abs','divergence_max'],
                         ['Mean normalized absolute divergence [1]','Mean absolute divergence [T/m]',
                          'Maximum sampled absolute divergence [T/m]'],strict=True):
    for shift,scope,title in [(-.18,'nodes_wall','32768 wall-interior nodes'),(.18,'offgrid_wall','32768 off-grid wall probes')]:
        axis.bar(x+shift,[result['fields'][name][scope][key] for name in ('vacuum','response','total')],
                 width=.36,label=title)
    axis.set_xticks(x,['Vacuum','Response','Total']);axis.set_yscale('log')
    axis.set_ylabel(label);axis.legend(fontsize=8);axis.grid(axis='y',alpha=.25)
fig.suptitle('NCSX | outer 50 | float64 JAX AD of actual component interpolant\n'
             'No finite-difference step; not an analytic-source divergence test',fontsize=11)
fig.savefig(OUT/'figures/convergence_final_divergence_precision.png',dpi=300)
plt.close(fig)
print('COMPLETE',flush=True)
