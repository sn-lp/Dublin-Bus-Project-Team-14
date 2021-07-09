//Google Maps
let map;

function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 53.3498, lng: -6.2603 },
    zoom: 12,
    disableDefaultUI: true,
  });
  initAutocomplete();
  initDirectionsService();
  initDirectionsRenderer();
}

//Initialise Directions service and renderer
let directionsService1;
let directionsRenderer1;

function initDirectionsService() {
  directionsService1 = new google.maps.DirectionsService();
}

function initDirectionsRenderer() {
  directionsRenderer1 = new google.maps.DirectionsRenderer();
}

//Directions
function calculateAndDisplayRoute(directionsService, directionsRenderer) {
  directionsRenderer.setMap(map);

  directionsService
    .route({
      origin: {
        query: document.getElementById("origin").value,
      },
      destination: {
        query: document.getElementById("destination").value,
      },
      travelMode: google.maps.TravelMode.TRANSIT,
      transitOptions: {
        modes: ["BUS"],
      },
    })
    .then((response) => {
      directionsRenderer.setDirections(response);
      directionsRenderer.setPanel(
        document.getElementById("directions_results")
      );

      //Switching UI
      const searchUI = document.getElementById("searchUI");
      searchUI.style.display = "none";

      const resultsUI = document.getElementById("resultsUI");
      resultsUI.style.display = "block";
    })
    .catch((e) => window.alert("Directions request failed due to " + status));
}

//Clear the map
function clearDirections(directionsRenderer) {
  directionsRenderer.set("directions", null);
  directionsRenderer.setPanel(document.getElementById("directions_results"));

  resultsUI.style.display = "none";
  searchUI.style.display = "block";
}

//Setting datetime
var today = new Date();
var year = today.getFullYear();
var month = today.getMonth() + 1;
var day = today.getDate();
var hour = today.getHours();
var minute = today.getMinutes();

const date_vars = [year, month, day, hour, minute];

for (var i = 0; i < date_vars.length; i++) {
  if (date_vars[i] < 10) {
    date_vars[i] = "0" + String(date_vars[i]);
  } else {
    date_vars[i] = String(date_vars[i]);
  }
}

var datetime_string =
  date_vars[0] +
  "-" +
  date_vars[1] +
  "-" +
  date_vars[2] +
  "T" +
  date_vars[3] +
  ":" +
  date_vars[4];

document.getElementById("departure-time").value = datetime_string;
document.getElementById("departure-time").min = datetime_string;

//Button to hide UI to just show map
const targetDiv = document.getElementById("over_map");
const toggleBtn = document.getElementById("map_toggle");

toggleBtn.onclick = function () {
  if (targetDiv.style.display !== "none") {
    targetDiv.style.display = "none";
  } else {
    targetDiv.style.display = "block";
  }
};

//Autocomplete
let autocomplete1;
let autocomplete2;

function initAutocomplete() {
  autocomplete1 = setAutocomplete(autocomplete1, "origin");
  autocomplete2 = setAutocomplete(autocomplete2, "destination");
}

function setAutocomplete(object, id) {
  var cityBounds = new google.maps.LatLngBounds(
    new google.maps.LatLng(53.1, -6.7),
    new google.maps.LatLng(53.7, -6.0)
  );
  object = new google.maps.places.Autocomplete(document.getElementById(id), {
    bounds: cityBounds,
    componentRestrictions: { country: "ie" },
    strictbounds: true,
    fields: ["place_id", "geometry", "name"],
  });
  return object;
}
