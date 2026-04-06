function loadKMeansPlayground(config) {
  const area = document.getElementById("interactiveArea");

  area.innerHTML = `
    <div class="kmeans-box">
      <div class="controls">
        <label>K:
          <input type="range" id="kRange" min="1" max="5" value="${config.k}">
        </label>
        <span id="kValue">${config.k}</span>
      </div>

      <canvas id="kCanvas" width="500" height="350"></canvas>

      <div class="formula">
        Distance:
        <code id="distanceFormula"></code>
      </div>

      <canvas id="elbowCanvas" width="500" height="200"></canvas>
    </div>
  `;

  initKMeans(config.points, config.k);
}














let points = [];
let centroids = [];
let selectedPoint = null;

function initKMeans(initPoints, k) {
  points = initPoints.map(p => ({ x: p[0]*40+50, y: p[1]*40+50 }));
  centroids = points.slice(0, k);

  draw();
  attachEvents();
  computeWCSS();
}

function draw() {
  const canvas = document.getElementById("kCanvas");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0,0,canvas.width,canvas.height);

  // points
  points.forEach(p => {
    ctx.beginPath();
    ctx.arc(p.x, p.y, 6, 0, Math.PI*2);
    ctx.fillStyle = "#2563eb";
    ctx.fill();
  });

  // centroids
  centroids.forEach(c => {
    ctx.beginPath();
    ctx.arc(c.x, c.y, 10, 0, Math.PI*2);
    ctx.fillStyle = "#dc2626";
    ctx.fill();
  });
}

function attachEvents() {
  const canvas = document.getElementById("kCanvas");

  canvas.onmousedown = e => {
    points.forEach(p => {
      if (Math.hypot(p.x-e.offsetX, p.y-e.offsetY) < 8)
        selectedPoint = p;
    });
  };

  canvas.onmousemove = e => {
    if (!selectedPoint) return;
    selectedPoint.x = e.offsetX;
    selectedPoint.y = e.offsetY;
    draw();
    updateFormula();
    computeWCSS();
  };

  canvas.onmouseup = () => selectedPoint = null;
}









function updateFormula() {
  if (points.length < 2) return;

  const p1 = points[0];
  const p2 = points[1];

  const dx = (p2.x - p1.x).toFixed(1);
  const dy = (p2.y - p1.y).toFixed(1);
  const d = Math.sqrt(dx*dx + dy*dy).toFixed(2);

  document.getElementById("distanceFormula").innerText =
    `√((${dx})² + (${dy})²) = ${d}`;
}










function computeWCSS() {
  let wcss = 0;

  points.forEach(p => {
    const c = centroids[0];
    wcss += Math.pow(p.x-c.x,2) + Math.pow(p.y-c.y,2);
  });

  drawElbow(wcss);
}

function drawElbow(wcss) {
  const canvas = document.getElementById("elbowCanvas");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0,0,canvas.width,canvas.height);

  ctx.beginPath();
  ctx.moveTo(20,180);
  ctx.lineTo(20 + wcss/100, 180 - wcss/200);
  ctx.stroke();
}
