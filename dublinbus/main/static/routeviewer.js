let directions = [];
let mapDirectionsStops = {};
let selectedButton;
let selectedDirection;
let markers = [];
let infowindow;
const defaultMapZoomLevel = 11;
const defaultMapPositionLat = 53.3498;
const defaultMapPositionLong = -6.2603;

//Google Maps
let map;

function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: defaultMapPositionLat, lng: defaultMapPositionLong },
    zoom: defaultMapZoomLevel,
    disableDefaultUI: true,
  });

  // We have one infowindow that is shared between all stops so that only one can be open at a time
  // this closes the infoWindow if one exists already, so when changing to another stop an existing infoWindow cannot be carried
  if (infowindow) {
    infowindow.close();
  }
  infowindow = new google.maps.InfoWindow();
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

function displayAddToFavouritesButton() {
  document.getElementById("add-to-favourites").style.display = "block";
}

function goToRoutesPage() {
  window.location.reload();
}

function addToFavourites() {
  console.log("ADD FFF");
}

function resetMapPositionAndZoom() {
  map.setZoom(defaultMapZoomLevel);
  map.setCenter(
    new google.maps.LatLng(defaultMapPositionLat, defaultMapPositionLong)
  );
}

function changeDirection(directionNumber) {
  resetMapPositionAndZoom();
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
  // draw the markers for the selected direction by the user
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
    // set the infoWindow content to contain the name of the bus stop
    let contentString = stopName;
    const newMarker = new google.maps.Marker({
      position: {
        lat: coordinates.latitude,
        lng: coordinates.longitude,
      },
      map,
    });
    markers.push(newMarker);
    newMarker.addListener("click", () => {
      // Close any open info window
      if (infowindow) infowindow.close();
      infowindow.setContent(contentString);
      infowindow.open(map, newMarker);
      // Pan map to the selected marker
      map.panTo(newMarker.getPosition());
    });
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
      // if the user inputs an invalid route number, the object returned by the DB will be empty
      if (
        Object.keys(busRoutes).length === 0 &&
        busRoutes.constructor === Object
      ) {
        // display error message if the object is empty
        document.getElementById("user-error-message").innerText =
          "Please enter a valid route number";
        return;
      }
      mapDirectionsStops = busRoutes;
      // when the user clicks on the "submit" button, draw the markers for the default selected direction
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
      displayAddToFavouritesButton();
      displayDirectionsButtons();
      injectDirectionNameInButtons();
      selectedDirection = directions[0];
    })
    .catch((error) => {
      console.log(error);
    });
}
