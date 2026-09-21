"""Case-only direct-source derivatives; do not interpolate the HINT B grid."""
import hashlib
import json
import os
from pathlib import Path
from time import perf_counter

os.environ.update(JAX_ENABLE_X64='true', XLA_PYTHON_CLIENT_PREALLOCATE='false',
                  JAX_USE_SIMPLIFIED_JAXPR_CONSTANTS='true', OMP_NUM_THREADS='4',
                  OPENBLAS_NUM_THREADS='4')
import jax
import jax.numpy as jnp
import numpy as np
from scipy.spatial import cKDTree
from hint_debug.storage import UnifiedStore
from hint_debug.preprocess.coils import CoilSet, CoilPotential
from hint_debug.preprocess.vmec import VMECReader
from hint_debug.preprocess.vmec_field import VMECPlasmaFieldBuilder
from hint_debug.preprocess.vmec_jax import VMECFourierEvaluator, _cartesian
from hint_debug.preprocess.casing import CasingQuadrature, _panel_values

CASE = Path('/root/LYH-HINT/cases/ncsx-debug')
OUT = CASE / 'run/postprocess-step050-complete/initial_source_ad.json'
start = perf_counter()
prepared, norm = UnifiedStore(CASE/'run/hint_debug_ncsx_vmec.nc').load_prepared()
g = prepared.grid
reader = VMECReader(CASE/'inputs/wout_ncsx_c09r00_free_nonnegative.nc')
builder = VMECPlasmaFieldBuilder(reader, reader.geometry())
builder.field.accelerator = VMECFourierEvaluator(builder.field)
ev = builder.field.accelerator
source = CoilPotential(CoilSet.read(CASE/'inputs/ncsx_coils.txt'),
                       prepared.coil_current_density_a_mm2, hardware='gpu', refinement=3)
coil_kernel = source._device_function(True)

def coil_one(x):
    return coil_kernel(x[None], source._device_sources)[0]

def wout_one(q):
    x, b = ev._evaluate(q[:1], q[1:2], q[2:3])
    return x[0], _cartesian(b, q[2:3])[0]

def wout_xyz_jacobian(q):
    x, b = wout_one(q)
    dx, db = jax.jacfwd(wout_one)(q)
    return x, b, db @ jnp.linalg.inv(dx)

coil_jac = jax.jit(jax.vmap(jax.jacfwd(coil_one)))
coil_values = jax.jit(jax.vmap(coil_one))
result = dict(version='2.2.0', outer_step=0, dtype='float64',
              method='JAX analytic derivatives of continuous source expressions, not HINT-grid interpolation',
              source_refinement=3, fields={},
              limitations=['Finite samples are not a global bound.',
                  'VC derivatives use fixed 24-point Gauss source panels away from LCFS; field values are checked against adaptive quadrature.',
                  'Wout reconstruction includes the production radial coefficient interpolation.',
                  'No classical analytic divergence is assigned at a discontinuous LCFS interface.'])

def record(name, xyz, b, jac):
    b, jac = np.asarray(b), np.asarray(jac)
    div = np.trace(jac, axis1=-2, axis2=-1)
    h = np.minimum(min(g.dr, g.dz), np.linalg.norm(xyz[:,:2], axis=1)*g.dphi)
    ab = np.abs(div)
    result['fields'][name] = dict(samples=len(div), mean_abs_t_m=float(ab.mean()),
        max_abs_t_m=float(ab.max()), rms_t_m=float(np.sqrt(np.mean(div**2))),
        mean_normalized=float(np.mean(h*ab)/np.mean(np.linalg.norm(b, axis=1))),
        p95_t_m=float(np.quantile(ab,.95)))
    print(json.dumps({name:result['fields'][name], 'elapsed_s':perf_counter()-start}), flush=True)

ids = np.flatnonzero(prepared.wall.mask)
ids = ids[np.linspace(0,len(ids)-1,512,dtype=int)]
i,j,k = np.unravel_index(ids,g.shape)
wall_xyz = np.column_stack((g.r[i]*np.cos(g.phi[k]),g.r[i]*np.sin(g.phi[k]),g.z[j]))
b0 = np.asarray(coil_values(wall_xyz)); d0 = np.asarray(coil_jac(wall_xyz))
record('vacuum_wall',wall_xyz,b0,d0)
c,s = np.cos(g.phi[k]),np.sin(g.phi[k])
stored = prepared.vacuum_field_t[i,j,k]
stored_xyz = np.column_stack((stored[:,0]*c-stored[:,1]*s,stored[:,0]*s+stored[:,1]*c,stored[:,2]))
result['vacuum_saved_grid_max_vector_difference_t'] = float(np.max(np.linalg.norm(stored_xyz-b0,axis=1)))

rng = np.random.default_rng(221)
queries = np.column_stack((rng.uniform(.02,.98,256),rng.uniform(0,2*np.pi,256),
                           rng.uniform(0,2*np.pi/g.nfp,256)))
x, b, db = jax.jit(jax.vmap(wout_xyz_jacobian))(queries)
x,b,db = map(np.asarray,(x,b,db))
b0,d0 = np.asarray(coil_values(x)),np.asarray(coil_jac(x))
record('total_wout_interior',x,b,db)
record('response_wout_minus_coils_interior',x,b-b0,db-d0)

np_,nt = builder._panel_counts(g)
quad = CasingQuadrature(builder.field.surface,np_,nt,orders=(16,24))
data = quad.base_data[quad.high_order]
surface_points = np.asarray(data[0]).reshape(-1,3)
exterior_ids = np.flatnonzero(prepared.wall.mask & (prepared.initial_s>=1))
exterior_ids = exterior_ids[np.linspace(0,len(exterior_ids)-1,min(4096,len(exterior_ids)),dtype=int)]
i,j,k = np.unravel_index(exterior_ids,g.shape)
ext = np.column_stack((g.r[i]*np.cos(g.phi[k]),g.r[i]*np.sin(g.phi[k]),g.z[j]))
dist = cKDTree(surface_points).query(ext)[0]
ext = ext[dist>.08]
ext = ext[np.linspace(0,len(ext)-1,min(64,len(ext)),dtype=int)]
assert len(ext)>=32

def casing_one(x):
    return jnp.sum(_panel_values(jnp,x[None],jnp.zeros((1,3)),*data),axis=1)[0]

bc = np.asarray(jax.jit(jax.vmap(casing_one))(ext))
dc = np.asarray(jax.jit(jax.vmap(jax.jacfwd(casing_one)))(ext))
record('response_virtual_casing_exterior',ext,bc,dc)
b0,d0 = np.asarray(coil_values(ext)),np.asarray(coil_jac(ext))
record('total_coils_plus_casing_exterior',ext,b0+bc,d0+dc)
adaptive = quad.evaluate(ext,np.zeros_like(ext),np.zeros(len(ext),bool),np.zeros(len(ext),bool))
result['vc_adaptive_field_max_difference_t'] = float(np.max(np.linalg.norm(bc-adaptive,axis=1)))
result['vc_panels'] = [np_,nt]
result['exterior_min_sampled_surface_distance_m'] = float(cKDTree(surface_points).query(ext)[0].min())
result['seconds'] = perf_counter()-start
result['input_sha256'] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
    [CASE/'inputs/ncsx_coils.txt',reader.path]}
OUT.write_text(json.dumps(result,indent=2)+'\n')
print('COMPLETE',OUT,result['seconds'],flush=True)
