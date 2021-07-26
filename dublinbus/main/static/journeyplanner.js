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
  fetch(travelTimeEstimationsEndpoint, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(suggestedRoutesData),
  })
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

function displayRouteDetails() {
  // this function will be implemented in another ticket/PR to display the details, including detailed steps, for the route
  // when the user clicks the "route details" button
  return;
}
