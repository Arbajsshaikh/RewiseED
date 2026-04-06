// list page filters
function initStudentsListFilters() {
  const searchInput = document.getElementById("studentSearch");
  const statusFilter = document.getElementById("statusFilter");
  const table = document.getElementById("studentsTable");
  if (!table) return;

  const rows = Array.from(table.querySelectorAll("tbody tr"));

  function applyFilters() {
    const q = (searchInput?.value || "").toLowerCase();
    const status = statusFilter?.value || "";

    rows.forEach((row) => {
      const name = row.querySelector("td:nth-child(1)")?.textContent.toLowerCase() || "";
      const email = row.querySelector("td:nth-child(2)")?.textContent.toLowerCase() || "";
      const rowStatus = row.getAttribute("data-status") || "";
      const matchText = !q || name.includes(q) || email.includes(q);
      const matchStatus = !status || status === rowStatus;
      row.style.display = matchText && matchStatus ? "" : "none";
    });
  }

  if (searchInput) searchInput.addEventListener("input", applyFilters);
  if (statusFilter) statusFilter.addEventListener("change", applyFilters);
}

// overview charts
function initStudentOverviewCharts(config) {
  const { dailyLabels, dailyValues, monthlyLabels, monthlyValues, courseLabels, courseProgress } = config;

  const dailyCtx = document.getElementById("dailyHoursChart");
  if (dailyCtx && window.Chart) {
    new Chart(dailyCtx, {
      type: "line",
      data: {
        labels: dailyLabels,
        datasets: [
          {
            label: "Hours",
            data: dailyValues,
            tension: 0.3,
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true },
        },
      },
    });
  }

  const monthlyCtx = document.getElementById("monthlyHoursChart");
  if (monthlyCtx && window.Chart) {
    new Chart(monthlyCtx, {
      type: "bar",
      data: {
        labels: monthlyLabels,
        datasets: [
          {
            label: "Hours per month",
            data: monthlyValues,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true },
        },
      },
    });
  }

  const courseCtx = document.getElementById("courseProgressChart");
  if (courseCtx && window.Chart) {
    new Chart(courseCtx, {
      type: "bar",
      data: {
        labels: courseLabels,
        datasets: [
          {
            label: "Progress (%)",
            data: courseProgress,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, max: 100 },
        },
      },
    });
  }
}

// per-course chart
function initStudentCourseCharts(config) {
  const { dailyLabels, dailyValues } = config;
  const ctx = document.getElementById("courseDailyChart");
  if (ctx && window.Chart) {
    new Chart(ctx, {
      type: "line",
      data: {
        labels: dailyLabels,
        datasets: [
          {
            label: "Hours",
            data: dailyValues,
            tension: 0.3,
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true },
        },
      },
    });
  }
}

// auto-init on each page
document.addEventListener("DOMContentLoaded", () => {
  initStudentsListFilters();
});
