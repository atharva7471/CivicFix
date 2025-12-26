// Image preview & ML placeholder
const imageInput = document.getElementById("imageInput");

if (imageInput) {
  imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];
    if (file) {
      const mlFeedback = document.getElementById("ml-feedback");
      mlFeedback.classList.remove("hidden");
      mlFeedback.innerText = "Analyzing image with AI...";
    }
  });
}

//Vote Button for Backend
document.querySelectorAll(".vote-btn").forEach((button) => {
  button.addEventListener("click", () => {
    const problemId = button.dataset.id;

    fetch(`/vote/${problemId}`, {
      method: "POST",
    })
      .then(async (res) => {
        const data = await res.json();

        // ❌ Handle error responses
        if (!res.ok) {
          alert(data.error || "Voting failed");
          return;
        }

        // ✅ Success case
        button.querySelector("span").innerText = data.votes + " Votes";

        button.classList.add("voted");
        button.disabled = true;
      })
      .catch((err) => {
        console.error(err);
        alert("Something went wrong. Try again.");
      });
  });
});

// Map Addition
// Map Addition
document.addEventListener("DOMContentLoaded", function () {
  const mapElement = document.getElementById("map");
  if (!mapElement) return;

  const map = L.map("map").setView([19.076, 72.8777], 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  let marker;

  // 🔹 Place marker + store coordinates
  function setMarker(lat, lng) {
    if (marker) map.removeLayer(marker);

    marker = L.marker([lat, lng]).addTo(map);

    // Store for backend
    document.getElementById("latitude").value = lat;
    document.getElementById("longitude").value = lng;

    // Show coordinates to user
    document.getElementById("coords-text").innerText = `Lat: ${lat.toFixed(
      5
    )}, Lng: ${lng.toFixed(5)}`;

    // Fetch area name
    reverseGeocode(lat, lng);
  }

  // 🔹 Map click
  map.on("click", function (e) {
    setMarker(e.latlng.lat, e.latlng.lng);
  });

  // 🔹 Search location
  const searchInput = document.getElementById("location-search");

  searchInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      searchLocation(searchInput.value);
    }
  });

  function searchLocation(query) {
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${query}`)
      .then((res) => res.json())
      .then((data) => {
        if (!data.length) {
          alert("Location not found");
          return;
        }

        const place = data[0];
        const lat = parseFloat(place.lat);
        const lng = parseFloat(place.lon);

        map.setView([lat, lng], 15);
        setMarker(lat, lng);
      });
  }

  // 🔹 Reverse geocoding (coords → area name)
  function reverseGeocode(lat, lng) {
    fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`
    )
      .then((res) => res.json())
      .then((data) => {
        if (data.display_name) {
          document.getElementById(
            "area-name"
          ).innerText = `📍 ${data.display_name}`;

          // Store for backend
          document.getElementById("area-name-input").value = data.display_name;
        }
      });
  }
});
