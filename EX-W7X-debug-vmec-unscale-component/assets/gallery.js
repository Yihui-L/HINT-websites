"use strict";

const groups = ["poincare", "section", "profile", "convergence"];
const labelMap = {
  pressure: "压强", s: "演化 s 标签", rho: "演化 ρ 标签",
  field_strength: "总磁场强度", response_field_strength: "响应磁场强度",
  vacuum_field_strength: "真空磁场强度", speed: "流速大小",
  velocity_change_rate: "流速变化率", speed_change_rate: "速度大小变化率",
  force_residual: "力残差大小", force_residual_relative: "当地相对力残差",
  lorentz_force: "洛伦兹力大小", pressure_gradient: "压强梯度大小",
  parallel_pressure_gradient: "平行压强梯度", current_density: "响应电流密度大小",
  toroidal_current_density: "环向响应电流密度",
  parallel_current_density: "平行响应电流密度",
  divergence_b: "总磁场散度", divergence_b_abs: "总磁场散度绝对值",
  divergence_b_response: "响应磁场散度",
  divergence_b_response_abs: "响应磁场散度绝对值",
  divergence_b_vacuum: "真空磁场散度",
  divergence_b_vacuum_abs: "真空磁场散度绝对值",
  field_r: "总场 BR", field_phi: "总场 Bφ", field_z: "总场 BZ",
  response_field_r: "响应场 BR", response_field_phi: "响应场 Bφ",
  response_field_z: "响应场 BZ", velocity_r: "径向流速",
  velocity_phi: "环向流速", velocity_z: "垂向流速",
  toroidal_current: "包围环向电流", enclosed_toroidal_current: "包围环向电流",
  rotational_transform: "旋转变换"
};
const diagnosticLabels = {
  evolution_force: "力残差演化", evolution_divergence: "归一化散度演化",
  evolution_energy: "动能与响应磁能", evolution_pressure_speed: "压强与流速峰值",
  evolution_divergence_ad: "总场插值器 AD 散度",
  evolution_divergence_fd4: "总场网格 FD4 散度",
  evolution_timing: "外迭代耗时",
  convergence_stepb_01: "Step-B 诊断 · 1", convergence_stepb_02: "Step-B 诊断 · 2",
  convergence_stepb_03: "Step-B 诊断 · 3",
  convergence_ad_vacuum: "真空场插值器 AD 散度",
  convergence_ad_response: "响应场插值器 AD 散度",
  convergence_ad_total: "总场插值器 AD 散度",
  convergence_fd4_vacuum: "真空场网格 FD4 散度",
  convergence_fd4_response: "响应场网格 FD4 散度",
  convergence_fd4_total: "总场网格 FD4 散度",
  convergence_checkpoint_means: "检查点加权均值",
  convergence_checkpoint_rms: "检查点加权 RMS",
  convergence_checkpoint_peaks: "检查点峰值",
  convergence_checkpoint_field_means: "场与压强加权均值",
  convergence_checkpoint_velocity_change_rate: "速度变化率",
  convergence_final_divergence_precision: "末态插值器散度精度"
};

function classify(name) {
  if (name.startsWith("poincare_")) return "poincare";
  if (name.startsWith("section_")) return "section";
  if (name.startsWith("profile_")) return "profile";
  if (name.startsWith("convergence_") || name.startsWith("evolution_")) return "convergence";
  return null;
}

function caption(name, group) {
  const stem = name.replace(/\.png$/, "").replace(/_step050$/, "");
  if (group === "section") {
    const key = stem.replace(/^section_/, "");
    return { title: labelMap[key] || key.replaceAll("_", " "), detail: key };
  }
  if (group === "profile") {
    const match = stem.match(/^profile_(.+?)_(initial_vmec_s|rho|phi|R|Z|s)$/);
    if (match) {
      const variable = labelMap[match[1]] || match[1].replaceAll("_", " ");
      return { title: `${variable} / ${match[2]}`, detail: stem.replace(/^profile_/, "") };
    }
  }
  if (group === "poincare") {
    const initial = stem.includes("step000");
    const plane = stem.match(/phi(\d{3})/);
    return { title: `${initial ? "第 0 步" : "第 50 步"}${plane ? ` / ${Number(plane[1])}°` : " / 三截面"}`,
             detail: initial ? "初始化总磁场" : "未收敛的末态总磁场" };
  }
  return { title: diagnosticLabels[stem] || stem.replaceAll("_", " "), detail: stem };
}

function figure(entry, group) {
  const file = entry.path.split("/").at(-1);
  const label = caption(file, group);
  const wrapper = document.createElement("figure");
  const text = document.createElement("figcaption");
  const title = document.createElement("strong");
  title.textContent = label.title;
  const detail = document.createElement("span");
  detail.textContent = label.detail;
  text.append(title, detail);
  const link = document.createElement("a");
  link.href = `./${entry.path}`;
  const img = document.createElement("img");
  img.src = link.href;
  img.loading = "lazy";
  img.decoding = "async";
  img.alt = `W7-X EIM HINT-debug ${label.title}，${label.detail}`;
  img.width = entry.pixels[0];
  img.height = entry.pixels[1];
  link.append(img);
  wrapper.append(text, link);
  return wrapper;
}

fetch("./result_manifest.json")
  .then(response => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.json(); })
  .then(manifest => {
    const counts = Object.fromEntries(groups.map(group => [group, 0]));
    for (const entry of manifest.images) {
      const group = classify(entry.path.split("/").at(-1));
      if (!group) continue;
      document.querySelector(`[data-gallery-group="${group}"]`).append(figure(entry, group));
      counts[group] += 1;
    }
    document.querySelector("#gallery-status").textContent =
      `共 ${manifest.image_count} 张图片 · 庞加莱 ${counts.poincare} · 二维截面 ${counts.section} · 剖面 ${counts.profile} · 演化诊断 ${counts.convergence}`;
  })
  .catch(error => {
    document.querySelector("#gallery-status").textContent = `图集清单读取失败：${error.message}`;
  });
