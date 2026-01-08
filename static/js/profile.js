document.getElementById("profileForm").addEventListener("submit", async e => {
  e.preventDefault();

  const res = await fetch("/profile/update", {
    method: "POST",
    body: new FormData(e.target)
  });

  const data = await res.json();
  if (data.success) showToast("Profile updated", "success");
});

document.getElementById("passwordForm").addEventListener("submit", async e => {
  e.preventDefault();

  const res = await fetch("/profile/password", {
    method: "POST",
    body: new FormData(e.target)
  });

  const data = await res.json();
  if (data.success) {
    showToast("Password changed", "success");
    e.target.reset();
  } else {
    showToast(data.error, "error");
  }
});
