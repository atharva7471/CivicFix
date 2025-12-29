document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("themeToggle");

  // Load saved theme
  if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark");
  }

  toggle.addEventListener("click", () => {
    document.body.classList.toggle("dark");

    localStorage.setItem(
      "theme",
      document.body.classList.contains("dark") ? "dark" : "light"
    );
  });
});
