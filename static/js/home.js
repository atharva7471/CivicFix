/* =========================
     VOTING
     ========================= */
document.querySelectorAll(".vote-btn").forEach((button) => {
  button.addEventListener("click", () => {
    const problemId = button.dataset.id;

    fetch(`/vote/${problemId}`, { method: "POST" })
      .then(async (res) => {
        const data = await res.json();

        if (!res.ok) {
          alert(data.error || "Voting failed");
          return;
        }

        button.querySelector("span").innerText = data.votes + " Votes";
        button.classList.add("voted");
        button.disabled = true;
      })
      .catch(() => alert("Something went wrong. Try again."));
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
        block: "start"
      });
    });
  }
});

