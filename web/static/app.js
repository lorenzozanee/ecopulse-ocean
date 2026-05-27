// Globe Background
const bgC=document.getElementById('globe-bg'),bgX=bgC.getContext('2d');
let W,H,particles=[],globeRot=0;
function resize(){W=bgC.width=window.innerWidth;H=bgC.height=window.innerHeight}
resize();window.addEventListener('resize',resize);
for(let i=0;i<120;i++)particles.push({x:Math.random()*W,y:Math.random()*H,r:Math.random()*1.2+0.3,vx:(Math.random()-0.5)*0.25,vy:(Math.random()-0.5)*0.25,alpha:Math.random()*0.4+0.08});
function drawBg(){bgX.clearRect(0,0,W,H);const cx=W*0.72,cy=H*0.42,r=Math.min(W,H)*0.38;const g=bgX.createRadialGradient(cx-r*0.3,cy-r*0.3,r*0.1,cx,cy,r);g.addColorStop(0,'rgba(0,30,60,0.12)');g.addColorStop(1,'rgba(0,0,0,0)');bgX.fillStyle=g;bgX.beginPath();bgX.arc(cx,cy,r,0,Math.PI*2);bgX.fill();bgX.strokeStyle='rgba(0,200,220,0.06)';bgX.lineWidth=0.3;for(let lat=-60;lat<=60;lat+=30){const phi=(90-lat)*Math.PI/180,yr=r*Math.sin(phi),y=cy-r*Math.cos(phi);if(yr<2)continue;bgX.beginPath();bgX.ellipse(cx,y,yr,yr*0.25,0,0,Math.PI*2);bgX.stroke()}for(let lon=0;lon<360;lon+=30){const theta=(lon+globeRot)*Math.PI/180,ex=r*Math.abs(Math.cos(theta));bgX.beginPath();bgX.ellipse(cx,cy,ex*0.85,r,0,0,Math.PI*2);bgX.stroke()}for(const p of particles){p.x+=p.vx;p.y+=p.vy;if(p.x<0)p.x=W;if(p.x>W)p.x=0;if(p.y<0)p.y=H;if(p.y>H)p.y=0;const dx=p.x-cx,dy=p.y-cy,dist=Math.sqrt(dx*dx+dy*dy);if(dist<r*1.15&&dist>r*0.82){bgX.fillStyle=`rgba(0,220,255,${p.alpha})`;bgX.beginPath();bgX.arc(p.x,p.y,p.r,0,Math.PI*2);bgX.fill()}}globeRot+=0.04;requestAnimationFrame(drawBg)}drawBg();

// Map Canvas
const mapC=document.getElementById('map-canvas'),mapX=mapC.getContext('2d');
let simTime=0;
function resizeMap(){mapC.width=mapC.parentElement.clientWidth;mapC.height=mapC.parentElement.clientHeight}
resizeMap();window.addEventListener('resize',resizeMap);
function drawMap(){const w=mapC.width,h=mapC.height;const img=mapX.createImageData(w,h);for(let y=0;y<h;y++){for(let x=0;x<w;x++){const i=(y*w+x)*4,nx=x/w*4,ny=y/h*2;const sst=24+8*Math.sin(nx*2.7+simTime*0.3)*Math.cos(ny*1.8+simTime*0.25)+4*Math.sin(nx*5.3-simTime*0.5)*Math.cos(ny*4.1+simTime*0.4);const chl=0.2+2.5*(0.5+0.5*Math.sin(nx*1.9+simTime*0.2+1.3)*Math.cos(ny*3.3-simTime*0.3));const t=(sst-24)/8;img.data[i]=Math.max(0,Math.min(255,(t>0.2?t*50:0)+chl*35));img.data[i+1]=Math.max(0,Math.min(255,15+chl*38+Math.abs(t)*18));img.data[i+2]=Math.max(0,Math.min(255,60+(1-Math.abs(t))*45+(1-chl/2.5)*55));img.data[i+3]=210}}mapX.putImageData(img,0,0);const hx=w*0.58,hy=h*0.38,hr=35+10*Math.sin(simTime*0.7);const glow=mapX.createRadialGradient(hx,hy,0,hx,hy,hr*2.5);glow.addColorStop(0,'rgba(255,140,0,0.18)');glow.addColorStop(1,'rgba(0,0,0,0)');mapX.fillStyle=glow;mapX.beginPath();mapX.arc(hx,hy,hr*2.5,0,Math.PI*2);mapX.fill();mapX.fillStyle='#ffaa00';mapX.font='9px monospace';mapX.fillText('Carbon Sink',hx-23,hy-38);simTime+=0.018;requestAnimationFrame(drawMap)}drawMap();

// WebSocket
let ws;let activeRegion='scs';
function connectWS(){ws=new WebSocket(`ws://${location.host}/ws`);ws.onmessage=e=>{const d=JSON.parse(e.data);if(d.type!=='metrics')return;document.getElementById('m-sst').textContent=d.sst.toFixed(1)+'°C';document.getElementById('m-chl').textContent=d.chl.toFixed(2)+' mg/m³';document.getElementById('m-poc').textContent=d.poc_flux.toFixed(1)+' gC/m²';document.getElementById('m-mld').textContent=d.mld.toFixed(0)+'m';document.getElementById('viewport-title').textContent='Digital Twin — '+d.region_cn;addRelay(d.timestamp,d.region)};ws.onclose=()=>setTimeout(connectWS,2000)}connectWS();

// Regions
document.querySelectorAll('.region-btn').forEach(btn=>{btn.addEventListener('click',()=>{document.querySelectorAll('.region-btn').forEach(b=>b.classList.remove('active'));btn.classList.add('active');activeRegion=btn.dataset.region;if(ws&&ws.readyState===WebSocket.OPEN)ws.send(JSON.stringify({type:'set_region',region:activeRegion}));fetchReport(activeRegion)})});

async function fetchReport(region){try{const res=await fetch(`/api/report/${region}?llm_provider=mock`);const data=await res.json();const container=document.getElementById('report-sections');if(!data.report)return;container.innerHTML=data.report.sections.map(s=>`<div class="report-card"><h4>${s.title} ${s.grade?`<span class="grade grade-${s.grade}">${s.grade}</span>`:''}</h4><p>${s.narrative}</p></div>`).join('')}catch(e){console.error(e)}}fetchReport('scs');

// Relay
const relayLog=document.getElementById('relay-log');
function addRelay(ts,region){const d=new Date(),t=d.toISOString().substring(11,19);const line=document.createElement('div');line.className='line';line.textContent=`[${t}] ${region.toUpperCase()} — metrics updated`;relayLog.prepend(line);if(relayLog.children.length>10)relayLog.lastChild.remove()}
