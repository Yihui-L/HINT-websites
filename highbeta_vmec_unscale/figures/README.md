# Outer-100 PNG index

84 PNG figures, 300 dpi; HINT-debug 0.8.8; VMEC start; scale_after=false.

All spatial data: completed outer iteration 100. Histories: available iterations 0-100.
See [case README](../README.md) for units, averaging, masks, input hashes, and limitations.

## Field-line trace diagnostics

Each iota value uses one theta=0 seed per initial VMEC s per section, not a multi-seed average.
Different sections are kept separate. All trace lengths below are FIELD periods, not full toroidal turns.

| phi [deg] | iota seeds | finite estimates | convergence + section-resolution pass | axis closure [m] |
|---|---:|---:|---:|---:|
| 0.0 | 191 | 90 | 24 | 8.69738e-08 |
| 30.0 | 191 | 58 | 34 | 5.43246e-08 |
| 60.0 | 191 | 71 | 53 | 7.77276e-08 |

Iota: 512 field periods, 128 toroidal substeps per period; initial VMEC s=0.0001-0.9999.
Finite but unqualified estimates use separate markers; failed traces are not filled by interpolation.

Axis searches met the grid-aware tolerance, not the stricter nonlinear tolerance; warnings were retained.
Dense launch coverage does not imply that reliable magnetic-surface iota exists throughout that range.

| phi [deg] | accepted Poincare seeds | valid return points | seeds surviving to last return |
|---|---:|---:|---:|
| 0.0 | 2308 | 116281 | 155 |
| 30.0 | 1143 | 121785 | 162 |
| 60.0 | 844 | 152332 | 202 |

Poincare: up to 600 field periods per line; domain/wall exits are retained as trace termination.

## Reading the plots

- Sections: phi=0, 30, 60 deg; wall, box, and VMEC axis/flux surfaces overlaid.
- Local force ratio: |J1 x B - grad(p)| / max(|J1 x B|, |grad(p)|), masked near zero denominator.
- Checkpoint mean/RMS histories: R-weighted cylindrical volume reductions, wall and evolving s<1 masks.
- Step-B histories: stored normalized diagnostics at the last inner step of each outer iteration.
- SI response-divergence history: arithmetic statistics over the physical box, not volume statistics.
- Profile s/rho bins: section-area averages of evolving HINT labels, not exact flux-surface averages.
- Iota initial_vmec_s plot: INITIAL launch label; other iota s/rho plots use evolving HINT labels.
- No pressure-ramp end marker: vmec start has no pressure ramp.

## Two-dimensional sections

- [section_current_density](section_current_density.png)
- [section_divergence_b](section_divergence_b.png)
- [section_divergence_b_abs](section_divergence_b_abs.png)
- [section_divergence_b_response](section_divergence_b_response.png)
- [section_divergence_b_response_abs](section_divergence_b_response_abs.png)
- [section_divergence_b_vacuum](section_divergence_b_vacuum.png)
- [section_divergence_b_vacuum_abs](section_divergence_b_vacuum_abs.png)
- [section_field_phi](section_field_phi.png)
- [section_field_r](section_field_r.png)
- [section_field_strength](section_field_strength.png)
- [section_field_z](section_field_z.png)
- [section_force_residual](section_force_residual.png)
- [section_force_residual_relative](section_force_residual_relative.png)
- [section_lorentz_force](section_lorentz_force.png)
- [section_parallel_current_density](section_parallel_current_density.png)
- [section_parallel_pressure_gradient](section_parallel_pressure_gradient.png)
- [section_pressure](section_pressure.png)
- [section_pressure_gradient](section_pressure_gradient.png)
- [section_response_field_phi](section_response_field_phi.png)
- [section_response_field_r](section_response_field_r.png)
- [section_response_field_strength](section_response_field_strength.png)
- [section_response_field_z](section_response_field_z.png)
- [section_rho](section_rho.png)
- [section_s](section_s.png)
- [section_speed](section_speed.png)
- [section_speed_change_rate](section_speed_change_rate.png)
- [section_toroidal_current_density](section_toroidal_current_density.png)
- [section_vacuum_field_strength](section_vacuum_field_strength.png)
- [section_velocity_change_rate](section_velocity_change_rate.png)
- [section_velocity_phi](section_velocity_phi.png)
- [section_velocity_r](section_velocity_r.png)
- [section_velocity_z](section_velocity_z.png)

