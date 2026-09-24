"use strict";

const groups = { poincare: "poincare", section: "section", profile: "profile", iota: "profile", convergence: "convergence" };

function figure(entry) {
  const wrapper = document.createElement("figure");
  const text = document.createElement("figcaption");
  const title = document.createElement("strong");
  title.textContent = entry.title;
  const detail = document.createElement("span");
  detail.textContent = entry.id;
  text.append(title, detail);

  const file = entry.file.split("/").at(-1);
  const link = document.createElement("a");
  link.href = `./figures/${file}`;
  const img = document.createElement("img");
  img.src = link.href;
  img.loading = "lazy";
  img.decoding = "async";
  img.alt = `NCSX HINT-debug ${entry.title}。${entry.caption}`;
  img.width = entry.width;
  img.height = entry.height;
  link.append(img);
  wrapper.append(text, link);
  return wrapper;
}

fetch("./Documents/docs-data/results.json")
  .then(response => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then(manifest => {
    if (manifest.version !== "2.3.0" || manifest.outer_step !== 50 || manifest.figures.length !== 93) {
      throw new Error("图像清单与本次算例不一致");
    }
    const counts = { poincare: 0, section: 0, profile: 0, convergence: 0 };
    for (const entry of manifest.figures) {
      const group = groups[entry.category];
      if (!group || !entry.file.startsWith("../figures/") || !entry.file.endsWith(entry.sha256.slice(0, 12))) {
        throw new Error(`无效的图像记录：${entry.id}`);
      }
      document.querySelector(`[data-gallery-group="${group}"]`).append(figure(entry));
      counts[group]++;
    }
    document.querySelector("#gallery-status").textContent =
      `共 ${manifest.figures.length} 张图片 · 庞加莱 ${counts.poincare} · 二维截面 ${counts.section} · 剖面与旋转变换 ${counts.profile} · 演化诊断 ${counts.convergence}`;
  })
  .catch(error => {
    document.querySelector("#gallery-status").textContent = `图集清单读取失败：${error.message}`;
  });
