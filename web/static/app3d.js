import * as THREE from 'three';

// === Globe Background ===
const bgC = document.getElementById('globe-bg'), bgX = bgC.getContext('2d');
let W, H, particles = [], globeRot = 0;
function resizeBg() { W = bgC.width = window.innerWidth; H = bgC.height = window.innerHeight; }
resizeBg(); window.addEventListener('resize', resizeBg);
for (let i = 0; i < 120; i++) particles.push({
  x: Math.random() * W, y: Math.random() * H, r: Math.random() * 1.2 + 0.3,
  vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25,
  alpha: Math.random() * 0.4 + 0.08,
});
function drawBg() {
  bgX.clearRect(0, 0, W, H);
  const cx = W * 0.72, cy = H * 0.42, r = Math.min(W, H) * 0.38;
  const g = bgX.createRadialGradient(cx - r * 0.3, cy - r * 0.3, r * 0.1, cx, cy, r);
  g.addColorStop(0, 'rgba(0,30,60,0.12)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  bgX.fillStyle = g; bgX.beginPath(); bgX.arc(cx, cy, r, 0, Math.PI * 2); bgX.fill();
  bgX.strokeStyle = 'rgba(0,200,220,0.06)'; bgX.lineWidth = 0.3;
  for (let lat = -60; lat <= 60; lat += 30) {
    const phi = (90 - lat) * Math.PI / 180, yr = r * Math.sin(phi), y = cy - r * Math.cos(phi);
    if (yr < 2) continue; bgX.beginPath(); bgX.ellipse(cx, y, yr, yr * 0.25, 0, 0, Math.PI * 2); bgX.stroke();
  }
  for (let lon = 0; lon < 360; lon += 30) {
    const theta = (lon + globeRot) * Math.PI / 180, ex = r * Math.abs(Math.cos(theta));
    bgX.beginPath(); bgX.ellipse(cx, cy, ex * 0.85, r, 0, 0, Math.PI * 2); bgX.stroke();
  }
  for (const p of particles) {
    p.x += p.vx; p.y += p.vy; if (p.x < 0) p.x = W; if (p.x > W) p.x = 0; if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
    const dx = p.x - cx, dy = p.y - cy, dist = Math.sqrt(dx * dx + dy * dy);
    if (dist < r * 1.15 && dist > r * 0.82) {
      bgX.fillStyle = `rgba(0,220,255,${p.alpha})`; bgX.beginPath(); bgX.arc(p.x, p.y, p.r, 0, Math.PI * 2); bgX.fill();
    }
  }
  globeRot += 0.04; requestAnimationFrame(drawBg);
}
drawBg();

// === 3D Globe with NASA Blue Marble textures + terrain ===
const OLAY = 1024, olayCanvas = document.createElement('canvas');
olayCanvas.width = OLAY; olayCanvas.height = OLAY / 2;
const olayCtx = olayCanvas.getContext('2d');
let scene, camera, renderer, earth, earthGroup, markers = [], dataOverlay, dataTexture, currentLayer = 'sst', globeTime = 0, isReady = false;

const LAYERS = { sst: { min: 22, max: 32 }, chl: { min: 0.1, max: 4 }, poc: { min: 0.2, max: 8 } };

function updateOverlay(time, layer) {
  const w = OLAY, h = OLAY / 2, img = olayCtx.createImageData(w, h), cfg = LAYERS[layer];
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4, nx = (x / w) * 8 - 4, ny = (y / h) * 4 - 2;
      const sst = 24 + 8 * Math.sin(nx * 1.3 + time * 0.3) * Math.cos(ny * 1.8 + time * 0.25)
                + 4 * Math.sin(nx * 2.7 - time * 0.5) * Math.cos(ny * 2.1 + time * 0.4);
      const chl = 0.3 + 2.2 * (0.5 + 0.5 * Math.sin(nx + time * 0.2 + 1) * Math.cos(ny * 1.7 - time * 0.3));
      const pocV = 0.5 + 5 * (0.5 + 0.5 * Math.sin(nx * 1.2 + time * 0.25 + 2) * Math.cos(ny * 1.9 - time * 0.35));
      const raw = layer === 'sst' ? sst : layer === 'chl' ? chl * 2 : pocV;
      const t = Math.max(0, Math.min(1, (raw - cfg.min) / (cfg.max - cfg.min + 0.01)));
      // Color ramp: blue (cold) → cyan → yellow → red (hot)
      let r, g, b;
      if (t < 0.25) { const s = t / 0.25; r = 10; g = 30 + s * 80; b = 160 - s * 60; }
      else if (t < 0.5) { const s = (t - 0.25) / 0.25; r = 10 + s * 60; g = 110 + s * 60; b = 100 - s * 60; }
      else if (t < 0.75) { const s = (t - 0.5) / 0.25; r = 70 + s * 180; g = 170 - s * 60; b = 40 - s * 30; }
      else { const s = (t - 0.75) / 0.25; r = 250; g = 110 - s * 60; b = 10; }
      img.data[i] = r; img.data[i + 1] = g; img.data[i + 2] = b;
      // Transparent over oceans (where land would be), semi-transparent everywhere
      img.data[i + 3] = 120;
    }
  }
  olayCtx.putImageData(img, 0, 0);
  if (dataTexture) dataTexture.needsUpdate = true;
}

