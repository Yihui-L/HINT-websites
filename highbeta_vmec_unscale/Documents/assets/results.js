"use strict";
const figures = JSON.parse(document.querySelector("#figure-data").textContent);
const cards = [...document.querySelectorAll(".figure-card")];
const tabs = [...document.querySelectorAll(".category-tab")];
const search = document.querySelector("#figure-search");
const dialog = document.querySelector("#viewer");
let category = "all";
let current = null;
let opener = null;
function visibleIds() { return cards.filter(card => !card.hidden).map(card => card.dataset.id); }
function filter() {
  const words = search.value.toLowerCase().trim().split(/\s+/);
  for (const card of cards) {
    const searchable = `${card.textContent} ${card.dataset.category}`.toLowerCase();
    card.hidden = !(category === "all" || card.dataset.category === category) || !words.every(word => searchable.includes(word));
  }
  const count = visibleIds().length;
  document.querySelector("#figure-count").textContent = `${count} / ${cards.length} 张图片`;
  document.querySelector("#empty").hidden = count !== 0;
}
tabs.forEach(tab => tab.addEventListener("click", () => {
  category = tab.dataset.category;
  for (const other of tabs) { other.classList.toggle("active", other === tab); other.setAttribute("aria-pressed", String(other === tab)); }
  filter();
}));
search.addEventListener("input", filter);
function show(id) {
  current = id;
  const data = figures.find(figure => figure.id === id);
  const image = document.querySelector("#viewer-image");
  image.src = data.file; image.alt = data.title;
  document.querySelector("#viewer-title").textContent = data.title;
  document.querySelector("#viewer-caption").textContent = data.caption;
  document.querySelector("#original-link").href = data.file;
  document.querySelector(".viewer-scroll").scrollTop = 0;
  if (!dialog.open) { dialog.showModal(); document.body.classList.add("modal-open"); }
}
for (const card of cards) {
  const link = card.querySelector(".image-link");
  link.addEventListener("click", event => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault(); opener = link; show(card.dataset.id);
  });
}
function move(direction) {
  const ids = visibleIds();
  if (!ids.length) return;
  show(ids[(ids.indexOf(current) + direction + ids.length) % ids.length]);
}
document.querySelector("#prev").addEventListener("click", () => move(-1));
document.querySelector("#next").addEventListener("click", () => move(1));
document.querySelector("#close-viewer").addEventListener("click", () => dialog.close());
dialog.addEventListener("close", () => { document.body.classList.remove("modal-open"); opener?.focus(); });
dialog.addEventListener("keydown", event => {
  if (event.key === "ArrowLeft") { event.preventDefault(); move(-1); }
  if (event.key === "ArrowRight") { event.preventDefault(); move(1); }
});
filter();
