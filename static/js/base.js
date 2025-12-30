document.addEventListener("DOMContentLoaded", () => {
  // AOS ANIMATIONS
  AOS.init({
    duration: 700,
    easing: "ease-out-cubic",
    once: false, // animate only once
    offset: 80, // trigger slightly before visible
  });

  // Theme Toggle
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

  
  document.addEventListener("DOMContentLoaded", () => {
    const feedLink = document.getElementById("feedLink");
    const feedSection = document.getElementById("feed-section");

    if (feedLink && feedSection && window.location.pathname === "/home") {
      feedLink.addEventListener("click", (e) => {
        e.preventDefault();
        feedSection.scrollIntoView({ behavior: "smooth" });
      });
    }
  });
});