function init3D() {
  const container = document.getElementById('map-container');
  if (!container) return;
  const w = container.clientWidth, h = container.clientHeight;
  scene = new THREE.Scene();

  camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 10);
  camera.position.set(0, 0.3, 3.2);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(w, h); renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  container.appendChild(renderer.domElement);

  // Lighting — key light + fill + rim for terrain depth
  scene.add(new THREE.AmbientLight(0x334466, 1.2));
  const sun = new THREE.DirectionalLight(0xffffff, 2.0);
  sun.position.set(5, 2, 3); scene.add(sun);
  const fill = new THREE.DirectionalLight(0x4488cc, 0.4);
  fill.position.set(-3, 0, -2); scene.add(fill);

  // Starfield
  const starsGeom = new THREE.BufferGeometry();
  const starsVerts = [];
  for (let i = 0; i < 300; i++) {
    const theta = Math.random() * Math.PI * 2, phi = Math.acos(2 * Math.random() - 1);
    starsVerts.push(Math.sin(phi) * Math.cos(theta) * 5, Math.sin(phi) * Math.sin(theta) * 5, Math.cos(phi) * 5);
  }
  starsGeom.setAttribute('position', new THREE.Float32BufferAttribute(starsVerts, 3));
  scene.add(new THREE.Points(starsGeom, new THREE.PointsMaterial({ color: 0x8899cc, size: 0.015 })));

  // Procedural earth texture — no CDN dependency
  const ETEX = 2048, eCanvas = document.createElement('canvas');
  eCanvas.width = ETEX; eCanvas.height = ETEX / 2;
  const eCtx = eCanvas.getContext('2d');

  // Ocean base gradient
  const grad = eCtx.createLinearGradient(0, 0, 0, ETEX / 2);
  grad.addColorStop(0, '#1a3a5c'); grad.addColorStop(0.5, '#1a5276'); grad.addColorStop(1, '#1a3a5c');
  eCtx.fillStyle = grad; eCtx.fillRect(0, 0, ETEX, ETEX / 2);

  // Simplified continent shapes (lat/lon → pixel mapping)
  function ly(lat) { return (90 - lat) / 180 * ETEX / 2; }
  function lx(lon) { return (lon + 180) / 360 * ETEX; }

  function drawContinent(points, color) {
    eCtx.fillStyle = color; eCtx.beginPath();
    for (let i = 0; i < points.length; i++) {
      const [lat, lon] = points[i];
      if (i === 0) eCtx.moveTo(lx(lon), ly(lat));
      else eCtx.lineTo(lx(lon), ly(lat));
    }
    eCtx.closePath(); eCtx.fill();
  }

  // Rough continent outlines
  const landColor = '#4a7c3f', desertColor = '#c4a862', tundraColor = '#8aac7a';
  // Africa
  drawContinent([[37,10],[-35,20],[-35,25],[-30,30],[-20,35],[5,37],[10,35],[30,32],[37,28],[37,10],[10,5],[-5,0],[-15,5],[-17,12]], '#7a9a3a');
  drawContinent([[-30,18],[-25,33],[-15,40],[5,40],[12,45],[12,52],[5,37],[0,35],[-10,30],[-15,28]], '#c4a862'); // Sahara
  drawContinent([[-5,38],[-5,42],[12,50],[12,38]], tundraColor); // Atlas
  // Eurasia
  drawContinent([[35,10],[42,15],[43,25],[47,28],[50,35],[55,55],[58,60],[65,60],[72,55],[70,35],[72,30],[68,25],[60,15],[55,5],[52,0],[48,-5],[40,-10],[35,-5],[30,5],[35,10]], '#6a8a3a');
  drawContinent([[45,5],[42,15],[45,30],[48,35],[55,50],[58,65],[70,65],[55,45],[52,35],[47,25],[45,15],[45,5]], '#55994a'); // Europe
  drawContinent([[25,50],[30,60],[40,68],[50,68],[55,55]], tundraColor); // Scandinavia
  drawContinent([[22,100],[25,108],[28,118],[30,122],[35,130],[40,135],[45,140],[50,140],[55,135],[50,128],[45,122],[40,118],[30,115],[28,110],[25,105],[22,100]], '#8a9a5a'); // Japan/Korea
  drawContinent([[-5,100],[0,105],[5,110],[8,115],[5,120],[0,118],[-2,112],[-5,105]], '#6a8a3a'); // Indonesia
  drawContinent([[5,95],[10,98],[15,100],[20,100],[25,98],[28,95],[25,92],[20,90],[10,88],[5,90]], '#6a8a3a'); // SE Asia
  drawContinent([[5,72],[10,75],[15,78],[20,77],[28,80],[35,80],[28,73],[22,70],[15,68],[10,68],[5,70]], '#8a7a3a'); // India
  // North America
  drawContinent([[25,-125],[25,-110],[30,-105],[35,-100],[40,-95],[50,-90],[60,-85],[65,-70],[70,-60],[70,-55],[60,-45],[50,-35],[45,-30],[30,-35],[25,-40],[20,-45],[15,-55],[10,-65],[5,-80],[8,-90],[10,-100],[15,-110],[20,-120],[25,-125]], '#5a8a3a');
  drawContinent([[55,-130],[60,-140],[65,-150],[65,-165],[60,-165],[50,-140],[55,-130]], tundraColor); // Alaska
  drawContinent([[40,-125],[42,-120],[45,-115],[48,-120],[45,-124],[42,-125]], '#b8a45a'); // Great Basin
  // South America
  drawContinent([[10,-85],[5,-80],[0,-78],[-5,-75],[-10,-70],[-15,-65],[-20,-60],[-25,-55],[-30,-50],[-35,-45],[-35,-40],[-30,-35],[-25,-35],[-15,-38],[-5,-42],[0,-50],[5,-60],[10,-75],[10,-85]], '#4a8a3a');
  drawContinent([[-15,-65],[-20,-60],[-25,-62],[-22,-68]], '#b8a45a'); // Andes high
  // Australia
  drawContinent([[-12,115],[-15,120],[-18,130],[-22,140],[-25,145],[-30,150],[-35,145],[-38,140],[-35,130],[-30,125],[-25,118],[-20,112],[-15,114]], '#c4954a');
  // Greenland
  drawContinent([[60,-55],[65,-52],[70,-45],[75,-40],[80,-30],[80,-20],[75,-15],[70,-20],[65,-30],[60,-42]], '#ddeedd');
  // Antarctica
  eCtx.fillStyle = '#eef4f0';
  eCtx.fillRect(0, ly(-65), ETEX, ETEX / 2 - ly(-65));

  // Terrain variation: add noise-like speckles
  const imgData = eCtx.getImageData(0, 0, ETEX, ETEX / 2);
  for (let y = 0; y < ETEX / 2; y += 3) {
    for (let x = 0; x < ETEX; x += 3) {
      const i = (y * ETEX + x) * 4;
      if (imgData.data[i + 1] > 80) { // land pixels (green channel high)
        const v = (Math.sin(x * 0.3 + y * 0.7) * Math.cos(y * 0.5) + 1) * 12;
        imgData.data[i] = Math.min(255, imgData.data[i] + v);
        imgData.data[i + 1] = Math.min(255, imgData.data[i + 1] + v * 0.7);
        imgData.data[i + 2] = Math.min(255, imgData.data[i + 2] + v * 0.3);
      }
    }
  }
  eCtx.putImageData(imgData, 0, 0);

  // Bump map canvas (grayscale height)
  const bCanvas = document.createElement('canvas');
  bCanvas.width = ETEX; bCanvas.height = ETEX / 2;
  const bCtx = bCanvas.getContext('2d');
  bCtx.drawImage(eCanvas, 0, 0);
  const bData = bCtx.getImageData(0, 0, ETEX, ETEX / 2);
  for (let i = 0; i < bData.data.length; i += 4) {
    const brightness = bData.data[i] * 0.3 + bData.data[i + 1] * 0.59 + bData.data[i + 2] * 0.11;
    // Oceans dark, land bright, mountains brighter
    const h = brightness > 100 ? Math.min(255, brightness + 40) : 10;
    bData.data[i] = bData.data[i + 1] = bData.data[i + 2] = h;
  }
  bCtx.putImageData(bData, 0, 0);

  const colorMap = new THREE.CanvasTexture(eCanvas);
  const bumpMap = new THREE.CanvasTexture(bCanvas);

  // Cloud layer — procedural
  const cCanvas = document.createElement('canvas');
  cCanvas.width = 1024; cCanvas.height = 512;
  const cCtx = cCanvas.getContext('2d');
  for (let y = 0; y < 512; y++) {
    for (let x = 0; x < 1024; x++) {
      const nx = x / 1024 * 12, ny = y / 512 * 6;
      const v = (Math.sin(nx * 3 + ny * 2) * Math.cos(nx * 5 - ny * 4) + 1) / 2;
      cCtx.fillStyle = `rgba(255,255,255,${v * 0.4})`;
      cCtx.fillRect(x, y, 1, 1);
    }
  }
  const cloudMap = new THREE.CanvasTexture(cCanvas);

  // Earth with procedural textures
  const geom = new THREE.SphereGeometry(1, 128, 96);
  const mat = new THREE.MeshPhongMaterial({
    map: colorMap,
    bumpMap: bumpMap,
    bumpScale: 0.03,
    specular: new THREE.Color(0x222222),
    shininess: 20,
  });
  earth = new THREE.Mesh(geom, mat);

  earthGroup = new THREE.Group();
  earthGroup.add(earth);
  scene.add(earthGroup);

  // Data overlay — semi-transparent sphere showing ocean metrics
  olayCtx.fillStyle = 'rgba(0,0,0,0)';
  olayCtx.fillRect(0, 0, OLAY, OLAY / 2);
  dataTexture = new THREE.CanvasTexture(olayCanvas);
  updateOverlay(0, 'sst');

  const overlayGeom = new THREE.SphereGeometry(1.005, 128, 96);
  const overlayMat = new THREE.MeshBasicMaterial({
    map: dataTexture,
    transparent: true,
    opacity: 0.45,
    blending: THREE.AdditiveBlending,
  });
  dataOverlay = new THREE.Mesh(overlayGeom, overlayMat);
  earthGroup.add(dataOverlay);

  // Clouds layer
  const cloudGeom = new THREE.SphereGeometry(1.015, 64, 48);
  const cloudMat = new THREE.MeshPhongMaterial({
    map: cloudMap,
    transparent: true,
    opacity: 0.25,
    blending: THREE.AdditiveBlending,
    side: THREE.FrontSide,
  });
  const clouds = new THREE.Mesh(cloudGeom, cloudMat);
  earthGroup.add(clouds);

  // Atmosphere glow
  const atmoGeom = new THREE.SphereGeometry(1.03, 64, 48);
  const atmoMat = new THREE.ShaderMaterial({
    vertexShader: `
      varying vec3 vNormal; varying vec3 vPosition;
      void main() { vNormal = normalize(normalMatrix * normal); vec4 p = modelViewMatrix * vec4(position, 1.0); vPosition = p.xyz; gl_Position = projectionMatrix * p; }
    `,
    fragmentShader: `
      varying vec3 vNormal; varying vec3 vPosition;
      void main() { float intensity = pow(0.7 - dot(vNormal, vec3(0, 0, 1.0)), 3.0); gl_FragColor = vec4(0.3, 0.6, 1.0, 1.0) * intensity; }
    `,
    blending: THREE.AdditiveBlending,
    side: THREE.FrontSide,
    transparent: true,
    depthWrite: false,
  });
  scene.add(new THREE.Mesh(atmoGeom, atmoMat));

  // ARGO float markers
  const mg = new THREE.SphereGeometry(0.01, 12, 12);
  const mm = new THREE.MeshBasicMaterial({ color: 0x00ffcc });
  const positions = [[15,115],[18,112],[10,118],[8,108],[20,117],[-35,-55],[40,-50],[-5,-85]];
  for (const [lat,lon] of positions) {
    const phi = (90-lat)*Math.PI/180, theta = (lon+180)*Math.PI/180, rd = 1.015;
    const mk = new THREE.Mesh(mg, mm);
    mk.position.set(-rd*Math.sin(phi)*Math.cos(theta), rd*Math.cos(phi), rd*Math.sin(phi)*Math.sin(theta));
    mk.userData = {lat,lon}; earthGroup.add(mk); markers.push(mk);
  }

  // Interaction state
  let dragging = false, px = 0, py = 0;
  let targetZoom = camera.position.z;
  let lastTouchDist = 0;

  // Mouse/touch drag → rotate
  function onPointerDown(e) {
    dragging = true; px = e.clientX; py = e.clientY;
    renderer.domElement.setPointerCapture(e.pointerId);
  }
  function onPointerMove(e) {
    if (!dragging) return;
    earthGroup.rotation.y += (e.clientX - px) * 0.005;
    earthGroup.rotation.x += (e.clientY - py) * 0.003;
    earthGroup.rotation.x = Math.max(-0.6, Math.min(0.6, earthGroup.rotation.x));
    px = e.clientX; py = e.clientY;
  }
  function onPointerUp(e) { dragging = false; }

  // Wheel → zoom (smooth lerp)
  function onWheel(e) {
    e.preventDefault();
    e.stopPropagation();
    targetZoom += e.deltaY * 0.005;
    targetZoom = Math.max(1.6, Math.min(6.0, targetZoom));
  }

  // Touch pinch → zoom
  function onTouchStart(e) {
    if (e.touches.length === 2) {
      lastTouchDist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      dragging = false;
    }
  }
  function onTouchMove(e) {
    if (e.touches.length === 2) {
      e.preventDefault();
      const dist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      const delta = lastTouchDist - dist;
      targetZoom += delta * 0.015;
      targetZoom = Math.max(1.6, Math.min(6.0, targetZoom));
      lastTouchDist = dist;
    }
  }

  renderer.domElement.style.touchAction = 'none';
  renderer.domElement.addEventListener('pointerdown', onPointerDown);
  window.addEventListener('pointermove', onPointerMove);
  window.addEventListener('pointerup', onPointerUp);
  renderer.domElement.addEventListener('wheel', onWheel, { passive: false });
  renderer.domElement.addEventListener('touchstart', onTouchStart, { passive: false });
  renderer.domElement.addEventListener('touchmove', onTouchMove, { passive: false });

  window.addEventListener('resize', () => {
    const cw = container.clientWidth, ch = container.clientHeight;
    renderer.setSize(cw, ch); camera.aspect = cw / ch; camera.updateProjectionMatrix();
  });
  isReady = true;
}

