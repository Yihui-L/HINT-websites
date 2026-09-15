"use strict";
const chapters = [...document.querySelectorAll(".chapter")];
const navigation = [...document.querySelectorAll("nav a")];
const search = document.querySelector("#global-search");
const sidebar = document.querySelector("#sidebar");
const menu = document.querySelector("#menu-toggle");
const contains = (text, query) => query.toLowerCase().trim().split(/\s+/).every(word => text.toLowerCase().includes(word));
search.addEventListener("input", () => {
  const query = search.value.trim();
  let count = 0;
  chapters.forEach((chapter, index) => {
    chapter.hidden = query !== "" && !contains(chapter.textContent, query);
    navigation[index].hidden = chapter.hidden;
    if (!chapter.hidden) count++;
  });
  document.querySelector("#search-status").textContent = query ? `${count} / ${chapters.length} 个章节` : "";
  document.querySelector("#no-results").hidden = count !== 0;
});
menu.addEventListener("click", () => {
  const open = sidebar.classList.toggle("open");
  menu.setAttribute("aria-expanded", String(open));
});
navigation.forEach(link => link.addEventListener("click", () => {
  sidebar.classList.remove("open"); menu.setAttribute("aria-expanded", "false");
}));
document.addEventListener("keydown", event => {
  if (event.key === "Escape") { sidebar.classList.remove("open"); menu.setAttribute("aria-expanded", "false"); }
});
for (const table of document.querySelectorAll(".parameters")) {
  const section = table.closest("section");
  const input = section.querySelector(".param-search");
  const select = section.querySelector(".param-version");
  const rows = [...table.tBodies[0].rows];
  function filter() {
    let count = 0;
    for (const row of rows) {
      const different = row.cells[1].textContent !== row.cells[2].textContent;
      const version = select.value;
      const matchesVersion = version === "all" || (version === "different" ? different : row.dataset.version.split(" ").includes(version));
      row.hidden = !matchesVersion || !contains(row.textContent, input.value);
      if (!row.hidden) count++;
    }
    section.querySelector(".param-count").textContent = `${count} / ${rows.length} 项`;
  }
  input.addEventListener("input", filter); select.addEventListener("change", filter); filter();
}
let scrollPending = false;
function updateCurrentChapter() {
  const visible = chapters.filter(chapter => !chapter.hidden);
  let current = visible[0];
  for (const chapter of visible) {
    if (chapter.getBoundingClientRect().top <= Math.max(130, innerHeight * .25)) current = chapter;
  }
  navigation.forEach(link => link.classList.toggle("active", current && link.hash === `#${current.id}`));
  scrollPending = false;
}
addEventListener("scroll", () => {
  if (!scrollPending) { scrollPending = true; requestAnimationFrame(updateCurrentChapter); }
}, {passive:true});
search.addEventListener("input", updateCurrentChapter);
updateCurrentChapter();
