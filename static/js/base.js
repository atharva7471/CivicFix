// =========================
// Toast Function
// =========================
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

// Apply saved theme immediately (prevents flash)
if (localStorage.getItem("theme") === "dark") {
  document.documentElement.classList.add("dark");
}

document.addEventListener("DOMContentLoaded", () => {
  AOS.init({
    duration: 700,
    easing: "ease-out-cubic",
    once: false, // animate repeatedly
    offset: 80, // trigger slightly before visible
  });

  // =========================
  // THEME TOGGLE
  // =========================
  const toggle = document.getElementById("themeToggle");

  if (toggle) {
    toggle.addEventListener("click", () => {
      document.documentElement.classList.toggle("dark");

      localStorage.setItem(
        "theme",
        document.documentElement.classList.contains("dark") ? "dark" : "light"
      );
    });
  }
  // =========================
  // ACCOUNT DROPDOWN
  // =========================
  const accountBtn = document.querySelector(".account-btn");
  const dropdown = document.querySelector(".account-dropdown");

  if (accountBtn && dropdown) {
    accountBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      dropdown.classList.toggle("open");
    });

    document.addEventListener("click", () => {
      dropdown.classList.remove("open");
    });
  }
  // Share btn
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

  // 1. Toggle menu when clicking the hamburger
  const menuToggle = document.getElementById("mobile-menu");
  const navLinks = document.querySelector(".nav-links");

  menuToggle.addEventListener("click", (e) => {
    navLinks.classList.toggle("active");
    e.stopPropagation(); // Prevents the window listener from firing immediately
  });

  // 2. Close menu when clicking outside
  window.addEventListener("click", (e) => {
    // If the menu is open AND the click wasn't on the menu or toggle button
    if (
      navLinks.classList.contains("active") &&
      !navLinks.contains(e.target) &&
      !menuToggle.contains(e.target)
    ) {
      navLinks.classList.remove("active");
    }
  });

  // 3. Optional: Close menu when a link inside is clicked
  navLinks.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      navLinks.classList.remove("active");
    });
  });
});
