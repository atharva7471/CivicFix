document.addEventListener("DOMContentLoaded", () => {
  /* =========================
     MAP (ADD PROBLEM ONLY)
     ========================= */
  const mapElement = document.getElementById("map");
  if (!mapElement || typeof L === "undefined") return;

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

  /* =========================
     LOCATION SEARCH
     ========================= */
  const searchInput = document.getElementById("location-search");

  if (searchInput) {
    searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        searchLocation(searchInput.value.trim());
      }
    });
  }

  function searchLocation(query) {
    if (!query) return;

    fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
        query
      )}`
    )
      .then((res) => res.json())
      .then((data) => {
        if (!data.length) {
          if (typeof showToast === "function") {
            showToast("Location not found", "error");
          }
          return;
        }

        const lat = parseFloat(data[0].lat);
        const lng = parseFloat(data[0].lon);
        map.setView([lat, lng], 15);
        setMarker(lat, lng);
      })
      .catch(() => {
        if (typeof showToast === "function") {
          showToast("Error searching location", "error");
        }
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

  /* =========================
     FORM VALIDATION
     ========================= */
  const form = document.querySelector("form");
  const latInput = document.getElementById("latitude");
  const lngInput = document.getElementById("longitude");
  const mapBox = document.getElementById("map");

  if (!form) return;
  const isAuthenticated = form.dataset.auth === "true";

  form.addEventListener("submit", (e) => {
    if (!isAuthenticated) {
      e.preventDefault();
      showToast("Login to submit an issue", "error");
      return;
    }

    if (!latInput.value || !lngInput.value) {
      e.preventDefault();

      showToast("Please select a location on the map", "error");

      mapBox.classList.add("map-error");
      mapBox.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  });
  const humanCheck = document.getElementById("humanCheck");

  form.addEventListener("submit", (e) => {
    if (!humanCheck.checked) {
      e.preventDefault();
      showToast("Please confirm the verification checkbox", "error");
      return;
    }

    // existing map validation below
  });
});
