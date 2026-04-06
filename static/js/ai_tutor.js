document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("aiTutorForm");
  if (!form) return;

  const chatWindow = document.getElementById("chatWindow");
  const textarea = document.getElementById("chatMessage");
  const chatUrl = form.dataset.chatUrl;

  function appendBubble(role, text) {
    const wrapper = document.createElement("div");
    wrapper.classList.add("chat-bubble");
    wrapper.classList.add(role === "user" ? "user" : "assistant");

    if (role === "assistant") {
      const header = document.createElement("div");
      header.classList.add("bubble-header");
      header.textContent = "AI Tutor";
      wrapper.appendChild(header);
    }

    const content = document.createElement("div");
    content.classList.add("bubble-content");
    content.textContent = text;
    wrapper.appendChild(content);

    chatWindow.appendChild(wrapper);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = textarea.value.trim();
    if (!message) return;

    // Remove empty state if present
    const emptyState = chatWindow.querySelector(".chat-empty-state");
    if (emptyState) emptyState.remove();

    appendBubble("user", message);
    textarea.value = "";

    form.classList.add("busy");
    const btn = form.querySelector("button[type=submit]");
    const oldLabel = btn.textContent;
    btn.textContent = "Thinking...";

    try {
      const resp = await fetch(chatUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message })
      });

      if (!resp.ok) {
        appendBubble("assistant", "Sorry, something went wrong. Please try again.");
      } else {
        const data = await resp.json();
        if (data.reply) {
          appendBubble("assistant", data.reply);
        } else {
          appendBubble("assistant", "No reply received from AI.");
        }
      }
    } catch (err) {
      console.error(err);
      appendBubble("assistant", "Network error. Please try again.");
    } finally {
      form.classList.remove("busy");
      btn.textContent = oldLabel;
    }
  });

  // Simple auto-resize
  textarea.addEventListener("input", () => {
    textarea.style.height = "auto";
    textarea.style.height = textarea.scrollHeight + "px";
  });
});
