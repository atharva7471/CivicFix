document.addEventListener("DOMContentLoaded", () => {
  // =========================
  // VOTING
  // =========================
  document.querySelectorAll(".vote-btn").forEach((button) => {
    button.addEventListener("click", async () => {
      if (button.disabled) return;

      const problemId = button.dataset.id;

      try {
        const res = await fetch(`/vote/${problemId}`, { method: "POST" });
        const data = await res.json();

        if (res.status === 401) {
          showToast("Please login to vote", "error");
          return;
        }

        if (!res.ok) {
          if (data.error === "Already voted") {
            showToast("You have already voted on this issue", "error");
            button.disabled = true;
            button.classList.add("voted");
            return;
          }

          showToast(data.error || "Voting failed", "error");
          return;
        }

        // Success
        const voteSpan = button.querySelector("span");
        voteSpan.innerText = `${data.votes} Votes`;

        voteSpan.classList.remove("vote-count-pop");
        void voteSpan.offsetWidth;
        voteSpan.classList.add("vote-count-pop");

        button.classList.add("voted");
        button.disabled = true;

        showToast("Vote counted successfully", "success");
      } catch {
        showToast("Network error. Try again.", "error");
      }
    });
  });

  // =========================
  // HERO NAVBAR SCROLL
  // =========================
  const navbar = document.getElementById("navbar");
  const hero = document.querySelector(".hero");

  if (navbar && hero) {
    const heroHeight = hero.offsetHeight - 80;
    window.addEventListener("scroll", () => {
      navbar.classList.toggle("fixed", window.scrollY > heroHeight);
    });
  }
  document.querySelectorAll(".share-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();

      const url = btn.dataset.url;
      const title = "Civic Issue Reported";
      const text = "Check out this civic issue on CivicFix.";

      // ✅ Mobile / supported browsers
      if (navigator.share) {
        try {
          await navigator.share({
            title: title,
            text: text,
            url: url,
          });
        } catch (err) {
          console.log("Share cancelled");
        }
      } else {
        // 💻 Desktop fallback → copy link
        try {
          await navigator.clipboard.writeText(url);
          showToast("Link copied to clipboard!");
        } catch (err) {
          alert("Copy failed. Please copy manually.");
        }
      }
    });
  });
});
