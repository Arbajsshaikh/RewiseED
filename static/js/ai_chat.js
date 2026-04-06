// =======================
// GLOBAL STATE
// =======================
window.CURRENT_VIDEO_ID = null;

// =======================
// VIDEO LOADER
// =======================
function loadVideo(el) {
  if (!el) return;

  const videoSrc = el.dataset.videoSrc;
  const videoId = el.dataset.videoId;

  if (!videoSrc || !videoId) {
    console.error("Missing video data");
    return;
  }

  const video = document.querySelector(".video-player video");
  if (!video) {
    console.error("Video element not found");
    return;
  }

  video.src = videoSrc;
  video.load();
  video.play().catch(() => {});

  document.querySelectorAll(".video-item").forEach(i =>
    i.classList.remove("active")
  );
  el.classList.add("active");

  window.CURRENT_VIDEO_ID = videoId;
}

// =======================
// AI CHAT
// =======================
function appendMessage(text, sender) {
  const box = document.getElementById("ai-messages");
  if (!box) return;

  const div = document.createElement("div");
  div.className = sender === "user" ? "user-msg" : "ai-msg";
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

async function sendQuestion(courseId) {
  console.log("sendQuestion called");

  const input = document.getElementById("ai-input");
  if (!input) {
    alert("Input box not found");
    return;
  }

  const question = input.value.trim();
  if (!question) return;

  if (!window.CURRENT_VIDEO_ID) {
    alert("Please select a lesson first");
    return;
  }

  appendMessage(question, "user");
  input.value = "";

  try {
    const res = await fetch(`/student/course/${courseId}/ai-chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: question,
        video_id: window.CURRENT_VIDEO_ID
      })
    });

    const data = await res.json();
    appendMessage(data.answer || "No response", "ai");

  } catch (e) {
    console.error(e);
    appendMessage("AI is unavailable.", "ai");
  }
}

// =======================
// MAKE FUNCTIONS GLOBAL (🔥 THIS FIXES YOUR ERROR)
// =======================
window.sendQuestion = sendQuestion;
window.loadVideo = loadVideo;

// =======================
// INIT FIRST VIDEO
// =======================
document.addEventListener("DOMContentLoaded", () => {
  console.log("ai_chat.js loaded");

  const first = document.querySelector(".video-item");
if (first) loadVideo(first);

});
