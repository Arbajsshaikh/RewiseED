// static/js/main.js
// Single entry for basic UI behavior + tilt effect for .tilt-card
document.addEventListener("DOMContentLoaded", () => {
  /* -------------------- password toggle -------------------- */
  const togglePassword = document.getElementById("togglePassword");
  const passwordInput = document.getElementById("password");
  if (togglePassword && passwordInput) {
    togglePassword.addEventListener("click", () => {
      const type = passwordInput.getAttribute("type") === "password" ? "text" : "password";
      passwordInput.setAttribute("type", type);
      // accessible label toggle (if present)
      const aria = togglePassword.getAttribute("aria-pressed") === "true";
      togglePassword.setAttribute("aria-pressed", String(!aria));
    });
  }

  /* -------------------- flash messages auto-hide -------------------- */
  const flashes = document.querySelectorAll(".flash-message");
  if (flashes.length) {
    setTimeout(() => {
      flashes.forEach(el => el.classList.add("hide"));
    }, 3000);
  }

  /* -------------------- dark mode toggle -------------------- */
  const darkToggle = document.querySelector(".dark-toggle");
  if (darkToggle) {
    darkToggle.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode");
      // persist preference (optional)
      try {
        localStorage.setItem("rw_dark_mode", document.body.classList.contains("dark-mode") ? "1" : "0");
      } catch (e) { /* ignore if localStorage unavailable */ }
    });
    // restore (if stored)
    try {
      if (localStorage.getItem("rw_dark_mode") === "1") document.body.classList.add("dark-mode");
    } catch (e) {}
  }

  /* -------------------- small utilities -------------------- */
  const searchBtn = document.querySelector(".js-open-search");
  if (searchBtn) {
    searchBtn.addEventListener("click", () => {
      // small placeholder — replace with a real panel later
      alert("Search panel coming soon. For now, use course/student filters.");
    });
  }

  const notifBtn = document.querySelector(".js-open-notifications");
  if (notifBtn) {
    notifBtn.addEventListener("click", () => {
      alert("No new notifications 🎉");
    });
  }

  /* -------------------- Tilt effect for .tilt-card --------------------
     Safe: does NOT transform table rows or whole table cells.
     Applies transform to inner .tilt-card only (so table layout stays intact).
     Tweak maxTilt and perspective for stronger/weaker effect.
  --------------------------------------------------------------- */
  const tiltSelector = ".tilt-card";
  const tiltEls = Array.from(document.querySelectorAll(tiltSelector));
  const isSmallScreen = () => window.matchMedia("(max-width: 720px)").matches;

  if (tiltEls.length) {
    const maxTilt = 8;           // degrees (smaller = subtler)
    const perspective = 900;     // px
    const scaleOnHover = 1.02;   // slight pop

    // Helper: get bounding center
    function getCenterRect(rect) {
      return { cx: rect.left + rect.width / 2, cy: rect.top + rect.height / 2 };
    }

    // For performance, attach a single mousemove on document when hovering an element
    tiltEls.forEach(el => {
      let pointerInside = false;
      let raf = null;

      function onEnter(e) {
        if (isSmallScreen()) return;
        pointerInside = true;
        el.style.willChange = "transform";
        el.style.transition = "transform 180ms ease, box-shadow 180ms ease";
        el.style.transformOrigin = "center center";
        el.style.boxShadow = "0 12px 30px rgba(2,6,23,0.12)";
        // add a subtle class for CSS sheen animation (handled in CSS)
        el.classList.add("tilt-active");
        document.addEventListener("mousemove", onMove);
      }

      function onLeave() {
        pointerInside = false;
        el.style.transition = "transform 300ms cubic-bezier(.2,.9,.2,1), box-shadow 300ms ease";
        el.style.transform = `perspective(${perspective}px) rotateX(0deg) rotateY(0deg) scale(1)`;
        el.style.boxShadow = "0 6px 18px rgba(2,6,23,0.06)";
        el.classList.remove("tilt-active");
        document.removeEventListener("mousemove", onMove);
        if (raf) { cancelAnimationFrame(raf); raf = null; }
      }

      function onMove(evt) {
        if (!pointerInside) return;
        // Avoid tilting when user is focusing inputs inside card
        const active = document.activeElement;
        if (active && el.contains(active) && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || active.isContentEditable)) {
          // keep card steady if typing inside
          return;
        }

        // throttle using rAF
        if (raf) return;
        raf = requestAnimationFrame(() => {
          const rect = el.getBoundingClientRect();
          const center = getCenterRect(rect);
          const px = (evt.clientX - center.cx) / (rect.width / 2);  // -1 .. 1
          const py = (evt.clientY - center.cy) / (rect.height / 2); // -1 .. 1

          const rotY = Math.max(-1, Math.min(1, px)) * maxTilt; // rotateY based on X movement
          const rotX = Math.max(-1, Math.min(1, -py)) * maxTilt; // rotateX based on Y movement (invert)

          el.style.transform = `perspective(${perspective}px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale(${scaleOnHover})`;
          raf = null;
        });
      }

      // bind events
      el.addEventListener("mouseenter", onEnter);
      el.addEventListener("mouseleave", onLeave);

      // mobile: gentle 'press' effect on touchstart
      el.addEventListener("touchstart", () => {
        if (isSmallScreen()) {
          el.style.transform = `scale(${scaleOnHover})`;
          el.classList.add("tilt-active");
        }
      }, { passive: true });
      el.addEventListener("touchend", () => {
        if (isSmallScreen()) {
          el.style.transform = `scale(1)`;
          el.classList.remove("tilt-active");
        }
      });
    });

    // when window resized, remove transforms on small screens
    window.addEventListener("resize", () => {
      if (isSmallScreen()) {
        tiltEls.forEach(el => {
          el.style.transform = "";
          el.style.willChange = "";
          el.style.transition = "";
          el.classList.remove("tilt-active");
        });
      }
    });
  }
});


function downloadTextFile(filename, content) {
  if (!content || content.trim() === "") {
    alert("Nothing to download.");
    return;
  }

  const blob = new Blob([content], { type: "text/plain;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();

  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}


