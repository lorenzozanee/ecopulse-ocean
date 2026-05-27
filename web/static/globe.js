// Three.js 3D Globe — ocean data texture, click-to-inspect, layer toggles
let scene, camera, renderer, earth, markers = [], currentLayer = 'sst', isGlobeReady = false;

const LAYER_CFG = {
  sst: { label: 'SST', min: 22, max: 32 },
  chl: { label: 'Chl-a', min: 0.1, max: 4 },
  poc: { label: 'POC Flux', min: 0.2, max: 8 },
};

const TEX_SIZE = 512;
const texCanvas = document.createElement('canvas');
texCanvas.width = TEX_SIZE; texCanvas.height = TEX_SIZE / 2;
const texCtx = texCanvas.getContext('2d');
let dataTexture, globeTime = 0;

function updateOceanTexture(time, layer) {
  const w = TEX_SIZE, h = TEX_SIZE / 2, img = texCtx.createImageData(w, h), cfg = LAYER_CFG[layer];
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4, lon = (x / w) * 360 - 180, lat = 90 - (y / h) * 180;
      const nx = lon / 90, ny = lat / 60;
      const sst = 24 + 8 * Math.sin(nx * 2.7 + time * 0.3) * Math.cos(ny * 1.8 + time * 0.25)
                + 4 * Math.sin(nx * 5.3 - time * 0.5) * Math.cos(ny * 4.1 + time * 0.4);
      const chl = 0.2 + 2.5 * (0.5 + 0.5 * Math.sin(nx * 1.9 + time * 0.2 + 1.3) * Math.cos(ny * 3.3 - time * 0.3));
      const pocV = 0.5 + 5 * (0.5 + 0.5 * Math.sin(nx * 2.1 + time * 0.25 + 2) * Math.cos(ny * 3.7 - time * 0.35));
      const raw = layer === 'sst' ? sst : layer === 'chl' ? chl * 2 : pocV;
      const t = Math.max(0, Math.min(1, (raw - cfg.min) / (cfg.max - cfg.min + 0.01)));
      img.data[i] = t * 60 + (1 - t) * 10;
      img.data[i + 1] = t * 80 + (1 - t) * 25;
      img.data[i + 2] = t * 30 + (1 - t) * 90;
      img.data[i + 3] = 215;
    }
  }
  texCtx.putImageData(img, 0, 0);
  if (dataTexture) dataTexture.needsUpdate = true;
}

function initGlobe(containerId) {
  const container = document.getElementById(containerId);
  if (!container || !hasWebGL()) return;
  const W = container.clientWidth, H = container.clientHeight;

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 10);
  camera.position.set(0, 0.3, 3.2);
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(W, H);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0x334466, 1.8));
  const sun = new THREE.DirectionalLight(0xddeeff, 2.5);
  sun.position.set(2, 1, 2); scene.add(sun);

  texCtx.fillStyle = '#0a1628';
  texCtx.fillRect(0, 0, TEX_SIZE, TEX_SIZE / 2);
  dataTexture = new THREE.CanvasTexture(texCanvas);
  updateOceanTexture(0, 'sst');

  const geom = new THREE.SphereGeometry(1, 64, 48);
  const mat = new THREE.MeshPhongMaterial({ map: dataTexture, specular: 0x112233, shininess: 5 });
  earth = new THREE.Mesh(geom, mat);
  scene.add(earth);

  const atmoGeom = new THREE.SphereGeometry(1.02, 64, 48);
  const atmoMat = new THREE.MeshPhongMaterial({ color: 0x00aadd, transparent: true, opacity: 0.06, side: THREE.FrontSide });
  scene.add(new THREE.Mesh(atmoGeom, atmoMat));

  const ringGeom = new THREE.TorusGeometry(1.01, 0.003, 16, 100);
  const ringMat = new THREE.MeshBasicMaterial({ color: 0x00d4ff, transparent: true, opacity: 0.2 });
  const ring = new THREE.Mesh(ringGeom, ringMat);
  ring.rotation.x = Math.PI / 2; scene.add(ring);

  const markerGeom = new THREE.SphereGeometry(0.012, 8, 8);
  const markerMat = new THREE.MeshBasicMaterial({ color: 0x00d4ff });
  const positions = [{ lat: 15, lon: 115 }, { lat: 18, lon: 112 }, { lat: 10, lon: 118 }, { lat: 8, lon: 108 }, { lat: 20, lon: 117 }];
  for (const fp of positions) {
    const pos = latLonToVec3(fp.lat, fp.lon, 0.01);
    const mk = new THREE.Mesh(markerGeom, markerMat);
    mk.position.copy(pos);
    mk.userData = { lat: fp.lat, lon: fp.lon };
    earth.add(mk);
    markers.push(mk);
  }

  renderer.domElement.addEventListener('click', (event) => {
    const rect = renderer.domElement.getBoundingClientRect();
    const mouse = new THREE.Vector2(((event.clientX - rect.left) / rect.width) * 2 - 1, -((event.clientY - rect.top) / rect.height) * 2 + 1);
    const rc = new THREE.Raycaster(); rc.setFromCamera(mouse, camera);
    const hits = rc.intersectObject(earth);
    if (hits.length > 0) {
      const p = hits[0].point;
      const lat = Math.asin(p.y) * 180 / Math.PI;
      const lon = Math.atan2(p.z, p.x) * 180 / Math.PI;
      showTooltip(lat, lon, event.clientX, event.clientY);
    }
  });

  let dragging = false, px = 0, py = 0;
  renderer.domElement.addEventListener('pointerdown', (e) => { dragging = true; px = e.clientX; py = e.clientY; });
  window.addEventListener('pointermove', (e) => {
    if (!dragging) return;
    earth.rotation.y += (e.clientX - px) * 0.005;
    earth.rotation.x += (e.clientY - py) * 0.003;
    earth.rotation.x = Math.max(-0.5, Math.min(0.5, earth.rotation.x));
    px = e.clientX; py = e.clientY;
  });
  window.addEventListener('pointerup', () => { dragging = false; });
  renderer.domElement.addEventListener('wheel', (e) => {
    e.preventDefault();
    camera.position.z += e.deltaY * 0.002;
    camera.position.z = Math.max(1.8, Math.min(5, camera.position.z));
  }, { passive: false });

  isGlobeReady = true;
}

