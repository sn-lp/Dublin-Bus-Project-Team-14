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
let suggestedRoutesData = { departureTime: "", routesData: [] };

// global variables that need to be accessed by independent functions
let travelTimeEstimations;
let suggestedRoutesElements;
let timeEstimationReplaced = false;

function initDirectionsService() {
  directionsService1 = new google.maps.DirectionsService();
}

function initDirectionsRenderer() {
  directionsRenderer1 = new google.maps.DirectionsRenderer();
}

//Make page title bold in navbar
document
  .getElementById("journeyplanner_nav")
  .setAttribute("style", "font-weight: bold;");

//Directions
function calculateAndDisplayRoute(directionsService, directionsRenderer) {
  if (
    (document.getElementById("origin").value = document.getElementById(
      "destination"
    ).value)
  ) {
    window.alert(
      "The starting location and the destination should be different!"
    );
    return;
  }

  document.getElementById("loading").style.display = "block";
  // hide over_map until we replaced the times in the suggested routes div
  document.getElementById("over_map").style.display = "none";

  departureTime = document.getElementById("departure-time").value;
  var unix_date = new Date();
  unix_date.setTime(Date.parse(departureTime));

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
      getRoutesTravelEstimationsFromModels(response, directionsRenderer);
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
      document.getElementById("loading").style.display = "none";
      // make window reload to prompt the user to enter a new origin/destination address if no bus connection could be found for the previous submission
      window.location.reload();
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
  // hide the suggested routes only until the time estimations have been replaced
  // otherwise because this is asynchronous the user could potentially see the times changing on the page
  if (!timeEstimationReplaced) {
    document.getElementById("directions_results").children[0].style.display =
      "none";
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
        // User rejected geolocation services.
        alert(
          "Error: Location services were rejected. Please allow location permissions in your browser to use this feature."
        );
      }
    );
  } else {
    // Browser doesn't support Geolocation.
    alert("Error: Browser does not support Location services.");
  }
});

