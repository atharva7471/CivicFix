// Show Toast Function
function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 3000);
}
/* =========================
     VOTING
     ========================= */
document.addEventListener("DOMContentLoaded", () => {
  showToast("Toast system working", "success");
});
document.querySelectorAll(".vote-btn").forEach((button) => {
  button.addEventListener("click", () => {
    const problemId = button.dataset.id;

    fetch(`/vote/${problemId}`, { method: "POST" })
      .then(async (res) => {
        const data = await res.json();

        if (!res.ok) {
          showToast(data.error || "Voting failed", "error");
          return;
        }

        button.querySelector("span").innerText = data.votes + " Votes";
        button.classList.add("voted");
        button.disabled = true;

        showToast("Vote counted successfully", "success");
      })
      .catch(() => {
        showToast("Something went wrong. Try again.", "error");
      });
  });
});

/* =========================
     HERO NAVBAR SCROLL (HOME ONLY)
     ========================= */
const navbar = document.getElementById("navbar");
const hero = document.querySelector(".hero");

if (navbar && hero) {
  const heroHeight = hero.offsetHeight;

  window.addEventListener("scroll", () => {
    if (window.scrollY > heroHeight - 80) {
      navbar.classList.add("fixed");
    } else {
      navbar.classList.remove("fixed");
    }
  });
}

// Scroll to Feed section
document.addEventListener("DOMContentLoaded", () => {
  const feedBtn = document.getElementById("scrollToFeed");
  const feedSection = document.getElementById("feed-section");

  if (feedBtn && feedSection) {
    feedBtn.addEventListener("click", (e) => {
      e.preventDefault();

      feedSection.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  }
});
