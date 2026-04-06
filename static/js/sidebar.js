// sidebar collapse toggle (optional)
document.addEventListener("DOMContentLoaded", function(){
  const sidebar = document.querySelector(".sidebar");
  if (!sidebar) return;

  // Add a small toggle button into sidebar footer if not present
  let btn = document.createElement("button");
  btn.className = "icon-circle";
  btn.title = "Toggle sidebar";
  btn.style.marginTop = "6px";
  btn.innerText = "≡";
  btn.addEventListener("click", () => {
    sidebar.classList.toggle("collapsed");
    // save preference
    try { localStorage.setItem("rw_sidebar_collapsed", sidebar.classList.contains("collapsed")); } catch(e){}
  });
  const footer = sidebar.querySelector(".sidebar-footer");
  if (footer) footer.prepend(btn);

  // restore preference
  try {
    const saved = localStorage.getItem("rw_sidebar_collapsed");
    if (saved === "true") sidebar.classList.add("collapsed");
  } catch(e){}
});
