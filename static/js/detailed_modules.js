document.querySelectorAll(".course-item").forEach(item => {
  item.addEventListener("click", async () => {

    document.querySelectorAll(".course-item")
      .forEach(i => i.classList.remove("active"));

    item.classList.add("active");

    const courseId = item.dataset.id;
    const title = item.dataset.title;

    courseTitle.innerText = title;

    // 🔄 Fetch AI summary
    rawContent.value = "🔍 Loading AI summary...";
    rawContent.disabled = true;

    try {
      const res = await fetch(`/trainer/course/${courseId}/summary`);
      const data = await res.json();

      if (data.summary && data.summary.trim().length > 0) {
        rawContent.value = data.summary;
      } else {
        rawContent.value = "";
        rawContent.placeholder =
          "⚠ No AI summary found. Paste content manually.";
      }
    } catch (err) {
      console.error(err);
      rawContent.value = "";
      rawContent.placeholder =
        "❌ Failed to load summary. Paste content manually.";
    }

    rawContent.disabled = false;
  });



  /* =========================
     GENERATE MODULES
  ========================== */
  generateBtn.addEventListener("click", async () => {
    const content = rawContent.value.trim();

    if (!content) {
  alert("Please select a course or paste content first");
  return;
}


    const res = await fetch("/trainer/detailed-modules/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content })
    });

    const data = await res.json();

    if (!Array.isArray(data.modules)) {
      alert("AI processing failed");
      console.error(data);
      return;
    }

    renderModules(data.modules);
  });

  /* =========================
     RENDER MODULE TILES
  ========================== */
  function renderModules(modules) {
    modulesContainer.innerHTML = "";

    modules.forEach(m => {
      const tile = document.createElement("div");
      tile.className = "dm-tile";
      tile.innerText = m.title;

      tile.addEventListener("click", () => {
        document.querySelectorAll(".dm-tile")
          .forEach(t => t.classList.remove("active"));

        tile.classList.add("active");
        openTopic(m.title);
      });

      modulesContainer.appendChild(tile);
    });
  }

  /* =========================
     OPEN TOPIC → AI PLAYGROUND
  ========================== */
  async function openTopic(topic) {
  const panel = document.getElementById("learnPanel");
  panel.innerHTML = "<p>🧠 Generating interactive playground...</p>";

  const res = await fetch("/trainer/detailed-modules/explain", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic })
  });

  const data = await res.json();

  panel.innerHTML = `
    <h2>${data.topic}</h2>
    <p>${data.concept_overview}</p>

    <h4>Learning Steps</h4>
    <ul>${(data.learning_steps || []).map(s => `<li>${s}</li>`).join("")}</ul>

    <h4>Formulas</h4>
    <code>${(data.formulas || []).join("<br>")}</code>

    <h4>Interactive Playground</h4>
    <div id="interactiveArea"></div>
  `;

  renderPlayground(data);
}





function renderPlaygrounds(playground) {
  if (!playground || !playground.type) return;

  const area = document.getElementById("interactiveArea");
  area.innerHTML = "";

  if (playground.type === "kmeans") {
    loadKMeansPlayground(playground);
  } else {
    area.innerHTML = "<p>⚠ No playground available for this topic yet.</p>";
  }
}

});





















