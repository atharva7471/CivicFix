// =========================
// GLOBAL BASE JS
// =========================
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
});
