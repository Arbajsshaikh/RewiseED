function initDeleteAssessmentConfirm() {
  document.querySelectorAll(".delete-assessment-form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      const ok = confirm("Delete this assessment and all its questions?");
      if (!ok) e.preventDefault();
    });
  });
}

function initDeleteQuestionConfirm() {
  document.querySelectorAll(".delete-question-form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      const ok = confirm("Delete this question?");
      if (!ok) e.preventDefault();
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initDeleteAssessmentConfirm();
});


function initDeleteQuestionConfirm() {
  document.querySelectorAll(".delete-question-form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      const ok = confirm("Delete this question?");
      if (!ok) e.preventDefault();
    });
  });
}
