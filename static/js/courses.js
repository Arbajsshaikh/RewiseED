document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("courseSearch");
  const levelFilter = document.getElementById("levelFilter");
  const table = document.getElementById("coursesTable");
  const rows = table ? Array.from(table.querySelectorAll("tbody tr")) : [];

  // simple search + filter
  function applyFilters() {
    const q = (searchInput?.value || "").toLowerCase();
    const level = levelFilter?.value || "";

    rows.forEach((row) => {
      const title = row.querySelector(".course-title-text")?.textContent.toLowerCase() || "";
      const rowLevel = row.getAttribute("data-level") || "";
      const matchText = !q || title.includes(q);
      const matchLevel = !level || rowLevel === level;
      row.style.display = matchText && matchLevel ? "" : "none";
    });
  }

  if (searchInput) searchInput.addEventListener("input", applyFilters);
  if (levelFilter) levelFilter.addEventListener("change", applyFilters);

  // delete confirmation
  document.querySelectorAll(".delete-video-form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      const ok = confirm("Delete this video permanently?");
      if (!ok) e.preventDefault();
    });
  });

  
  document.querySelectorAll(".delete-course-form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      const ok = confirm("Are you sure you want to delete this course?");
      if (!ok) e.preventDefault();
    });
  });
});