function animate3D() {
  if (!isReady) return;
  requestAnimationFrame(animate3D);
  earthGroup.rotation.y += 0.0018; globeTime += 0.02;
  // Smooth zoom lerp
  camera.position.z += (targetZoom - camera.position.z) * 0.15;
  for (const m of markers) m.scale.setScalar(1 + 0.35 * Math.sin(globeTime * 4 + m.userData.lat));
  if (Math.floor(globeTime * 60) % 60 === 0) updateOverlay(globeTime, currentLayer);
  renderer.render(scene, camera);
}

function setLayer(layer) { if (LAYERS[layer]) { currentLayer = layer; updateOverlay(globeTime, layer); } }

if ((() => { try { return !!document.createElement('canvas').getContext('webgl'); } catch (_) { return false; } })()) {
  init3D(); animate3D();
} else {
  document.getElementById('map-canvas').style.display = 'block';
}

// Layer buttons
document.querySelectorAll('.layer-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.layer-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active'); setLayer(btn.dataset.layer);
  });
});

// === WebSocket ===
let ws, activeRegion = 'scs';
function connectWS() {
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = e => {
    const d = JSON.parse(e.data); if (d.type !== 'metrics') return;
    document.getElementById('m-sst').textContent = d.sst.toFixed(1) + '°C';
    document.getElementById('m-chl').textContent = d.chl.toFixed(2) + ' mg/m³';
    document.getElementById('m-poc').textContent = d.poc_flux.toFixed(1) + ' gC/m²';
    document.getElementById('m-mld').textContent = d.mld.toFixed(0) + 'm';
    document.getElementById('viewport-title').childNodes[0].textContent = 'Digital Twin — ' + d.region_cn + ' ';
    addRelay(d.timestamp, d.region);
  };
  ws.onclose = () => setTimeout(connectWS, 2000);
}
connectWS();

document.querySelectorAll('.region-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.region-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active'); activeRegion = btn.dataset.region;
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'set_region', region: activeRegion }));
    fetchReport(activeRegion);
  });
});

async function fetchReport(region) {
  try {
    const res = await fetch(`/api/report/${region}?llm_provider=mock`);
    const data = await res.json(); if (!data.report) return;
    document.getElementById('report-sections').innerHTML = data.report.sections.map(s =>
      `<div class="report-card"><h4>${s.title} ${s.grade ? `<span class="grade grade-${s.grade}">${s.grade}</span>` : ''}</h4><p>${s.narrative}</p></div>`
    ).join('');
  } catch (e) { /* offline */ }
}
fetchReport('scs');

const relayLog = document.getElementById('relay-log');
function addRelay(ts, region) {
  const t = new Date().toISOString().substring(11, 19);
  const line = document.createElement('div'); line.className = 'line';
  line.textContent = `[${t}] ${region.toUpperCase()} — metrics updated`;
  relayLog.prepend(line); if (relayLog.children.length > 10) relayLog.lastChild.remove();
}
