console.log("certificate.js loaded");

document.addEventListener("DOMContentLoaded", () => {

  const student = document.getElementById("studentName");
  const course = document.getElementById("courseSelect");
  const date = document.getElementById("issueDate");
  const trainer = document.getElementById("trainerName");

  const prevStudent = document.getElementById("prevStudent");
  const prevCourse = document.getElementById("prevCourse");
  const prevTrainer = document.getElementById("prevTrainer");
  const prevDate = document.getElementById("prevDate");
  const prevDate2 = document.getElementById("prevDate2");
  const signaturePreview = document.getElementById("signaturePreview");

  /* ======================
     LIVE TEXT BINDING
  ====================== */
  student.addEventListener("input", e => {
    prevStudent.innerText = e.target.value || "STUDENT NAME";
  });

  trainer.addEventListener("input", e => {
    prevTrainer.innerText = e.target.value || "TRAINER NAME";
  });

  date.addEventListener("input", e => {
    prevDate.innerText = e.target.value;
    prevDate2.innerText = e.target.value;
  });

  /* ======================
     COURSE DROPDOWN
  ====================== */
  fetch("/trainer/certificates/courses")
    .then(res => res.json())
    .then(courses => {
      courses.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c.id;
        opt.textContent = c.title;
        course.appendChild(opt);
      });
    });

  course.addEventListener("change", e => {
    prevCourse.innerText =
      e.target.selectedOptions[0]?.text || "Course Name";
  });

  /* ======================
     SIGNATURE PAD
  ====================== */
  const canvas = document.getElementById("signaturePad");
  const ctx = canvas.getContext("2d");

  let drawing = false;

  canvas.addEventListener("mousedown", e => {
    drawing = true;
    ctx.beginPath();
    ctx.moveTo(e.offsetX, e.offsetY);
  });

  canvas.addEventListener("mousemove", e => {
    if (!drawing) return;
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.strokeStyle = "#000";
    ctx.lineTo(e.offsetX, e.offsetY);
    ctx.stroke();
  });

  canvas.addEventListener("mouseup", () => drawing = false);
  canvas.addEventListener("mouseleave", () => drawing = false);

  /* ======================
     SIGNATURE ACTIONS
  ====================== */
  window.clearSignature = function () {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    signaturePreview.style.display = "none";
    localStorage.removeItem("trainer_signature");
  };

  window.saveSignature = function () {
    const data = canvas.toDataURL("image/png");
    localStorage.setItem("trainer_signature", data);

    signaturePreview.src = data;
    signaturePreview.style.display = "block";

    alert("Signature saved ✔");
  };

  /* ======================
     LOAD SAVED SIGNATURE
  ====================== */
  const saved = localStorage.getItem("trainer_signature");
  if (saved) {
    signaturePreview.src = saved;
    signaturePreview.style.display = "block";
  }
});
