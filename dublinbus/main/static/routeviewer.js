let directions = [];
let mapDirectionsStops = {};
let selectedButton;
let selectedDirection;
let markers = [];

//Google Maps
let map;

function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 53.3498, lng: -6.2603 },
    zoom: 12,
    disableDefaultUI: true,
  });
}

function hideSubmitForm() {
  document.getElementById("searchRouteUI").style.display = "none";
}

function displayDirectionsButtons() {
  document.getElementById("directions-buttons").style.display = "block";
}

function injectDirectionNameInButtons() {
  document.getElementById("direction-button-0").innerText = directions[0];
  document.getElementById("direction-button-1").innerText = directions[1];
}

function displayBackToRoutesButton() {
  document.getElementById("back-to-routes").style.display = "block";
}

function goToRoutesPage() {
  window.location.reload();
}

function changeDirection(directionNumber) {
  // Get the container element
  const btnContainer = document.getElementById("directions-buttons");

  // Get all buttons with class="nav-link" inside the container
  const btns = btnContainer.getElementsByClassName("nav-link");

  var current = document.getElementsByClassName("active");
  current[0].className = current[0].className.replace(" active", "");
  selectedButton = document.getElementById(
    "direction-button-" + directionNumber
  );
  selectedButton.className += " active";
  selectedDirection = directions[directionNumber];
  drawMarkers(mapDirectionsStops[selectedDirection]);
}

function drawMarkers(stops) {
  if (markers.length > 0) {
    markers.forEach((marker) => {
      marker.setMap(null);
    });
  }
  markers = [];
  for (const [stopName, coordinates] of Object.entries(stops)) {
    const newMarker = new google.maps.Marker({
      position: {
        lat: coordinates.latitude,
        lng: coordinates.longitude,
      },
      map,
    });
    markers.push(newMarker);
  }
}

function getBusStopsFromBackend() {
  routeNumber = document.getElementById("bus-route-input").value;
  busRoutesEndpoint = "/api/get_bus_stops/?route_number=" + routeNumber;
  fetch(busRoutesEndpoint)
    .then((response) => {
      if (response.ok) {
        return response.json();
      } else {
        document.getElementById("user-error-message").innerText =
          "Something went wrong, please try again.";
        // status and statusText doesn't work for all browsers but works in Chrome and Safari
        throw new Error(response.status + ", " + response.statusText);
      }
    })
    .then((busRoutes) => {
      if (
        Object.keys(busRoutes).length === 0 &&
        busRoutes.constructor === Object
      ) {
        // if the user inputs an invalid route number, display error message
        document.getElementById("user-error-message").innerText =
          "Please enter a valid route number";
        return;
      }
      mapDirectionsStops = busRoutes;
      index = 0;
      for (const [direction, stops] of Object.entries(busRoutes)) {
        directions.push(direction);
        if (index == 0) {
          drawMarkers(stops);
        }
        index += 1;
      }
      hideSubmitForm();
      displayBackToRoutesButton();
      displayDirectionsButtons();
      injectDirectionNameInButtons();
      selectedDirection = directions[0];
    })
    .catch((error) => {
      console.log(error);
    });
}