function showTooltip(lat, lon, cx, cy) {
  let el = document.getElementById('globe-tooltip');
  if (!el) {
    el = document.createElement('div');
    el.id = 'globe-tooltip';
    el.style.cssText = 'position:fixed;z-index:999;background:rgba(13,21,32,0.95);border:1px solid #00d4ff;border-radius:6px;padding:8px 12px;color:#ccdde8;font-size:0.7rem;font-family:monospace;pointer-events:none;';
    document.body.appendChild(el);
  }
  const r = guessRegion(lat, lon);
  el.innerHTML = `<b>${r}</b><br>Lat ${lat.toFixed(1)}° Lon ${lon.toFixed(1)}°`;
  el.style.left = (cx + 15) + 'px';
  el.style.top = (cy - 15) + 'px';
  el.style.display = 'block';
  setTimeout(() => { el.style.display = 'none'; }, 2500);
}

function guessRegion(lat, lon) {
  if (lat > 5 && lat < 22 && lon > 110 && lon < 120) return 'South China Sea';
  if (lat > 35 && lat < 60 && lon > -60 && lon < -10) return 'North Atlantic';
  if (lat < -45) return 'Southern Ocean';
  if (lat > -10 && lat < 10 && lon > -120 && lon < -80) return 'East Pacific';
  if (lat > 0 && lat < 20 && lon > 60 && lon < 90) return 'North Indian';
  return 'Open Ocean';
}

function latLonToVec3(lat, lon, alt) {
  const phi = (90 - lat) * Math.PI / 180, theta = (lon + 180) * Math.PI / 180, r = 1 + alt;
  return new THREE.Vector3(-r * Math.sin(phi) * Math.cos(theta), r * Math.cos(phi), r * Math.sin(phi) * Math.sin(theta));
}

function animateGlobe() {
  if (!isGlobeReady) return;
  requestAnimationFrame(animateGlobe);
  earth.rotation.y += 0.0015;
  globeTime += 0.02;
  for (const m of markers) { m.scale.setScalar(1 + 0.3 * Math.sin(globeTime * 4 + m.userData.lat)); }
  if (Math.floor(globeTime * 60) % 60 === 0) updateOceanTexture(globeTime, currentLayer);
  renderer.render(scene, camera);
}

function setGlobeLayer(layer) {
  if (!LAYER_CFG[layer]) return;
  currentLayer = layer;
  updateOceanTexture(globeTime, layer);
}

function hasWebGL() {
  try { return !!document.createElement('canvas').getContext('webgl'); } catch (e) { return false; }
}

function resizeGlobe(containerId) {
  const container = document.getElementById(containerId);
  if (!container || !renderer) return;
  const W = container.clientWidth, H = container.clientHeight;
  renderer.setSize(W, H);
  camera.aspect = W / H;
  camera.updateProjectionMatrix();
}

window.Globe = { initGlobe, animateGlobe, setGlobeLayer, resizeGlobe, hasWebGL };
