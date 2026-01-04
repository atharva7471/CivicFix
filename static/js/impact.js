// Login to like and likes
document.querySelectorAll(".like-btn").forEach((button) => {
  button.addEventListener("click", () => {
    const problemId = button.dataset.id;

    fetch(`/like/${problemId}`, { method: "POST" })
      .then(async (res) => {
        let data = {};
        try {
          data = await res.json();
        } catch {
          showToast("Please login to continue", "error");
          return;
        }

        // 🔒 Not logged in
        if (!res.ok && data.error === "Login required") {
          showToast("Please login to like resolved issues", "error");
          return;
        }

        // 🚫 Already liked
        if (!res.ok && data.error === "Already liked") {
          showToast("You already liked this solution ❤️", "error");
          button.disabled = true;
          button.classList.add("liked");
          return;
        }

        // ❌ Other error
        if (!res.ok) {
          showToast("Like failed", "error");
          return;
        }

        // ✅ Success
        const span = button.querySelector("span");
        span.innerText = data.likes;

        button.disabled = true;
        button.classList.add("liked");

        showToast("Thanks for supporting this solution ❤️", "success");
      })
      .catch(() => {
        showToast("Something went wrong", "error");
      });
  });
});

const tabButtons = document.querySelectorAll(".tab-btn");
const tabContents = document.querySelectorAll(".tab-content");
const toastContainer = document.getElementById("toast-container");

/** * Tab Switching Logic
 */
tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.tab;

    // Update button states
    tabButtons.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");

    // Update content visibility
    tabContents.forEach((content) => {
      content.classList.remove("active");
      if (content.id === target) {
        content.classList.add("active");
      }
    });
  });
});
