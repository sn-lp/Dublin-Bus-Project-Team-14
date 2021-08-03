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

// variable that will hold the departure date and time the user selected
let departureTime;

// dict that will have info about departure time and every suggested route by the directions api to send to backend
let suggestedRoutesData = { departure_time: "", routesData: [] };

function initDirectionsService() {
  directionsService1 = new google.maps.DirectionsService();
}

function initDirectionsRenderer() {
  directionsRenderer1 = new google.maps.DirectionsRenderer();
}

//Directions
function calculateAndDisplayRoute(directionsService, directionsRenderer) {
  directionsRenderer.setMap(map);

  var user_departure_time = document.getElementById("departure-time").value;
  var unix_date = new Date();
  unix_date.setTime(Date.parse(user_departure_time));

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
        departureTime: unix_date,
      },
      provideRouteAlternatives: true,
    })
    .then((response) => {
      // check response status here, in case the api fails to give a response we can handle it
      if (response.status != "OK") {
        throw new Error("status: " + response.status);
      }
      directionsRenderer.setDirections(response);
      // add listener that calls directionsResultDivChanged() every time a new html element is added to the "directions_results" div
      // we need to catch when the directions steps' div is injected so we can hide it
      document
        .getElementById("directions_results")
        .addEventListener(
          "DOMSubtreeModified",
          directionsResultDivChanged,
          false
        );
      getRoutesTravelEstimationsFromModels(response);
      directionsRenderer.setPanel(
        document.getElementById("directions_results")
      );

      //Switching UI
      const searchUI = document.getElementById("searchUI");
      searchUI.style.display = "none";

      const resultsUI = document.getElementById("resultsUI");
      resultsUI.style.display = "block";

      if (
        document.getElementById("user-error-message").style.display == "block"
      ) {
        document.getElementById("user-error-message").style.display = "none";
      }

      if (
        document.getElementById("submit-selected-route").style.display == "none"
      ) {
        document.getElementById("submit-selected-route").style.display =
          "block";
      }
    })
    .catch((e) => {
      console.log(e);
      window.alert("No bus directions could be found");
    });
}

// hides the directions detailed steps from first window where the multiple routes are suggested
// we will display the detailed directions when user clicks the "route details" button
function directionsResultDivChanged() {
  if (
    !document.getElementById("directions_results").hasChildNodes() ||
    document.getElementById("directions_results").childNodes.length != 2
  ) {
    return;
  }
  document.getElementById("directions_results").children[1].style.display =
    "none";
}

//Clear the map
function clearDirections(directionsRenderer) {
  if (
    document.getElementById("directions_results").children[0].style.display ==
    "none"
  ) {
    document.getElementById("directions_results").children[0].style.display =
      "block";
  }
  directionsRenderer.set("directions", null);
  directionsRenderer.setPanel(document.getElementById("directions_results"));

  resultsUI.style.display = "none";
  searchUI.style.display = "block";
}

//Setting datetime in format YYYY-MM-DDTHH:MM
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

//Setting the datetime selector so that you can't select a time prior to the current time (on page load)
document.getElementById("departure-time").value = datetime_string;
document.getElementById("departure-time").min = datetime_string;

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

//Reverse geocoding
locationButton = document.getElementById("location_button");
originField = document.getElementById("origin");

function reverse_geocoder(latitude, longitude) {
  var xmlhttp1 = new XMLHttpRequest();
  var parsedResponse;

  xmlhttp1.onreadystatechange = function () {
    if (xmlhttp1.readyState == 4 && xmlhttp1.status == 200) {
      parsedResponse = JSON.parse(xmlhttp1.responseText);
      originField.value = parsedResponse["results"][0].formatted_address;
    }
  };
  xmlhttp1.open(
    "GET",
    "https://maps.googleapis.com/maps/api/geocode/json?latlng=" +
      latitude +
      "," +
      longitude +
      "&key=" +
      google_api_key,
    true
  );
  xmlhttp1.send();
}

//Geolocation
locationButton.addEventListener("click", () => {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const pos = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };
        reverse_geocoder(pos.lat, pos.lng);
      },
      () => {
        alert("Error: Location services were rejected.");
        locationButton.style.display = "none";
        setLocationPrefs(1);
      }
    );
  } else {
    // Browser doesn't support Geolocation
    alert("Error: Browser does not support Location services.");
    locationButton.style.display = "none";
    setLocationPrefs(1);
  }
});

//Local Storage for locations preference
function setLocationPrefs(num) {
  // run this function, only if the browser supports localstorage
  if (typeof Storage !== "undefined") {
    if (localStorage.getItem("locations_pref") == null) {
      localStorage.setItem("locations_pref", num);
    }
  }
}

function readLocationPrefs() {
  if (typeof Storage !== "undefined") {
    if (localStorage.getItem("locations_pref") == 1) {
      locationButton.style.display = "none";
    }
  }
}

readLocationPrefs();

