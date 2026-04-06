function renderInteractive(data) {
  const win = window.open("", "_blank");
  win.document.write(`
    <html>
    <head>
      <title>${data.title}</title>
      <style>
        body { font-family: Inter; padding: 20px; }
        .card { background:#fff; padding:20px; margin-bottom:20px; border-radius:12px; }
      </style>
    </head>
    <body>
      <h1>${data.title}</h1>
      ${data.sections.map(renderSection).join("")}
    </body>
    </html>
  `);
}

function renderSection(sec) {
  if (sec.type === "text")
    return `<div class="card">${sec.content}</div>`;

  if (sec.type === "steps")
    return `<div class="card"><ul>${sec.items.map(i=>`<li>${i}</li>`).join("")}</ul></div>`;

  if (sec.type === "formula")
    return `<div class="card"><pre>${sec.content}</pre></div>`;

  return "";
}
function renderLearningPanel(data) {
  const panel = document.getElementById("learnPanel");

  panel.innerHTML = `
    <h2>${data.topic}</h2>
    <p>${data.explanation}</p>

    ${renderSteps(data.steps)}
    ${renderFormulas(data.formulas)}
    <div id="interactiveArea"></div>
  `;

  renderInteractions(data.interactions);
}

function renderSteps(steps = []) {
  if (!steps.length) return "";
  return `<ol>${steps.map(s => `<li>${s}</li>`).join("")}</ol>`;
}

function renderFormulas(formulas = []) {
  return formulas.map(f => `
    <div class="formula-box">
      <strong>${f.name}</strong><br>
      <code>${f.formula}</code>
    </div>
  `).join("");
}
function renderInteractions(interactions = []) {
  const area = document.getElementById("interactiveArea");

  interactions.forEach(i => {
    if (i.type === "draggable_points") {
      createDraggablePoints(area);
    }

    if (i.type === "slider") {
      createSlider(area, i);
    }

    if (i.type === "plot") {
      createPlot(area, i);
    }
  });
}