// returns travel time estimation for all suggested routes that come in the google directions API
function getRoutesTravelEstimationsFromModels(
  directionsResponseObject,
  directionsRenderer
) {
  suggestedRoutesData.routesData = getRoutesDataFromDirectionsAPIResponse(
    directionsResponseObject
  );
  // get departure date and time selected by the user
  departureTime = document.getElementById("departure-time").value;
  suggestedRoutesData.departureTime = departureTime;

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
        // hide suggested routes div if server error occurs
        document.getElementById(
          "directions_results"
        ).children[0].style.display = "none";
        document.getElementById("user-error-message").style.display = "block";
        displayErrorMessageToUser();
        // status and statusText doesn't work for all browsers but works in Chrome and Safari
        throw new Error(response.status + ", " + response.statusText);
      }
    })
    .then((estimationsResponse) => {
      travelTimeEstimations = estimationsResponse;
      replaceTravelTimeEstimations(travelTimeEstimations);
      timeEstimationReplaced = true;
      document.getElementById("loading").style.display = "none";
      document.getElementById("directions_results").children[0].style.display =
        "block";
      document.getElementById("over_map").style.display = "block";
      // only draw the journey line on the map after we rendered the suggested routes div, otherwise this will be displayed before the user sees any suggested routes
      directionsRenderer.setMap(map);
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
  let journey_start_time = routeLegs.departure_time.value.toString();
  let start_time = { start_time: journey_start_time };
  routeData.push(start_time);
  routeSteps = routeLegs.steps;
  for (let i = 0; i < routeSteps.length; i++) {
    let routeStepsData = { step: {} };
    if (routeSteps[i].travel_mode == "WALKING") {
      const step_duration = routeSteps[i].duration.value;
      const travel_mode = "WALKING";
      routeStepsData.step = {
        step_duration: step_duration,
        travel_mode: travel_mode,
      };
    }
    if (routeSteps[i].travel_mode == "TRANSIT") {
      for (let j = 0; j < routeSteps[i].transit.line.agencies.length; j++) {
        if (routeSteps[i].transit.line.agencies[j].name != "Dublin Bus") {
          const step_duration = routeSteps[i].duration.value;
          const travel_mode = "TRANSIT";
          const provider = routeSteps[i].transit.line.agencies[j].name;
          const departure_time = routeSteps[
            i
          ].transit.departure_time.value.toString();
          routeStepsData.step = {
            step_duration: step_duration,
            travel_mode: travel_mode,
            provider: provider,
            departure_time: departure_time,
          };
        } else {
          const step_duration = routeSteps[i].duration.value;
          const travel_mode = "TRANSIT";
          const provider = routeSteps[i].transit.line.agencies[j].name;
          const bus_line_long_name = routeSteps[i].transit.line.name;
          const bus_line_short_name = routeSteps[i].transit.line.short_name;
          const headsign = routeSteps[i].transit.headsign;
          const departure_stop = routeSteps[i].transit.departure_stop.name;
          const arrival_stop = routeSteps[i].transit.arrival_stop.name;
          const departure_time = routeSteps[
            i
          ].transit.departure_time.value.toString();
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
            departure_time: departure_time,
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
  removeAppendedElements();
  // replace or hide steps' details of a selected route when user clicks on the "Route Details" button
  replaceOrHideStepTimes();
  displayCostCalculationInfo();
  document.getElementById("directions_results").children[0].style.display =
    "none";
  if (
    document.getElementById("directions_results").children[1].style.display ==
    "none"
  ) {
    document.getElementById("directions_results").children[1].style.display =
      "block";
  }
  document.getElementById("submit-selected-route").style.display = "none";
  document.getElementById("clear").style.display = "none";
  document.getElementById("back-to-routes").style.display = "block";
}

// changes window to display suggested routes again
function displaySuggestedRoutes() {
  // if a route's details triggered an error message, remove it when going back to suggested routes
  if (document.getElementById("user-error-message").style.display == "block") {
    document.getElementById("user-error-message").style.display = "none";
  }
  if (document.getElementById("info").style.display == "block") {
    document.getElementById("info").style.display = "none";
  }
  removeAppendedElements();
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

function replaceTravelTimeEstimations(travelTimeEstimations) {
  // try access all (nested) elements until we reach individual route elements that we can use to replace google's time estimations with ours
  // if the expected html elements don't exist, display an error message to the user
  try {
    if (!document.getElementById("directions_results")) {
      throw new Error(
        "Could not find 'directions_results' html child elements."
      );
    }
    const directionsResultsDiv = document.getElementById("directions_results");
    if (
      !directionsResultsDiv.hasChildNodes() ||
      directionsResultsDiv.children[0] == null
    ) {
      displayErrorMessageToUser();
      return;
    }
    const multipleRoutesDiv = directionsResultsDiv.children[0];
    if (
      !multipleRoutesDiv.hasChildNodes() ||
      multipleRoutesDiv.children[0] == null
    ) {
      displayErrorMessageToUser();
      return;
    }
    const routesSelectionDiv = multipleRoutesDiv.children[0];
    if (
      !routesSelectionDiv.childNodes.length > 1 ||
      routesSelectionDiv.children[1] == null
    ) {
      displayErrorMessageToUser();
      return;
    }
    const routeOptions = routesSelectionDiv.children[1];
    if (!routeOptions.hasChildNodes() || routeOptions.children[0] == null) {
      displayErrorMessageToUser();
      return;
    }
    if (!routeOptions.children[0].hasChildNodes()) {
      displayErrorMessageToUser();
      return;
    }
    // routesElements is a list of <li> elements injected in the "directions_results" div by calling "directionsRenderer.setPanel",
    // each <li> element corresponds to an individual suggested route
    const routesElements = routeOptions.children[0].children;
    suggestedRoutesElements = routesElements;
    // we can map the routes in the backend response object to the corresponding route that the directions api returns since they are in the same index order
    for (let i = 0; i < suggestedRoutesElements.length; i++) {
      routeEstimations = travelTimeEstimations[`route_${i}`];
      replaceRouteTravelTime(suggestedRoutesElements[i], routeEstimations);
    }
  } catch (error) {
    console.log(error);
  }
}
// receives a route i.e. <li> element and replaces the travel times for that route
function replaceRouteTravelTime(route, routeEstimations) {
  if (
    !route.hasChildNodes() ||
    !route.children[0].classList.contains("adp-summary-duration")
  ) {
    displayErrorMessageToUser();
    return;
  }
  const routeDurationDiv = route.children[0];
  routeDurationDiv.innerText = routeEstimations.route_duration;
  const routeInitalTime = route.children[2].children[0];
  routeInitalTime.innerText = routeEstimations.journey_starts;
  const routeEndTime = route.children[2].children[1];
  routeEndTime.innerText = routeEstimations.journey_ends;
}

function replaceOrHideStepTimes() {
  try {
    if (!document.getElementById("directions_results")) {
      throw new Error(
        "Could not find 'directions_results' html child elements."
      );
    }
    const directionsResultsDiv = document.getElementById("directions_results");
    if (
      !directionsResultsDiv.hasChildNodes() ||
      directionsResultsDiv.children[1] == null
    ) {
      displayErrorMessageToUser();
      return;
    }
    const detailsDiv = directionsResultsDiv.children[1];
    if (
      !detailsDiv.hasChildNodes() ||
      detailsDiv.children[0] == null ||
      !detailsDiv.children[0].hasChildNodes() ||
      detailsDiv.children[0].childNodes.length < 3
    ) {
      displayErrorMessageToUser();
      return;
    }
    const stepsDiv = detailsDiv.children[0].children[2];
    if (
      !stepsDiv.hasChildNodes() ||
      stepsDiv.childNodes.length < 3 ||
      stepsDiv.children[0] == null
    ) {
      displayErrorMessageToUser();
      return;
    }
    const routeSummaryDiv = stepsDiv.children[0];
    const stepDetailsDiv = stepsDiv.children[1];
    if (
      !routeSummaryDiv.hasChildNodes() ||
      routeSummaryDiv.childNodes.length < 3 ||
      !stepDetailsDiv.hasChildNodes() ||
      stepDetailsDiv.children[0] == null
    ) {
      displayErrorMessageToUser();
      return;
    }
    const journeyTimeDiv = routeSummaryDiv.children[2];
    const tableDetailsDiv = stepDetailsDiv.children[0];
    if (
      !journeyTimeDiv.hasChildNodes() ||
      !tableDetailsDiv.hasChildNodes() ||
      tableDetailsDiv.children[0] == null
    ) {
      displayErrorMessageToUser();
      return;
    }
    const timeDiv = journeyTimeDiv.children[0];
    const tableDetailsBodyDiv = tableDetailsDiv.children[0];
    selectedRouteIndex = getSelectedRouteIndex();
    timeDiv.innerText =
      travelTimeEstimations[`route_${selectedRouteIndex}`]["route_duration"];

    for (let i = 0; i < tableDetailsBodyDiv.children.length; i++) {
      tableRow = tableDetailsBodyDiv.children[i];

      // for now disable google infowindow display when clicking a step since the window will show google step times estimations that don't correspond to ours
      tableRow.setAttribute("jsaction", " ");

      if (!tableRow.hasChildNodes() || tableRow.children[0] == null) {
        displayErrorMessageToUser();
        return;
      }
      const subStep = tableRow.children[0];
      if (!subStep.hasChildNodes()) {
        displayErrorMessageToUser();
        return;
      }
      const stepEstimations = subStep.children[2];
      // when step is walk we don't want to change anything because google walk time estimation is the one we are using when a step is walking mode
      // google's stepEstimations html element has style display "none" when it is a walking step
      // so we only do display cost and plot when display style is "block" --> which means it is not a walking step
      if (stepEstimations.style.display != "none") {
        if (
          !stepEstimations.hasChildNodes() ||
          stepEstimations.children.length < 3
        ) {
          displayErrorMessageToUser();
          return;
        }
        const clockTimes = stepEstimations.children[0];
        const durationAndNumberOfStops = stepEstimations.children[1];
        // replace step time and number of stops details in "Route Details" view
        if (
          !travelTimeEstimations[`route_${selectedRouteIndex}`][`step_${i}`]
        ) {
          displayErrorMessageToUser();
          return;
        }
        step_start_time =
          travelTimeEstimations[`route_${selectedRouteIndex}`][`step_${i}`][
            "step_starts"
          ];
        step_end_time =
          travelTimeEstimations[`route_${selectedRouteIndex}`][`step_${i}`][
            "step_ends"
          ];
        step_number_of_stops =
          travelTimeEstimations[`route_${selectedRouteIndex}`][`step_${i}`][
            "number_of_stops"
          ];
        step_duration =
          travelTimeEstimations[`route_${selectedRouteIndex}`][`step_${i}`][
            "step_duration"
          ];
        clockTimes.innerText = `${step_start_time}-${step_end_time}`;
        // number of stops will always be 0 for walking steps and some bus providers
        if (step_number_of_stops == 0) {
          durationAndNumberOfStops.innerText = `     (${step_duration})`;
        } else if (step_duration == "") {
          durationAndNumberOfStops.innerText = `     (${step_number_of_stops} stops)`;
        } else {
          durationAndNumberOfStops.innerText = `     (${step_duration}, ${step_number_of_stops} stops)`;
        }

        stepCost =
          travelTimeEstimations[`route_${selectedRouteIndex}`][`step_${i}`][
            "step_cost"
          ];
        if (stepCost) {
          // display estimated step cost only for Dublin Bus steps, other steps will have stepCost to null
          displayStepCost(stepEstimations, stepCost);
        }
        // step_predicted_by_app will be true if it is a dubliin bus step predicted by the app
        // in which case we want to display the dot plot
        step_predicted_by_app =
          travelTimeEstimations[`route_${selectedRouteIndex}`][`step_${i}`][
            "predicted_by_app"
          ];
        if (step_predicted_by_app) {
          step_route_name =
            travelTimeEstimations[`route_${selectedRouteIndex}`][`step_${i}`][
              "route_name"
            ];
          step_prediction_in_seconds =
            travelTimeEstimations[`route_${selectedRouteIndex}`][`step_${i}`][
              "prediction_in_seconds"
            ];
          if (step_route_name && step_prediction_in_seconds) {
            let quantilePlotDiv = document.createElement("DIV");
            quantilePlotDiv.id = "quantile-dot-plot-div";
            subStep.insertBefore(quantilePlotDiv, subStep.previousSibling);
            let displayPlotButton = document.createElement("BUTTON");
            displayPlotButton.id = "quantile-dot-plot-button";
            displayPlotButton.innerText =
              "Show probabilistc travel time estimate";
            quantilePlotDiv.insertBefore(
              displayPlotButton,
              quantilePlotDiv.firstChild
            );
            document
              .getElementById("quantile-dot-plot-button")
              .classList.add("btn");
            document
              .getElementById("quantile-dot-plot-button")
              .classList.add("btn-primary");
            displayPlotButton.onclick = function () {
              QDP_request(
                `${step_route_name}`,
                `${step_prediction_in_seconds}`
              );
            };
          }
        }
      }
    }
  } catch (error) {
    console.log(error);
  }
}

function displayStepCost(stepEstimationsDiv, stepCost) {
  const node = document.createElement("SPAN");
  node.id = "estimated_step_cost";
  node.setAttribute("data-tooltip", "Adult fare paying with Leap Card.");
  node.setAttribute("data-tooltip-position", "right");
  node.innerText = `Estimated cost: ${stepCost}`;
  stepEstimationsDiv.parentNode.insertBefore(
    node,
    stepEstimationsDiv.nextSibling
  );
}

function displayCostCalculationInfo() {
  const info = document.createElement("div");
  info.id = "info";
  info.innerText =
    "Estimated costs for Dublin Bus are calculated using Transport for Ireland Bus Fares. The total cost of the journey may depend on other provider's fares.";
  const resultsDiv = document.getElementById("directions_results");
  resultsDiv.appendChild(info);
}

function getSelectedRouteIndex() {
  index = 0;
  suggestedRoutesElements.forEach((route) => {
    // the selected <li> element i.e. route, gets the class "adp-listsel" when selected
    if (route.classList.contains("adp-listsel")) {
      route_index = index;
    }
    index += 1;
  });
  return route_index;
}

function displayErrorMessageToUser() {
  // display error message to the user if the injected html elements expected from calling "directionsRenderer.setPanel" are not available
  if (
    document.getElementById("directions_results").children[1].style.display ==
    "block"
  ) {
    document.getElementById("directions_results").children[1].style.display =
      "none";
  }
  document.getElementById("user-error-message").style.display = "block";
  document.getElementById("user-error-message").innerText =
    "Sorry, something went wrong, please try again";
}

//Quantile Dot Plot Javascript function
function QDP_request(lineid, prediction) {
  endpoint =
    "/api/quantile_dotplot_generator/?line_id=" +
    lineid +
    "&prediction=" +
    prediction;
  plotDiv = document.getElementById("plot");
  if (!plotDiv) {
    //Fetch request to backend
    fetch(endpoint)
      .then((response) => response.json())
      .then((data) => {
        //base64 will hold the bytestream which contains the image data.
        base64 = data["image_base64"];
        displayDotPlot(base64);
      })
      .catch((error) => {
        console.log(error);
      });
  }
}

function displayDotPlot(dotPlotData) {
  // create new element to be parent of plot image and append to quantile-dot-plot-div created for each step
  let plotDiv = document.createElement("DIV");
  plotDiv.id = "plot";
  plotDiv.setAttribute("style", "height:400px");
  plotDiv.setAttribute(
    "style",
    "display:flex; flex-direction:column; overflow:scroll"
  );
  quantilePlotDiv = document.getElementById("quantile-dot-plot-div");
  quantilePlotDiv.insertBefore(plotDiv, quantilePlotDiv.nextSibling);
  // add img element as child to new element plotDiv and style display
  dot_plot_element = document.createElement("img");
  dot_plot_element.setAttribute("src", "data:image/png;base64," + dotPlotData);
  dot_plot_element.setAttribute(
    "alt",
    "This image shows the probabilities of your bus trip duration. Each dot represents a 5% chance of how long your trip will take. The red line represents the most likely time duration for your trip."
  );
  // add div with info explaining the plot interpretation
  let plotInfo = document.createElement("div");
  plotInfo.id = "plot-info";
  plotInfo.innerText =
    "This image shows the probabilities of your bus trip duration. Each dot represents a 5% chance of how long your trip will take. The red line represents the most likely time duration for your trip.";

  plotInfo.setAttribute("style", "max-width:100%; order:2");
  dot_plot_element.setAttribute("style", "width:100%; height:100%; order:1");
  dot_plot_div = document.getElementById("plot");
  dot_plot_div.appendChild(dot_plot_element);
  dot_plot_div.appendChild(plotInfo);

  // change button text
  plotButton = document.getElementById("quantile-dot-plot-button");
  plotButton.innerText = "Hide probabilist travel time estimate";
  plotButton.onclick = function () {
    hidePlot();
  };
}

function removeAppendedElements() {
  if (document.getElementById("estimated_step_cost")) {
    document.getElementById("estimated_step_cost").remove();
  }
  if (document.getElementById("quantile-dot-plot-div")) {
    document.getElementById("quantile-dot-plot-div").remove();
  }
  if (document.getElementById("info")) {
    document.getElementById("info").remove();
  }
}

function hidePlot() {
  plotDiv = document.getElementById("plot");
  plotDiv.style.display = "none";
  plotButton = document.getElementById("quantile-dot-plot-button");
  plotButton.innerText = "Show probabilistc travel time estimate";
  plotButton.onclick = function () {
    showPlot();
  };
}

function showPlot() {
  plotDiv = document.getElementById("plot");
  plotButton = document.getElementById("quantile-dot-plot-button");
  plotDiv.style.display = "block";
  plotButton.innerText = "Hide probabilist travel time estimate";
  plotButton.onclick = function () {
    hidePlot();
  };
}
