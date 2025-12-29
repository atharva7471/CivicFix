/* =========================
     IMAGE PREVIEW / ML FEEDBACK
     ========================= */
const imageInput = document.getElementById("imageInput");
if (imageInput) {
  imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];
    if (file) {
      const mlFeedback = document.getElementById("ml-feedback");
      if (mlFeedback) {
        mlFeedback.classList.remove("hidden");
        mlFeedback.innerText = "Analyzing image with AI...";
      }
    }
  });
}

/* =========================
     MAP (ADD PROBLEM ONLY)
     ========================= */
const mapElement = document.getElementById("map");
if (mapElement) {
  const map = L.map("map").setView([19.076, 72.8777], 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  let marker;

  function setMarker(lat, lng) {
    if (marker) map.removeLayer(marker);
    marker = L.marker([lat, lng]).addTo(map);

    document.getElementById("latitude").value = lat;
    document.getElementById("longitude").value = lng;

    document.getElementById("coords-text").innerText = `Lat: ${lat.toFixed(
      5
    )}, Lng: ${lng.toFixed(5)}`;

    reverseGeocode(lat, lng);
  }

  map.on("click", (e) => setMarker(e.latlng.lat, e.latlng.lng));

  const searchInput = document.getElementById("location-search");
  if (searchInput) {
    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        searchLocation(searchInput.value);
      }
    });
  }

  function searchLocation(query) {
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${query}`)
      .then((res) => res.json())
      .then((data) => {
        if (!data.length) return alert("Location not found");
        const lat = parseFloat(data[0].lat);
        const lng = parseFloat(data[0].lon);
        map.setView([lat, lng], 15);
        setMarker(lat, lng);
      });
  }

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
          document.getElementById("area-name-input").value = data.display_name;
        }
      });
  }
}