// returns travel time estimation for all suggested routes that come in the google directions API
function getRoutesTravelEstimationsFromModels(directionsResponseObject) {
  suggestedRoutesData.routesData = getRoutesDataFromDirectionsAPIResponse(
    directionsResponseObject
  );
  // get departure date and time selected by the user
  departureTime = document.getElementById("departure-time").value;
  suggestedRoutesData.departure_time = departureTime;

  let travelTimeEstimationsEndpoint =
    "/api/get_journey_travel_time_estimation/";

  const request = new Request(travelTimeEstimationsEndpoint, {
    headers: {
      "X-CSRFToken": csrftoken,
      Accept: "application/json",
      "Content-Type": "application/json",
    },
  });
  fetch(request, {
    method: "POST",
    mode: "same-origin",
    body: JSON.stringify(suggestedRoutesData),
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      } else {
        document.getElementById("user-error-message").style.display = "block";
        document.getElementById("user-error-message").innerText =
          "Something went wrong, please try again.";
        // status and statusText doesn't work for all browsers but works in Chrome and Safari
        throw new Error(response.status + ", " + response.statusText);
      }
    })
    .then((travelTimeEstimations) => {
      //travelTimeEstimations will be the response sent by the backend with the travel time estimations for all suggested routes
    })
    .catch((error) => {
      console.log(error);
    });
}

// returns an array with routes data relevant to feed the models
function getRoutesDataFromDirectionsAPIResponse(directionsResponseObject) {
  if (
    !directionsResponseObject.routes ||
    directionsResponseObject.routes.length == 0
  ) {
    return;
  }
  let routesData = [];
  // for each suggested route get the steps data for it
  for (let i = 0; i < directionsResponseObject.routes.length; i++) {
    suggestedRoute = getRouteData(directionsResponseObject.routes[i]);
    routesData.push(suggestedRoute);
  }
  return routesData;
}

// returns an array with specific data for every step of a suggested route
// for every step, if it is not a "Dublin Bus" service we are saving the times that the google directions api provides for that step
// if the step is a "Dublin Bus" service we store the bus stops, bus name and number, and number of stops
function getRouteData(route) {
  if (!route.legs || route.legs.length == 0) {
    return {};
  }
  routeLegs = route.legs[0];
  if (!routeLegs.steps || routeLegs.steps.length == 0) {
    return {};
  }
  let routeData = [];
  routeSteps = routeLegs.steps;
  for (let i = 0; i < routeSteps.length; i++) {
    let routeStepsData = { step: {} };
    if (routeSteps[i].travel_mode == "WALKING") {
      const step_duration = routeSteps[i].duration.text;
      const travel_mode = "WALKING";
      routeStepsData.step = {
        step_duration: step_duration,
        travel_mode: travel_mode,
      };
    }
    if (routeSteps[i].travel_mode == "TRANSIT") {
      for (let j = 0; j < routeSteps[i].transit.line.agencies.length; j++) {
        if (routeSteps[i].transit.line.agencies[j].name != "Dublin Bus") {
          const step_duration = routeSteps[i].duration.text;
          const travel_mode = "TRANSIT";
          const provider = routeSteps[i].transit.line.agencies[j].name;
          routeStepsData.step = {
            step_duration: step_duration,
            travel_mode: travel_mode,
            provider: provider,
          };
        } else {
          const step_duration = routeSteps[i].duration.text;
          const travel_mode = "TRANSIT";
          const provider = routeSteps[i].transit.line.agencies[j].name;
          const bus_line_long_name = routeSteps[i].transit.line.name;
          const bus_line_short_name = routeSteps[i].transit.line.short_name;
          const headsign = routeSteps[i].transit.headsign;
          const departure_stop = routeSteps[i].transit.departure_stop.name;
          const arrival_stop = routeSteps[i].transit.arrival_stop.name;
          // getting the number of stops should be useful to display cost of Dublin Bus journey
          const number_of_stops = routeSteps[i].transit.num_stops;
          routeStepsData.step = {
            step_duration: step_duration,
            travel_mode: travel_mode,
            provider: provider,
            bus_line_long_name: bus_line_long_name,
            bus_line_short_name: bus_line_short_name,
            headsign: headsign,
            departure_stop: departure_stop,
            arrival_stop: arrival_stop,
            number_of_stops: number_of_stops,
          };
        }
      }
    }
    routeData.push(routeStepsData);
  }
  return routeData;
}

// displays detailed steps, for the selected route when the user clicks the "route details" button
function displayRouteDetails() {
  document.getElementById("directions_results").children[0].style.display =
    "none";
  document.getElementById("directions_results").children[1].style.display =
    "block";
  document.getElementById("submit-selected-route").style.display = "none";
  document.getElementById("clear").style.display = "none";
  document.getElementById("back-to-routes").style.display = "block";
}

// changes window to display suggested routes again
function displaySuggestedRoutes() {
  // change display style of divs injected in "directions_results" when
  // directionsRenderer.setPanel(document.getElementById("directions_results")) is called
  document.getElementById("directions_results").children[0].style.display =
    "block";
  document.getElementById("directions_results").children[1].style.display =
    "none";
  document.getElementById("submit-selected-route").style.display = "block";
  document.getElementById("clear").style.display = "block";
  document.getElementById("back-to-routes").style.display = "none";
}
