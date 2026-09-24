import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const canvas = document.getElementById("scene");
const status = document.getElementById("load-status");
const tooltip = document.getElementById("coil-tooltip");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.25;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xe8efef);
scene.add(new THREE.HemisphereLight(0xffffff, 0x7e9695, 2.3));
const sun = new THREE.DirectionalLight(0xffffff, 2.5);
sun.position.set(8, 12, 10);
scene.add(sun);
const fill = new THREE.DirectionalLight(0xb4e3df, 1.1);
fill.position.set(-9, 5, -8);
scene.add(fill);

const camera = new THREE.PerspectiveCamera(40, 1, 0.05, 100);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.07;
controls.minDistance = 1.5;
controls.maxDistance = 30;
controls.autoRotateSpeed = 0.7;

const assembly = new THREE.Group();
scene.add(assembly);
const modular = [];
const auxiliary = [];
const negligible = [];
let surface;
let cameraDistance = 8;

function toScene(xyz, offset) {
  return new THREE.Vector3(xyz[offset], xyz[offset + 2], xyz[offset + 1]);
}

function buildSurface(data) {
  const { nphi, ntheta, xyz } = data;
  const positions = new Float32Array(xyz.length);
  for (let k = 0; k < xyz.length; k += 3) {
    positions[k] = xyz[k];
    positions[k + 1] = xyz[k + 2];
    positions[k + 2] = xyz[k + 1];
  }
  const indices = new Uint32Array(nphi * ntheta * 6);
  let cursor = 0;
  for (let i = 0; i < nphi; i++) {
    for (let j = 0; j < ntheta; j++) {
      const a = i * ntheta + j;
      const b = ((i + 1) % nphi) * ntheta + j;
      const c = i * ntheta + ((j + 1) % ntheta);
      const d = ((i + 1) % nphi) * ntheta + ((j + 1) % ntheta);
      indices.set([a, b, c, c, b, d], cursor);
      cursor += 6;
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setIndex(new THREE.BufferAttribute(indices, 1));
  geometry.computeVertexNormals();
  const material = new THREE.MeshPhysicalMaterial({
    color: 0x249a87, metalness: 0.08, roughness: 0.58,
    transparent: true, opacity: 0.58, side: THREE.DoubleSide, depthWrite: false,
  });
  surface = new THREE.Mesh(geometry, material);
  surface.renderOrder = 1;
  assembly.add(surface);
}

function buildCoils(items) {
  const modularMaterial = new THREE.MeshStandardMaterial({ color: 0xc96337, metalness: 0.18, roughness: 0.48 });
  const auxiliaryMaterial = new THREE.MeshStandardMaterial({ color: 0x2d718e, metalness: 0.12, roughness: 0.55 });
  const negligibleMaterial = new THREE.MeshStandardMaterial({ color: 0x9caaa9, metalness: 0.1, roughness: 0.65 });
  for (const item of items) {
    const points = [];
    for (let k = 0; k < item.xyz.length - 3; k += 3) points.push(toScene(item.xyz, k));
    const curve = new THREE.CatmullRomCurve3(points, true, "centripetal");
    const geometry = new THREE.TubeGeometry(curve, points.length, 0.008, 5, true);
    const current = Math.abs(item.current_a);
    const group = current >= 2e5 ? modular : current >= 1e-3 ? auxiliary : negligible;
    const material = group === modular ? modularMaterial : group === auxiliary ? auxiliaryMaterial : negligibleMaterial;
    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = item.name;
    mesh.userData.currentA = item.current_a;
    assembly.add(mesh);
    group.push(mesh);
  }
}

function enableCoilTooltip() {
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  const meshes = [...modular, ...auxiliary, ...negligible];
  canvas.addEventListener("pointermove", event => {
    if (event.buttons) { tooltip.hidden = true; return; }
    const rect = canvas.getBoundingClientRect();
    pointer.set(2 * (event.clientX - rect.left) / rect.width - 1,
      1 - 2 * (event.clientY - rect.top) / rect.height);
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster.intersectObjects(meshes, false)[0];
    if (!hit) { tooltip.hidden = true; return; }
    const currentKA = hit.object.userData.currentA / 1000;
    tooltip.textContent = `${hit.object.name} · I = ${currentKA.toFixed(3)} kA`;
    tooltip.style.left = `${Math.min(event.clientX - rect.left + 12, rect.width - 220)}px`;
    tooltip.style.top = `${canvas.offsetTop + Math.max(12, event.clientY - rect.top - 32)}px`;
    tooltip.hidden = false;
  });
  canvas.addEventListener("pointerleave", () => { tooltip.hidden = true; });
}

function setView(kind) {
  controls.autoRotate = false;
  document.getElementById("auto-rotate").checked = false;
  camera.up.set(0, 1, 0);
  const direction = kind === "top" ? new THREE.Vector3(0, 1, 0.001)
    : kind === "side" ? new THREE.Vector3(0.01, 0.18, 1)
      : new THREE.Vector3(1, 0.68, 1.08);
  if (kind === "top") camera.up.set(0, 0, -1);
  camera.position.copy(direction.normalize().multiplyScalar(cameraDistance));
  camera.lookAt(0, 0, 0);
  controls.target.set(0, 0, 0);
  controls.update();
  document.querySelectorAll("[data-view]").forEach(button => {
    const selected = button.dataset.view === kind;
    button.classList.toggle("selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
}

function resize() {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  if (!width || !height) return;
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}

try {
  const response = await fetch("./assets/geometry.json");
  if (!response.ok) throw new Error(`geometry.json: HTTP ${response.status}`);
  const data = await response.json();
  buildSurface(data.surface);
  buildCoils(data.coils);
  const sphere = new THREE.Box3().setFromObject(assembly).getBoundingSphere(new THREE.Sphere());
  cameraDistance = Math.max(5.5, sphere.radius * 2.5);
  setView("iso");
  resize();
  new ResizeObserver(resize).observe(canvas);
  document.querySelectorAll("[data-view]").forEach(button => button.addEventListener("click", () => setView(button.dataset.view)));
  document.getElementById("reset-view").addEventListener("click", () => setView("iso"));
  document.getElementById("show-lcfs").addEventListener("change", event => { surface.visible = event.target.checked; });
  document.getElementById("show-aux").addEventListener("change", event => { auxiliary.forEach(mesh => { mesh.visible = event.target.checked; }); });
  document.getElementById("show-idle").addEventListener("change", event => { negligible.forEach(mesh => { mesh.visible = event.target.checked; }); });
  document.getElementById("auto-rotate").addEventListener("change", event => { controls.autoRotate = event.target.checked; });
  document.getElementById("surface-opacity").addEventListener("input", event => { surface.material.opacity = Number(event.target.value) / 100; });
  window.lucide?.createIcons();
  enableCoilTooltip();
  status.hidden = true;
  window.__viewerStats = { coilCount: data.coils.length, modularCount: modular.length, auxiliaryCount: auxiliary.length, negligibleCount: negligible.length, vertices: data.surface.xyz.length / 3, nfp: data.surface.nfp };
  window.__viewerReady = true;
  animate();
} catch (error) {
  status.textContent = `三维几何未能载入：${error.message}`;
  status.classList.add("error");
  console.error(error);
}
