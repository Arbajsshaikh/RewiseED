// ui.js - small interactions for sidebar toggle and compact behaviour
document.addEventListener('DOMContentLoaded', function(){
  const leftCollapse = document.getElementById('leftCollapse');
  const compactToggle = document.getElementById('compactToggle');

  leftCollapse && leftCollapse.addEventListener('click', () => {
    document.querySelector('.sidebar-left').classList.toggle('collapsed');
    document.querySelector('.app-shell').classList.toggle('left-collapsed');
  });

  compactToggle && compactToggle.addEventListener('click', () => {
    document.querySelector('.sidebar-left').classList.toggle('compact-icons');
  });

  // basic search submit on Enter
  const globalSearch = document.getElementById('globalSearch');
  if (globalSearch) {
    globalSearch.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        // you can wire this to an endpoint later
        const q = globalSearch.value.trim();
        if (q) {
          window.location.href = '/trainer/search?q=' + encodeURIComponent(q);
        }
      }
    });
  }
});
