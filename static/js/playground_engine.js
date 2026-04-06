function renderPlaygrounds(playground) {
  const area = document.getElementById("interactiveArea");

  if (!playground || !playground.type) {
    area.innerHTML = "⚠ No interactive playground available.";
    return;
  }

  if (playground.type === "kmeans") {
    loadKMeansPlayground(playground);
  }
}

function renderScatterPlayground(data) {
  const canvas = document.createElement("canvas");
  canvas.width = 500;
  canvas.height = 400;
  canvas.style.border = "1px solid #ccc";

  const slider = document.createElement("input");
  slider.type = "range";
  slider.min = data.controls[0].min;
  slider.max = data.controls[0].max;
  slider.value = data.controls[0].default;

  const label = document.createElement("div");
  label.innerText = `${data.controls[0].label}: ${slider.value}`;

  slider.oninput = () => {
    label.innerText = `${data.controls[0].label}: ${slider.value}`;
    draw(slider.value);
  };

  area.append(label, canvas, slider);

  function draw(k) {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "#000";
    ctx.fillText(`K = ${k}`, 10, 20);

    for (let i = 0; i < 20; i++) {
      ctx.beginPath();
      ctx.arc(
        Math.random() * 400 + 50,
        Math.random() * 300 + 50,
        4,
        0,
        Math.PI * 2
      );
      ctx.fill();
    }
  }

  draw(slider.value);
}
