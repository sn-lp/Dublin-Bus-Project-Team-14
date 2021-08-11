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

window.onload = function afterWindowLoaded() {
  displayFavourites();
};

//Make page title bold in navbar
document.getElementById("routes_nav").setAttribute("style", "font-weight: bold;");

function displayFavourites() {
  // run this function, only if the browser supports localstorage
  if (typeof Storage !== "undefined") {
    if (localStorage.getItem("favourite_routes") == null) {
      return;
    }
    // display title
    var para = document.createElement("P");
    para.classList.add("font-weight-bold");
    para.classList.add("text-center");
    para.innerHTML = "Favourites";
    document.getElementById("favourites").appendChild(para);
    // display buttons
    let favourites_array = JSON.parse(localStorage.getItem("favourite_routes"));
    favourites_array.forEach(function (item, index, array) {
      // create div
      var route_div = document.createElement("DIV");
      route_div.classList.add("d-grid");
      route_div.classList.add("gap-2");
      // create button
      var btn = document.createElement("BUTTON");
      btn.setAttribute("class", "btn btn-primary");
      btn.setAttribute("type", "submit");
      btn.addEventListener("click", function () {
        getBusStopsByBusNum(item);
      });
      btn.textContent = item;
      // append the button to the div, and append the div to the favourite section
      route_div.appendChild(btn);
      document.getElementById("favourites").appendChild(route_div);
    });
  }
}

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

function hideFavourites() {
  document.getElementById("favourites").style.display = "none";
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

function displayAddOrRemoveFavouritesButton(routeNumber) {
  // run this function, only if the browser supports localstorage
  if (typeof Storage !== "undefined") {
    // clear all
    document.getElementById("add-to-favourites").style.display = "none";
    document.getElementById("remove-from-favourites").style.display = "none";

    let favourites_array = [];

    // to avoid NullPointerException
    if (localStorage.getItem("favourite_routes")) {
      favourites_array = JSON.parse(localStorage.getItem("favourite_routes"));
    }

    // if localstorage doesn't contain the route number, then display "add to favourite" button
    if (
      favourites_array.length == 0 ||
      !favourites_array.includes(routeNumber)
    ) {
      let btn = document.getElementById("add-to-favourites");
      btn.style.display = "block";
      btn.addEventListener("click", function () {
        addToLocalstorageByRouteNum(routeNumber);
      });
      // else display "remove from favourite" button
    } else {
      document.getElementById("remove-from-favourites").style.display = "block";
      let btn = document.getElementById("remove-from-favourites");
      btn.addEventListener("click", function () {
        removeFromLocalstorage(routeNumber);
      });
    }
  }
}

function goToRoutesPage() {
  window.location.reload();
}

function addToLocalstorage() {
  let route_num = document.getElementById("bus-route-input").value;
  if (route_num != "") {
    addToLocalstorageByRouteNum(route_num);
  }
}

function addToLocalstorageByRouteNum(route_num) {
  // run this function, only if the browser supports localstorage
  if (typeof Storage !== "undefined") {
    // localstorage is empty, then initialise it
    if (localStorage.getItem("favourite_routes") == null) {
      let favourites_array = [route_num];
      let favourites_str = JSON.stringify(favourites_array);
      localStorage.setItem("favourite_routes", favourites_str);

      // localstorage is not empty, then append new route to it
    } else {
      let favourites_array = JSON.parse(
        localStorage.getItem("favourite_routes")
      );
      // only append the new favourite routes, if it's not duplicated
      if (!favourites_array.includes(route_num)) {
        favourites_array.push(route_num);
        let favourites_str = JSON.stringify(favourites_array);
        localStorage.setItem("favourite_routes", favourites_str);
      }
    }
    displayAddOrRemoveFavouritesButton(route_num);
  }
}

function removeFromLocalstorage(routeNumber) {
  // run this function, only if the browser supports localstorage
  if (typeof Storage !== "undefined") {
    // localstorage is null, then return
    if (localStorage.getItem("favourite_routes") == null) {
      return;
    }

    let favourites_array = JSON.parse(localStorage.getItem("favourite_routes"));
    // remove the route from localstorage, if the route exists in localstorage
    if (favourites_array.includes(routeNumber)) {
      favourites_array = favourites_array.filter(function (item) {
        return item !== routeNumber;
      });
      if (favourites_array.length == 0) {
        localStorage.removeItem("favourite_routes");
      } else {
        let favourites_str = JSON.stringify(favourites_array);
        localStorage.setItem("favourite_routes", favourites_str);
      }
    }
    // reload buttons
    displayAddOrRemoveFavouritesButton(routeNumber);
  }
}

// KYLE COMMENTED OUT FOR NOW - I THINK THIS MAKES THE UI LESS USABLE
// function resetMapPositionAndZoom() {
//   map.setZoom(defaultMapZoomLevel);
//   map.setCenter(
//     new google.maps.LatLng(defaultMapPositionLat, defaultMapPositionLong)
//   );
// }

function changeDirection(directionNumber) {
  // resetMapPositionAndZoom();
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
      icon: {
        url: "http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png",
        scaledSize: new google.maps.Size(40, 40),
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
  routeName = document.getElementById("bus-route-input").value;
  routeNumber = routeName.split(" ")[0];
  document.getElementById("bus-route-input").value = routeNumber;
  getBusStopsByBusNum(routeNumber);
}

function getBusStopsByBusNum(routeNumber) {
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
        document.getElementById("user-error-message").style.display = "block";
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
      hideFavourites();
      displayBackToRoutesButton();
      displayAddOrRemoveFavouritesButton(routeNumber);
      displayDirectionsButtons();
      injectDirectionNameInButtons();
      selectedDirection = directions[0];
    })
    .catch((error) => {
      console.log(error);
    });
}

// Autocomplete
new Autocomplete("#autocomplete", {
  search: (input) => {
    const url = `/api/autocomple_route?insert=${input}`;
    return new Promise((resolve) => {
      fetch(url)
        .then((response) => response.json())
        .then((data) => {
          resolve(data.data);
        });
    });
  },
});
