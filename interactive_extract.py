# interactive_extract_enhanced.py
# Single-file Flask app (backend + frontend).
# - Uses OpenAI on the server to extract topics and subtopics as JSON.
# - Frontend maps subtopics to interactive visual modules (kmeans, perceptron, gradient, confusion, matrix).
# - Keep OPENAI_API_KEY in environment variables.

from flask import Flask, request, jsonify, render_template_string
import os, json, textwrap
import openai

app = Flask(__name__, static_folder=None)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not set in environment. Set OPENAI_API_KEY before running.")
openai.api_key = OPENAI_API_KEY

HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Interactive Extractor — Enhanced</title>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <style>
    :root{ --bg:#0f172a; --card:#0b1220; --accent:#7c3aed; --muted:#94a3b8; --glass: rgba(255,255,255,0.03); }
    body{ margin:0; font-family:Inter,system-ui,Segoe UI,Arial; background:linear-gradient(180deg,#071025 0%, #08142a 60%); color:#e6eef8; min-height:100vh; padding:24px; }
    .app{ max-width:1200px; margin:0 auto; display:grid; grid-template-columns:360px 1fr; gap:20px; }
    .panel{ background: linear-gradient(180deg, rgba(255,255,255,0.02), transparent); border-radius:14px; padding:14px; box-shadow: 0 6px 30px rgba(2,6,23,0.6); border:1px solid rgba(255,255,255,0.03);}
    textarea{ width:100%; min-height:220px; background:transparent; border:1px dashed rgba(255,255,255,0.06); color:inherit; padding:10px; border-radius:8px; resize:vertical }
    button{ background:var(--accent); border:none; padding:8px 12px; color:white; border-radius:8px; cursor:pointer; box-shadow:0 6px 18px rgba(124,58,237,0.18) }
    .secondary{ background:transparent; border:1px solid rgba(255,255,255,0.06); padding:8px 10px; color:var(--muted); }
    .topic{ padding:10px; border-radius:10px; margin-bottom:8px; background:linear-gradient(180deg, rgba(255,255,255,0.02), transparent); cursor:pointer; border:1px solid rgba(255,255,255,0.02); }
    .topic h4{ margin:0; font-size:14px }
    .sub{ margin-top:8px; padding:8px; border-radius:8px; cursor:pointer; background:rgba(255,255,255,0.02); font-size:13px }
    .selected{ outline: 2px solid rgba(124,58,237,0.25); box-shadow: inset 0 0 18px rgba(124,58,237,0.04); }
    .mini{ font-size:12px; color:var(--muted) }
    .flex{ display:flex; gap:10px; align-items:center; }
    .wrap{ display:flex; gap:10px; }
    canvas{ border-radius:10px; background:linear-gradient(180deg, rgba(255,255,255,0.01), transparent); }
    .controls{ margin-top:10px; display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
    .card{ padding:10px; border-radius:10px; background:linear-gradient(180deg, rgba(255,255,255,0.015), transparent); border:1px solid rgba(255,255,255,0.02) }
    .titlebar{ display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:10px; }
    .hint{ font-size:12px; color:var(--muted) }
  </style>
</head>
<body>
  <div class="app">
    <div class="panel">
      <div class="titlebar">
        <h3 style="margin:0">Paste summary / corpus</h3>
        <div class="mini hint">Server-side OpenAI → dynamic interactive modules</div>
      </div>

      <textarea id="corpus">Paste your topic summary here — try "KMeans clustering", "perceptron", "gradient descent", "confusion matrix", "matrix multiply" or a deep learning summary.</textarea>
      <div style="margin-top:8px;" class="wrap">
        <button id="extractBtn">Extract & Generate Modules</button>
        <button class="secondary" id="demoBtn">Load Demo</button>
        <button class="secondary" id="clearBtn">Clear</button>
      </div>
      <div id="status" class="mini" style="margin-top:10px;color:#dbeafe"></div>

      <h4 style="margin-top:14px">Topics</h4>
      <div id="topicsList"></div>
    </div>

    <div class="panel">
      <div class="titlebar">
        <div>
          <h2 id="detailTitle" style="margin:0">Select a subtopic</h2>
          <div id="detailHint" class="mini hint">Interactive component will appear here</div>
        </div>
        <div class="mini">Interactive-preview</div>
      </div>

      <div id="detailContent" class="card" style="min-height:380px; display:flex; flex-direction:column; gap:10px;">
        <div id="summaryArea" style="color:var(--muted)">Choose a topic & subtopic from the left. I will show a dynamic, interactive visualizer if available.</div>

        <!-- Container for dynamic interactive modules -->
        <div id="moduleArea" style="flex:1; display:flex; gap:12px; flex-direction:column;"></div>

        <div style="display:flex; gap:10px; justify-content:flex-end;">
          <button id="exportState">Export State</button>
        </div>
      </div>
    </div>
  </div>

<script>
/* ---------- Data & Controls ---------- */
let topicsJson = null;
const status = document.getElementById('status');
const topicsList = document.getElementById('topicsList');
const detailTitle = document.getElementById('detailTitle');
const detailHint = document.getElementById('detailHint');
const summaryArea = document.getElementById('summaryArea');
const moduleArea = document.getElementById('moduleArea');

document.getElementById('extractBtn').onclick = async () => {
  const text = document.getElementById('corpus').value;
  if(!text.trim()){ status.textContent = 'Please paste some text.'; return; }
  status.textContent = 'Calling OpenAI...';
  try {
    const resp = await fetch('/api/extract', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text})});
    const js = await resp.json();
    if(js.error){ status.textContent = 'Error from server: ' + js.error; return; }
    topicsJson = js;
    renderTopics(js);
    status.textContent = 'Topics ready — click a subtopic.';
  } catch(e) {
    status.textContent = 'Network error: ' + e;
  }
};

document.getElementById('demoBtn').onclick = () => {
  topicsJson = {
    topics:[
      {id:'dl', title:'Deep Learning', subtopics:[
        {id:'ann', title:'ANN (perceptron, forward, backprop)', bullets:['Perceptron','Forward Propagation','Backpropagation']},
      ]},
      {id:'kmeans', title:'KMeans Clustering', subtopics:[
        {id:'kmeans-intro', title:'KMeans (interactive)', bullets:['Choose K','Initialize centroids','Assign points','Update centroids'], interactive:'kmeans'}
      ]},
      {id:'gd', title:'Optimization', subtopics:[
        {id:'grad-1d', title:'Gradient Descent (1D)', bullets:['Loss function','Learning rate','Update steps'], interactive:'gradient'}
      ]},
      {id:'perc', title:'Perceptron', subtopics:[
        {id:'perceptron-demo', title:'Perceptron (interactive)', bullets:['Weights','Bias','Activation'], interactive:'perceptron'}
      ]},
      {id:'cm', title:'Evaluation', subtopics:[
        {id:'conf-matrix', title:'Confusion Matrix (interactive threshold)', bullets:['TP/FP/FN/TN','Precision/Recall'], interactive:'confusion'}
      ]},
      {id:'mat', title:'Matrix', subtopics:[
        {id:'matmul', title:'Matrix Multiply Visual', bullets:['A x B = C'], interactive:'matrix'}
      ]}
    ]
  };
  renderTopics(topicsJson);
  status.textContent = 'Demo loaded.';
};

document.getElementById('clearBtn').onclick = () => { document.getElementById('corpus').value=''; status.textContent=''; topicsList.innerHTML=''; topicsJson=null; moduleArea.innerHTML=''; detailTitle.textContent='Select a subtopic'; summaryArea.textContent='Choose a topic/subtopic to see an interactive demo.' };

/* ---------- Render topic tree ---------- */
function renderTopics(js){
  topicsList.innerHTML = '';
  js.topics.forEach(t => {
    const tdiv = document.createElement('div'); tdiv.className='topic';
    const h = document.createElement('h4'); h.textContent = t.title; tdiv.appendChild(h);
    const subwrap = document.createElement('div');
    t.subtopics.forEach(s => {
      const sdiv = document.createElement('div'); sdiv.className='sub'; sdiv.textContent = s.title;
      sdiv.onclick = () => selectSubtopic(t, s, sdiv);
      subwrap.appendChild(sdiv);
    });
    tdiv.appendChild(subwrap);
    topicsList.appendChild(tdiv);
  });
}

/* ---------- Selection & module mapping ---------- */
function selectSubtopic(topic, sub, node){
  // highlight selection
  document.querySelectorAll('.sub').forEach(el=>el.classList.remove('selected'));
  node.classList.add('selected');

  detailTitle.textContent = topic.title + ' → ' + sub.title;
  summaryArea.innerHTML = '';
  if(sub.bullets){ 
    const ul = document.createElement('ul');
    sub.bullets.forEach(b => { const li = document.createElement('li'); li.textContent=b; ul.appendChild(li); });
    summaryArea.appendChild(ul);
  }
  // decide which interactive module to show
  const keyword = (sub.interactive || (sub.id + ' ' + sub.title)).toLowerCase();
  moduleArea.innerHTML = '';

  if(keyword.includes('kmeans') || /k[- ]?means/.test(keyword)) {
    showKMeansModule(sub);
  } else if(keyword.includes('perceptron') || keyword.includes('neuron') || keyword.includes('activation')) {
    showPerceptronModule(sub);
  } else if(keyword.includes('gradient') || keyword.includes('descent') || keyword.includes('optimi')) {
    showGradientModule(sub);
  } else if(keyword.includes('confus') || keyword.includes('precision') || keyword.includes('recall') || keyword.includes('threshold')) {
    showConfusionModule(sub);
  } else if(keyword.includes('matrix') || keyword.includes('matmul') || keyword.includes('multiply')) {
    showMatrixModule(sub);
  } else {
    // fallback: show a small editable explainer and ask user to tag interactive keywords
    const fallback = document.createElement('div'); fallback.innerHTML = `<div class="mini hint">No specific interactive module found. You can add keywords like "kmeans", "perceptron", "gradient", "confusion", or "matrix" in the subtopic title or return JSON with "interactive": "kmeans".</div>`;
    moduleArea.appendChild(fallback);
  }
}

/* ---------- KMeans Module ---------- */
function showKMeansModule(sub){
  const container = document.createElement('div'); container.style.display='flex'; container.style.gap='12px';
  const left = document.createElement('div'); left.style.flex='1';
  const canvasWrap = document.createElement('div'); canvasWrap.style.position='relative';
  const canvas = document.createElement('canvas'); canvas.width=760; canvas.height=420; canvas.style.maxWidth='100%'; canvas.style.borderRadius='10px';
  canvasWrap.appendChild(canvas);
  left.appendChild(canvasWrap);
  const right = document.createElement('div'); right.style.width='320px';
  right.innerHTML = `
    <div><b>K-Means Interactive</b></div>
    <div class="hint mini">Drag points, change K, see centroids, lines & WCSS</div>
    <div class="controls card" style="margin-top:10px;">
      <label>K <input id="k_slider" type="range" min="1" max="6" value="2" /></label>
      <span id="k_val">2</span>
      <button id="add_pt" class="secondary">+Point</button>
      <button id="rm_pt" class="secondary">-Point</button>
      <div style="margin-top:8px">WCSS: <b id="wcss_val">0</b></div>
    </div>
    <div style="margin-top:8px"><canvas id="elbow_canvas" width="320" height="120" style="width:100%; border-radius:8px;"></canvas></div>
  `;
  container.appendChild(left); container.appendChild(right);
  moduleArea.appendChild(container);

  // state
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  let pts = [];
  function randPts(n=8){
    pts = [];
    for(let i=0;i<n;i++) pts.push({x: Math.random()*(w-120)+60, y: Math.random()*(h-120)+60, id: i});
  }
  randPts(8);

  let dragging = null;
  canvas.onmousedown = (e)=>{ const r=canvas.getBoundingClientRect(); const mx=e.clientX-r.left, my=e.clientY-r.top; for(const p of pts){ if(Math.hypot(p.x-mx,p.y-my) < 10){ dragging=p; break; } } }
  window.onmousemove = (e)=>{ if(!dragging) return; const r=canvas.getBoundingClientRect(); dragging.x = Math.max(20, Math.min(w-20, e.clientX-r.left)); dragging.y = Math.max(20, Math.min(h-20, e.clientY-r.top)); draw(); }
  window.onmouseup = ()=> dragging=null;

  // controls
  const k_slider = document.getElementById('k_slider'), k_val = document.getElementById('k_val'), wcss_val = document.getElementById('wcss_val');
  k_slider.oninput = ()=>{ k_val.textContent = k_slider.value; draw(); };
  document.getElementById('add_pt').onclick = ()=>{ pts.push({x:Math.random()*(w-120)+60,y:Math.random()*(h-120)+60,id:Date.now()}); k_slider.max = Math.max(1, Math.min(12, pts.length)); draw(); }
  document.getElementById('rm_pt').onclick = ()=>{ if(pts.length) pts.pop(); k_slider.max = Math.max(1, Math.min(12, pts.length)); draw(); }

  function dist(a,b){ const dx=a.x-b.x, dy=a.y-b.y; return Math.hypot(dx,dy); }
  function kmeans(points, K, iters=20){
    if(points.length===0) return {centroids:[], labels:[], wcss:0};
    let centroids = points.slice(0, K).map(p => ({x:p.x+0.01*Math.random(), y:p.y+0.01*Math.random()}));
    let labels = new Array(points.length).fill(0);
    for(let it=0; it<iters; it++){
      let changed=false;
      for(let i=0;i<points.length;i++){
        let best=0, bestd=dist(points[i], centroids[0]);
        for(let c=1;c<centroids.length;c++){ const d=dist(points[i],centroids[c]); if(d<bestd){best=d; bestd=d} }
        if(labels[i] !== best){ labels[i] = best; changed=true; }
      }
      const sums = centroids.map(()=>({x:0,y:0,c:0}));
      for(let i=0;i<points.length;i++){ const l=labels[i]; sums[l].x += points[i].x; sums[l].y += points[i].y; sums[l].c += 1; }
      for(let c=0;c<centroids.length;c++) if(sums[c].c>0){ centroids[c].x = sums[c].x / sums[c].c; centroids[c].y = sums[c].y / sums[c].c; }
      if(!changed) break;
    }
    let wcss = 0;
    for(let i=0;i<points.length;i++){ const c = centroids[labels[i]]; const d = dist(points[i], c); wcss += d*d; }
    return {centroids, labels, wcss};
  }

  function draw(){
    ctx.clearRect(0,0,w,h);
    // grid
    ctx.strokeStyle = 'rgba(255,255,255,0.03)'; ctx.lineWidth=1;
    for(let gx=20; gx<w; gx+=40){ ctx.beginPath(); ctx.moveTo(gx,0); ctx.lineTo(gx,h); ctx.stroke(); }
    for(let gy=20; gy<h; gy+=40){ ctx.beginPath(); ctx.moveTo(0,gy); ctx.lineTo(w,gy); ctx.stroke(); }

    const K = Math.max(1, Math.min(12, Number(k_slider.value)));
    const res = kmeans(pts, K, 10);
    // lines from centroids to points
    ctx.lineWidth = 1;
    for(let i=0;i<pts.length;i++){
      const c = res.centroids[res.labels[i]];
      ctx.beginPath(); ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(c.x, c.y);
      ctx.strokeStyle = 'rgba(200,200,220,0.12)'; ctx.stroke();
    }
    // centroids
    res.centroids.forEach((c, idx) => {
      ctx.beginPath(); ctx.arc(c.x, c.y, 10, 0, Math.PI*2); ctx.fillStyle = colorFor(idx); ctx.fill();
      ctx.strokeStyle='rgba(0,0,0,0.3)'; ctx.stroke();
    });
    // points
    pts.forEach((p, i) => {
      ctx.beginPath(); ctx.arc(p.x, p.y, 7, 0, Math.PI*2); ctx.fillStyle = '#fff'; ctx.fill();
      ctx.beginPath(); ctx.arc(p.x, p.y, 6, 0, Math.PI*2); ctx.fillStyle = colorFor(res.labels[i]); ctx.fill();
      ctx.strokeStyle='rgba(0,0,0,0.25)'; ctx.stroke();
    });
    wcss_val.textContent = res.wcss.toFixed(3);
    drawElbowSmall(pts);
  }

  function colorFor(i){ return ['#ef4444','#f59e0b','#10b981','#3b82f6','#8b5cf6','#ec4899'][i%6]; }

  function drawElbowSmall(points){
    const c = document.getElementById('elbow_canvas'); const cc = c.getContext('2d');
    cc.clearRect(0,0,c.width,c.height);
    const Kmax = Math.min(8, Math.max(3, points.length));
    const data = [];
    for(let kk=1; kk<=Kmax; kk++){
      const res = kmeans(points, kk, 6); data.push({k:kk,wcss:res.wcss});
    }
    const maxW = Math.max(...data.map(d=>d.wcss));
    cc.lineWidth = 2; cc.strokeStyle = '#ffffff';
    cc.beginPath();
    for(let i=0;i<data.length;i++){
      const x = 10 + i*( (c.width-20)/(data.length-1) );
      const y = 10 + (1 - (data[i].wcss / maxW))*(c.height-20);
      if(i===0) cc.moveTo(x,y); else cc.lineTo(x,y);
    } cc.stroke();
    // dots
    for(let i=0;i<data.length;i++){
      const x = 10 + i*( (c.width-20)/(data.length-1) );
      const y = 10 + (1 - (data[i].wcss / maxW))*(c.height-20);
      cc.beginPath(); cc.arc(x,y,3,0,Math.PI*2); cc.fillStyle='#7c3aed'; cc.fill();
    }
  }

  draw();
}

/* ---------- Perceptron Module ---------- */
function showPerceptronModule(sub){
  const container = document.createElement('div'); container.style.display='flex'; container.style.gap='12px';
  const left = document.createElement('div'); left.style.flex='1';
  const canvas = document.createElement('canvas'); canvas.width=760; canvas.height=420; left.appendChild(canvas);
  const right = document.createElement('div'); right.style.width='320px';
  right.innerHTML = `
    <div><b>Perceptron / Single Neuron</b></div>
    <div class="mini hint">Adjust weights & bias; see decision boundary and prediction.</div>
    <div class="controls card" style="margin-top:8px;">
      <div>W1: <input id="w1" type="range" min="-5" max="5" step="0.1" value="1"/></div>
      <div>W2: <input id="w2" type="range" min="-5" max="5" step="0.1" value="1"/></div>
      <div>Bias: <input id="b" type="range" min="-10" max="10" step="0.1" value="0"/></div>
      <div style="margin-top:6px">Activation:
        <select id="act"><option value="step">Step</option><option value="sigmoid">Sigmoid</option></select>
      </div>
      <div style="margin-top:8px">Sample input: <button id="sample">Random</button></div>
      <div style="margin-top:8px">Output: <b id="outp">0</b></div>
    </div>
  `;
  container.appendChild(left); container.appendChild(right);
  moduleArea.appendChild(container);

  const ctx = canvas.getContext('2d'); const w=canvas.width, h=canvas.height;
  let samples = [];
  function genSamples(n=60){
    samples=[];
    for(let i=0;i<n;i++){
      const x = Math.random()* (w-80) + 40; const y = Math.random()*(h-80)+40;
      // label by a hidden linear line
      const vx = (x - w/2)/40, vy = (y - h/2)/40;
      const label = (vx + vy + 0.2*Math.random() > 0) ? 1 : 0;
      samples.push({x,y,label});
    }
  }
  genSamples(80);

  const w1El = document.getElementById('w1'), w2El = document.getElementById('w2'), bEl = document.getElementById('b'), actEl = document.getElementById('act'), outp = document.getElementById('outp');
  document.getElementById('sample').onclick = ()=>{ genSamples(80); draw(); }

  function activation(z, mode){
    if(mode==='step') return z>=0 ? 1 : 0;
    return 1/(1+Math.exp(-z));
  }

  function draw(){
    ctx.clearRect(0,0,w,h);
    // draw samples
    const w1 = parseFloat(w1El.value), w2=parseFloat(w2El.value), b=parseFloat(bEl.value), act=actEl.value;
    samples.forEach(s=>{
      const nx = (s.x - w/2)/40, ny=(s.y - h/2)/40;
      const z = w1*nx + w2*ny + b;
      const yhat = activation(z, act);
      ctx.beginPath();
      ctx.arc(s.x,s.y,6,0,Math.PI*2);
      ctx.fillStyle = yhat>0.5 ? 'rgba(16,185,129,0.9)' : 'rgba(239,68,68,0.9)';
      ctx.fill();
      ctx.strokeStyle='rgba(255,255,255,0.06)'; ctx.stroke();
    });
    // decision boundary: solve w1*x + w2*y + b = 0 -> y = (-w1*x - b)/w2
    ctx.beginPath(); ctx.lineWidth=2; ctx.strokeStyle='rgba(255,255,255,0.7)';
    if(Math.abs(w2)>0.001){
      const x1 = 0, y1 = (-w1*( (x1 - w/2)/40 ) - b)/w2; // uses normalized too; better draw approximate line in pixel space
      // compute two points in pixel coordinates:
      const px1 = 0; const py1 = h/2 + (- (w1*( (px1 - w/2)/40 ) ) - b)/w2*40;
      const px2 = w; const py2 = h/2 + (- (w1*( (px2 - w/2)/40 ) ) - b)/w2*40;
      ctx.moveTo(px1, py1); ctx.lineTo(px2, py2); ctx.stroke();
    }
    outp.textContent = '—';
  }
  // update listeners
  [w1El,w2El,bEl,actEl].forEach(el => el.oninput = draw);
  draw();
}

/* ---------- Gradient Descent Module (1D) ---------- */
function showGradientModule(sub){
  const container = document.createElement('div'); container.className='card';
  container.innerHTML = `
    <div style="display:flex; gap:12px; align-items:center; justify-content:space-between;">
      <div><b>Gradient Descent (1D)</b><div class="mini hint">Minimize f(x) = (x-3)^2 + 2</div></div>
      <div class="mini">Step-by-step</div>
    </div>
    <canvas id="gd_canvas" width="900" height="260" style="margin-top:10px; width:100%; border-radius:8px;"></canvas>
    <div class="controls" style="margin-top:8px;">
      <label>Learning rate: <input id="lr" type="range" min="0.01" max="1" step="0.01" value="0.1"/></label>
      <span id="lr_val">0.1</span>
      <button id="gd_step">Step</button>
      <button id="gd_run">Run</button>
      <button id="gd_reset">Reset</button>
    </div>
    <div style="margin-top:8px">x: <b id="x_val">0</b> &nbsp; loss: <b id="loss_val">0</b></div>
  `;
  moduleArea.appendChild(container);

  const canvas = document.getElementById('gd_canvas'); const ctx = canvas.getContext('2d'); const W=canvas.width, H=canvas.height;
  const lrEl = document.getElementById('lr'), lrVal = document.getElementById('lr_val'), xVal = document.getElementById('x_val'), lossVal = document.getElementById('loss_val');
  let x = -6; const f = x => (x-3)*(x-3)+2;
  function df(x){ return 2*(x-3); }
  lrEl.oninput = ()=>{ lrVal.textContent = lrEl.value; }
  function draw(){
    ctx.clearRect(0,0,W,H);
    // draw curve
    ctx.beginPath(); for(let i=0;i<W;i++){
      const xs = -8 + (i/W)*16;
      const ys = f(xs);
      const sy = H - ( (ys - 0)/(18) )*H; // heuristic mapping
      if(i===0) ctx.moveTo(i, sy); else ctx.lineTo(i, sy);
    } ctx.strokeStyle='rgba(255,255,255,0.7)'; ctx.lineWidth=2; ctx.stroke();
    // draw current x
    const px = ((x + 8)/16)*W;
    const py = H - ( (f(x) - 0)/(18) )*H;
    ctx.beginPath(); ctx.arc(px, py, 8,0,Math.PI*2); ctx.fillStyle='#7c3aed'; ctx.fill();
    xVal.textContent = x.toFixed(3);
    lossVal.textContent = f(x).toFixed(3);
  }
  document.getElementById('gd_step').onclick = ()=>{ const lr = parseFloat(lrEl.value); x = x - lr * df(x); draw(); }
  let anim = null;
  document.getElementById('gd_run').onclick = ()=>{ if(anim){ clearInterval(anim); anim=null; document.getElementById('gd_run').textContent='Run'; return; } anim = setInterval(()=>{ const lr = parseFloat(lrEl.value); x = x - lr * df(x); draw(); }, 120); document.getElementById('gd_run').textContent='Stop'; }
  document.getElementById('gd_reset').onclick = ()=>{ x = -6; draw(); }
  draw();
}

/* ---------- Confusion Matrix Module ---------- */
function showConfusionModule(sub){
  const container = document.createElement('div');
  container.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <div><b>Confusion Matrix & Threshold</b><div class="mini hint">Adjust threshold; see TP/FP/TN/FN and metrics</div></div>
      <div class="mini">Interactive</div>
    </div>
    <div style="display:flex; gap:12px; margin-top:10px;">
      <canvas id="cf_canvas" width="540" height="320" style="border-radius:8px;"></canvas>
      <div style="width:260px;">
        <div class="card">
          <div>Threshold: <input id="th" type="range" min="0" max="1" step="0.01" value="0.5"/></div>
          <div style="margin-top:8px">TP: <b id="tp">0</b></div>
          <div>FP: <b id="fp">0</b></div>
          <div>TN: <b id="tn">0</b></div>
          <div>FN: <b id="fn">0</b></div>
          <div style="margin-top:8px">Precision: <b id="prec">0</b></div>
          <div>Recall: <b id="rec">0</b></div>
        </div>
      </div>
    </div>
  `;
  moduleArea.appendChild(container);

  const canvas = document.getElementById('cf_canvas'); const ctx = canvas.getContext('2d');
  let scores = [];
  function genScores(n=100){
    scores = [];
    for(let i=0;i<n;i++){
      // positive scores tend to be higher
      const label = Math.random() < 0.4 ? 1 : 0;
      const score = label ? Math.random()*0.4 + 0.5 : Math.random()*0.6;
      scores.push({label, score});
    }
    draw();
  }
  genScores(120);
  document.getElementById('th').oninput = draw;

  function draw(){
    ctx.clearRect(0,0,canvas.width, canvas.height);
    const th = parseFloat(document.getElementById('th').value);
    // draw scores as scatter plot
    scores.forEach((s, i) => {
      const x = (i / scores.length) * (canvas.width-40) + 20;
      const y = canvas.height/2 + (s.score - th)*120;
      ctx.beginPath(); ctx.arc(x,y,4,0,Math.PI*2);
      ctx.fillStyle = s.label ? '#06b6d4' : '#fb7185';
      ctx.fill();
    });
    // compute confusion
    let TP=0, FP=0, TN=0, FN=0;
    scores.forEach(s => {
      const pred = s.score >= th ? 1 : 0;
      if(pred===1 && s.label===1) TP++;
      if(pred===1 && s.label===0) FP++;
      if(pred===0 && s.label===0) TN++;
      if(pred===0 && s.label===1) FN++;
    });
    document.getElementById('tp').textContent = TP; document.getElementById('fp').textContent = FP; document.getElementById('tn').textContent = TN; document.getElementById('fn').textContent = FN;
    const prec = TP + FP === 0 ? 0 : TP / (TP + FP);
    const rec = TP + FN === 0 ? 0 : TP / (TP + FN);
    document.getElementById('prec').textContent = prec.toFixed(3); document.getElementById('rec').textContent = rec.toFixed(3);

    // draw threshold line
    ctx.fillStyle = 'rgba(255,255,255,0.06)'; ctx.fillRect(10, canvas.height/2 - 2, canvas.width-20, 4);
    ctx.fillStyle = '#fff'; ctx.fillRect(10, canvas.height-24, canvas.width-20, 12);
    ctx.fillStyle = '#000'; ctx.fillText('Score (higher => predicted positive). Threshold = ' + th.toFixed(2), 14, canvas.height-14);
  }
}

/* ---------- Matrix Multiply Module ---------- */
function showMatrixModule(sub){
  const container = document.createElement('div'); container.className='card';
  container.innerHTML = `
    <div style="display:flex; justify-content:space-between;">
      <div><b>Matrix Multiply Visualizer</b><div class="mini hint">Edit elements of A (2x3) and B (3x2), result updates live</div></div>
      <div class="mini">A x B = C</div>
    </div>
    <div style="display:flex; gap:16px; margin-top:10px;">
      <div id="A" style="display:grid; grid-template-columns:repeat(3,60px); gap:6px;"></div>
      <div id="B" style="display:grid; grid-template-columns:repeat(2,60px); gap:6px;"></div>
      <div id="C" style="display:grid; grid-template-columns:repeat(2,80px); gap:6px;"></div>
    </div>
    <div style="margin-top:8px;"><button id="rndMat">Randomize</button></div>
  `;
  moduleArea.appendChild(container);

  const A = document.getElementById('A'), B = document.getElementById('B'), C = document.getElementById('C');
  const makeInput = (v) => { const inp = document.createElement('input'); inp.value = v; inp.style.width='56px'; inp.oninput = compute; return inp; };
  let aVals = [], bVals = [];

  function init(){
    A.innerHTML=''; B.innerHTML=''; C.innerHTML='';
    aVals = []; bVals = [];
    for(let i=0;i<2;i++){
      for(let j=0;j<3;j++){ const inp = makeInput(Math.round((Math.random()-0.5)*6)); aVals.push(inp); A.appendChild(inp); }
    }
    for(let i=0;i<3;i++){
      for(let j=0;j<2;j++){ const inp = makeInput(Math.round((Math.random()-0.5)*6)); bVals.push(inp); B.appendChild(inp); }
    }
    for(let i=0;i<2;i++){ for(let j=0;j<2;j++){ const out = document.createElement('div'); out.style.background='rgba(255,255,255,0.03)'; out.style.padding='8px'; out.style.borderRadius='6px'; C.appendChild(out); } }
    compute();
  }
  function compute(){
    const aMat = [[ Number(aVals[0].value),Number(aVals[1].value),Number(aVals[2].value) ], [Number(aVals[3].value),Number(aVals[4].value),Number(aVals[5].value)] ];
    const bMat = [
      [Number(bVals[0].value),Number(bVals[1].value)],
      [Number(bVals[2].value),Number(bVals[3].value)],
      [Number(bVals[4].value),Number(bVals[5].value)]
    ];
    // C = A(2x3) x B(3x2) => C(2x2)
    const outDivs = C.children;
    for(let i=0;i<2;i++){
      for(let j=0;j<2;j++){
        let s=0;
        for(let k=0;k<3;k++) s += aMat[i][k]*bMat[k][j];
        outDivs[i*2 + j].textContent = s.toFixed(2);
      }
    }
  }
  document.getElementById('rndMat').onclick = init;
  init();
}

/* ---------- Export state ---------- */
document.getElementById('exportState').onclick = ()=>{
  const payload = { topics: topicsJson, time: new Date().toISOString() };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type:'application/json' });
  const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href=url; a.download='interactive-state.json'; a.click();
}

</script>
</body>
</html>
"""

# -------------------------
# Backend: extract endpoint
# -------------------------
@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/extract", methods=["POST"])
def api_extract():
    """
    Expect JSON: { text: "..." }
    Return hierarchical JSON:
    { topics: [ { id, title, subtopics: [ { id, title, bullets[], interactive? } ] } ] }
    """
    body = request.get_json(force=True)
    text = body.get("text", "")
    if not text.strip():
        return jsonify({"error":"no text provided"}), 400

    prompt_system = "You are an assistant that extracts a clean hierarchical JSON of topics and subtopics from a text corpus. ALWAYS output valid JSON ONLY. Use concise titles and short ids (lowercase, hyphen)."
    prompt_user = f"""
Analyze the TEXT below and extract the main topics (3-8). For each topic, extract 2-8 subtopics.
For each subtopic provide 2-6 short bullet points.

If a subtopic is obviously tied to an interactive demo, set an \"interactive\" field to one of: "kmeans", "perceptron", "gradient", "confusion", "matrix" (only when relevant).

OUTPUT ONLY valid JSON with this exact shape:
{{ "topics": [ {{ "id":"...", "title":"...", "subtopics":[ {{ "id":"...", "title":"...", "bullets":[...], "interactive":"optional" }} ] }} ] }}

TEXT:
\"\"\"{text}\"\"\"
"""
    try:
        # choose a model you have access to; adjust as needed
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":prompt_system}, {"role":"user","content":prompt_user}],
            max_tokens=900,
            temperature=0.0,
        )
        raw = resp['choices'][0]['message']['content']
    except Exception as e:
        print("OpenAI call failed:", e)
        # fallback example
        fallback = {
            "topics": [
                {"id":"kmeans", "title":"KMeans Clustering", "subtopics":[ {"id":"kmeans-intro","title":"KMeans (interactive)","bullets":["Choose K","Initialize centroids","Assign points","Update centroids"], "interactive":"kmeans"} ]}
            ]
        }
        return jsonify(fallback)

    # parse JSON robustly
    try:
        parsed = json.loads(raw)
        return jsonify(parsed)
    except Exception:
        # try substring extraction
        s = raw.find('{'); e = raw.rfind('}')
        if s!=-1 and e!=-1:
            maybe = raw[s:e+1]
            try:
                parsed = json.loads(maybe)
                return jsonify(parsed)
            except Exception as e2:
                print("Parse failed:", e2, "raw:", raw[:1000])
                return jsonify({"error":"failed to parse model output", "raw": raw}), 500
        return jsonify({"error":"no json in model output", "raw":raw}), 500

if __name__ == "__main__":
    print("Starting enhanced interactive extractor at http://127.0.0.1:5000")
    app.run(debug=True)