## Profiles and rotational transform

- [profile_enclosed_toroidal_current_rho](profile_enclosed_toroidal_current_rho.png)
- [profile_enclosed_toroidal_current_s](profile_enclosed_toroidal_current_s.png)
- [profile_field_strength_R](profile_field_strength_R.png)
- [profile_field_strength_Z](profile_field_strength_Z.png)
- [profile_field_strength_phi](profile_field_strength_phi.png)
- [profile_field_strength_rho](profile_field_strength_rho.png)
- [profile_field_strength_s](profile_field_strength_s.png)
- [profile_force_residual_R](profile_force_residual_R.png)
- [profile_force_residual_Z](profile_force_residual_Z.png)
- [profile_force_residual_phi](profile_force_residual_phi.png)
- [profile_force_residual_relative_R](profile_force_residual_relative_R.png)
- [profile_force_residual_relative_Z](profile_force_residual_relative_Z.png)
- [profile_force_residual_relative_phi](profile_force_residual_relative_phi.png)
- [profile_force_residual_relative_rho](profile_force_residual_relative_rho.png)
- [profile_force_residual_relative_s](profile_force_residual_relative_s.png)
- [profile_force_residual_rho](profile_force_residual_rho.png)
- [profile_force_residual_s](profile_force_residual_s.png)
- [profile_pressure_R](profile_pressure_R.png)
- [profile_pressure_Z](profile_pressure_Z.png)
- [profile_pressure_phi](profile_pressure_phi.png)
- [profile_pressure_rho](profile_pressure_rho.png)
- [profile_pressure_s](profile_pressure_s.png)
- [profile_rotational_transform_R](profile_rotational_transform_R.png)
- [profile_rotational_transform_Z](profile_rotational_transform_Z.png)
- [profile_rotational_transform_initial_vmec_s](profile_rotational_transform_initial_vmec_s.png)
- [profile_rotational_transform_rho](profile_rotational_transform_rho.png)
- [profile_rotational_transform_s](profile_rotational_transform_s.png)
- [profile_speed_R](profile_speed_R.png)
- [profile_speed_Z](profile_speed_Z.png)
- [profile_speed_phi](profile_speed_phi.png)
- [profile_speed_rho](profile_speed_rho.png)
- [profile_speed_s](profile_speed_s.png)
- [profile_toroidal_current_density_R](profile_toroidal_current_density_R.png)
- [profile_toroidal_current_density_Z](profile_toroidal_current_density_Z.png)
- [profile_toroidal_current_density_phi](profile_toroidal_current_density_phi.png)
- [profile_toroidal_current_density_rho](profile_toroidal_current_density_rho.png)
- [profile_toroidal_current_density_s](profile_toroidal_current_density_s.png)

## Convergence and timings

- [convergence_checkpoint_field_means](convergence_checkpoint_field_means.png)
- [convergence_checkpoint_means](convergence_checkpoint_means.png)
- [convergence_checkpoint_peaks](convergence_checkpoint_peaks.png)
- [convergence_checkpoint_rms](convergence_checkpoint_rms.png)
- [convergence_checkpoint_velocity_change_rate](convergence_checkpoint_velocity_change_rate.png)
- [convergence_response_divergence_si](convergence_response_divergence_si.png)
- [convergence_stepb_01](convergence_stepb_01.png)
- [convergence_stepb_02](convergence_stepb_02.png)
- [convergence_stepb_03](convergence_stepb_03.png)
- [convergence_wall_clock_timings](convergence_wall_clock_timings.png)

## Poincare sections

- [poincare_000.0deg](poincare_000.0deg.png)
- [poincare_030.0deg](poincare_030.0deg.png)
- [poincare_060.0deg](poincare_060.0deg.png)
- [poincare_outboard_detail](poincare_outboard_detail.png)
- [poincare_three_sections](poincare_three_sections.png)
