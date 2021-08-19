//Fetch initial API response to create a cache.
fetch("/api/get_gtfsr_response");

//Google Maps
let map;

function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 53.3498, lng: -6.2603 },
    zoom: 12,
    disableDefaultUI: true,
  });
  infowindow = new google.maps.InfoWindow();
  if (infowindow) {
    infowindow.close();
  }
  //Gelocation button.
  const locationButton = document.createElement("button");
  locationButton.textContent = "My Location";
  locationButton.classList.add("btn");
  locationButton.classList.add("btn-primary");
  locationButton.setAttribute("id", "locationButton");
  locationButton.setAttribute("style", "margin-bottom: 2vh;");
  map.controls[google.maps.ControlPosition.BOTTOM_CENTER].push(locationButton);
  locationButton.addEventListener("click", () => {
    // Try HTML5 geolocation.
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const pos = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          };
          infowindow.setPosition(pos);
          infowindow.setContent("Your Location");
          infowindow.open(map);
          map.panTo(pos);
          map.setZoom(15);
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
}

//Make page title bold in navbar
document
  .getElementById("realtime_nav")
  .setAttribute("style", "font-weight: bold;");

const stop_name_heading = document.getElementById("stop_name_box");

function getAllBusStops() {
  busStopsEndpoint = "/api/get_all_bus_stops";

  fetch(busStopsEndpoint)
    .then((response) => {
      if (response.ok) {
        return response.json();
      }
    })
    .then((busStopsResponse) => {
      markers = [];
      for (const [stopName, stop] of Object.entries(busStopsResponse)) {
        // set the infoWindow content to contain the name of the bus stop
        let contentString = stopName;
        const newMarker = new google.maps.Marker({
          position: {
            lat: stop.latitude,
            lng: stop.longitude,
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
          stop_name_heading.innerText = contentString;
          realtime_fetch(stop.id);
        });
      }
      new MarkerClusterer(map, markers, {
        imagePath:
          "https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m",
      });
    })
    .catch((error) => {
      console.log("Error.");
    });
}

getAllBusStops();

//Realtime with GTFSR API and Backend
const bus_results_div = document.getElementById("realtime_buses");

function realtime_fetch(stop_id) {
  stopTimesEndpoint = "/api/get_bus_stop_times/?stop_id=" + stop_id;

  //Fetch request to backend
  fetch(stopTimesEndpoint)
    .then((response) => response.json())
    .then((data) => {
      //Returns a dictionary with all relevant GTFSR info for this stop.
      var gtfsr_dict = gtfsr_api_fetch(stop_id);
      //Sends frontend and backend data to be matched. Small delay of 200ms is needed here to allow gtfsr_dict to populate correctly.
      setTimeout(realtime, 200, data, gtfsr_dict);
    })
    .catch((error) => {
      console.log("Error: Realtime request failed.");
    });
}

//Returns a dictionary with all GTFSR data relevant to a given stop_id.
function gtfsr_api_fetch(stop_id) {
  endpoint = "/api/get_gtfsr_response";

  var gtfsr_dict = {};

  //Fetch request to backend
  fetch(endpoint)
    .then((response) => response.json())
    .then((data) => {
      parsedGTFSR = data;
      for (var i = 0; i < parsedGTFSR["entity"].length; i++) {
        try {
          var stop_time_update_object =
            parsedGTFSR["entity"][i]["trip_update"]["stop_time_update"];
          var trip_id = parsedGTFSR["entity"][i]["trip_update"]["trip"].trip_id;
          var bus_route = trip_id.split("-")[1];

          //For each stop_time_update from GTFSR.
          for (var x = 0; x < stop_time_update_object.length; x++) {
            var stop_id_response = stop_time_update_object[x].stop_id;
            var delay = stop_time_update_object[x].departure["delay"];

            if (stop_id_response == stop_id) {
              gtfsr_dict[trip_id] = {
                delay: delay,
                bus_route: bus_route,
              };
            }
          }
          // return gtfsr_dict;
        } catch (e) {
          //All errors are caught.
        }
      }
    })
    .catch((error) => {
      console.log("Error: Realtime request failed.");
    });

  return gtfsr_dict;
}

function realtime(backend_data, gtfsr_dict) {
  if (Object.keys(backend_data).length < 1) {
    document.getElementById(
      "realtime_buses"
    ).innerHTML = `<p class="font-weight-bold text-center">No buses were found within the next hour</p>`;
  } else {
    //Set results table as empty.
    document.getElementById("realtime_buses").innerHTML = `
  <table class="table" id="results_table">
    <thead>
      <tr>
        <th scope="col">Route</th>
        <th scope="col">ETA</th>
      </tr>
    </thead>
  <tbody id='results_rows'>`;

    // Loop through backend data.
    for (const [key, values] of Object.entries(backend_data)) {
      arrival_time = values.arrival_time;
      backend_trip_id = values.trip_id;
      bus_route = backend_trip_id.split("-")[1];

      //If there is a GTFSR dictionary entry for this trip_id, try to get the delay.
      try {
        var delay = gtfsr_dict[backend_trip_id]["delay"];
      } catch (err) {}

      if (typeof delay != "undefined") {
        var arrival_time = add_delay_to_eta(arrival_time, delay);
      }

      push_realtime_update(arrival_time, bus_route);
    }

    sortTable();
    make_table_data_readable();
  }
  hideFirstMenu();
  displayAddOrRemoveFavouritesButton(
    document.getElementById("stop_name_box").innerHTML
  );
}

//Function which handles the addition and subtraction of delays to buses via the API.
function add_delay_to_eta(eta, delay) {

  var dt = new Date(null);
  dt.setHours(eta.split(":")[0], eta.split(":")[1], eta.split(":")[2]);

  dt.setSeconds(dt.getSeconds() + delay);

  var dt_hour_string = dt.getHours();
  var dt_minutes_string = dt.getMinutes();
  var dt_seconds_string = dt.getSeconds();

  var dt_vars = [dt_hour_string, dt_minutes_string, dt_seconds_string];

  for (var i = 0; i < dt_vars.length; i++) {
    if (dt_vars[i] < 10) {
      dt_vars[i] = "0" + String(dt_vars[i]);
    } else {
      dt_vars[i] = String(dt_vars[i]);
    }
  }

  var dt_string = dt_vars[0] + ":" + dt_vars[1] + ":" + dt_vars[2];

  return dt_string;
}

//Pushes to the frontend a resulting bus and ETA.
function push_realtime_update(estimated_arrival, bus_route) {
  var row = document.createElement("tr");
  var bus_route_td = document.createElement("td");
  var eta_td = document.createElement("td");

  bus_route_td.innerHTML = bus_route;

  //Time
  var current_time = new Date();
  var eta = new Date(
    current_time.getFullYear(),
    current_time.getMonth(),
    current_time.getDate(),
    estimated_arrival.substring(0, 2),
    estimated_arrival.substring(3, 5),
    estimated_arrival.substring(6, 8)
  );

  var time_remaining = Math.floor(
    (Math.round(eta.getTime() / 1000) -
      Math.round(current_time.getTime() / 1000)) /
      60
  );

  if (time_remaining < 10) {
    time_remaining = "0" + time_remaining;
  }

  eta_td.innerHTML = time_remaining;

  row.appendChild(bus_route_td);
  row.appendChild(eta_td);

  document.getElementById("results_rows").appendChild(row);
}

//Helped by W3 schools 'How TO - Sort a Table' https://www.w3schools.com/howto/howto_js_sort_table.asp.
function sortTable() {
  var table, rows, switching, i, x, y, shouldSwitch;
  table = document.getElementById("results_table");
  switching = true;
  /* Make a loop that will continue until
  no switching has been done: */
  while (switching) {
    // Start by saying: no switching is done:
    switching = false;
    rows = table.rows;
    /* Loop through all table rows (except the
    first, which contains table headers): */
    for (i = 1; i < rows.length - 1; i++) {
      // Start by saying there should be no switching:
      shouldSwitch = false;
      /* Get the two elements you want to compare,
      one from current row and one from the next: */
      x = rows[i].getElementsByTagName("TD")[1];
      y = rows[i + 1].getElementsByTagName("TD")[1];
      // Check if the two rows should switch place:
      if (x.innerHTML > y.innerHTML) {
        // If so, mark as a switch and break the loop:
        shouldSwitch = true;
        break;
      }
    }
    if (shouldSwitch) {
      /* If a switch has been marked, make the switch
      and mark that a switch has been done: */
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
    }
  }
}

//Removes 0's where minutes are less than 10 for nicer display.
function make_table_data_readable() {
  table = document.getElementById("results_table");
  rows = table.rows;

  for (i = 1; i < rows.length; i++) {
    this_row = rows[i].getElementsByTagName("TD")[1];

    if (this_row.innerHTML < 10 && this_row.innerHTML > 0) {
      this_row.innerHTML = this_row.innerHTML.substring(1, 2);
      this_row.innerHTML += " mins";
    } else if (this_row.innerHTML == 0) {
      this_row.innerHTML = "NOW";
    } else {
      this_row.innerHTML += " mins";
    }
  }
}

window.onload = function afterWindowLoaded() {
  displayFavourites();
};

//AnYi's favourites function from routeviewer.js, modified for stops.
function displayFavourites() {
  // run this function, only if the browser supports localstorage
  if (typeof Storage !== "undefined") {
    if (localStorage.getItem("favourite_stops") == null) {
      return;
    }
    // display title
    var para = document.createElement("P");
    para.classList.add("font-weight-bold");
    para.classList.add("text-center");
    para.innerHTML = "Favourites";
    document.getElementById("favourites").appendChild(para);
    // display buttons
    let favourites_array = JSON.parse(localStorage.getItem("favourite_stops"));
    favourites_array.forEach(function (item, index, array) {
      // create div
      var favourites_div = document.createElement("DIV");
      favourites_div.classList.add("d-grid");
      favourites_div.classList.add("gap-2");
      // create button
      var btn = document.createElement("BUTTON");
      btn.setAttribute("class", "btn btn-primary");
      btn.setAttribute("type", "submit");
      btn.addEventListener("click", function () {
        call_realtime_by_stop_name(item);
      });
      btn.textContent = item;
      // append the button to the div, and append the div to the favourite section
      favourites_div.appendChild(btn);
      document.getElementById("favourites").appendChild(favourites_div);
    });
  }
}

function call_realtime_by_stop_name(stop_name) {
  busStopsEndpoint = "/api/get_all_bus_stops/?stop_name=" + stop_name;
  //Fetch request to backend
  fetch(busStopsEndpoint)
    .then((response) => response.json())
    .then((data) => {
      realtime_fetch(Object.entries(data)[0][1]["id"]);
      LatLng = {
        lat: Object.entries(data)[0][1]["latitude"],
        lng: Object.entries(data)[0][1]["longitude"],
      };
      map.panTo(LatLng);
      map.setZoom(20);
      stop_name_heading.innerText = stop_name;
    })
    .catch((error) => {
      console.log("Error: Request failed.");
    });
}

function call_realtime_from_search() {
  var stop_name = document.getElementById("bus-stop-input").value;
  call_realtime_by_stop_name(stop_name);
}

function addToLocalstorageByStopNum(stop_num) {
  // run this function, only if the browser supports localstorage
  if (typeof Storage !== "undefined") {
    // localstorage is empty, then initialise it
    if (localStorage.getItem("favourite_stops") == null) {
      let favourites_array = [stop_num];
      let favourites_str = JSON.stringify(favourites_array);
      localStorage.setItem("favourite_stops", favourites_str);

      // localstorage is not empty, then append new route to it
    } else {
      let favourites_array = JSON.parse(
        localStorage.getItem("favourite_stops")
      );
      // only append the new favourite routes, if it's not duplicated
      if (!favourites_array.includes(stop_num)) {
        favourites_array.push(stop_num);
        let favourites_str = JSON.stringify(favourites_array);
        localStorage.setItem("favourite_stops", favourites_str);
      }
    }
    displayAddOrRemoveFavouritesButton(stop_num);
  }
}

function removeFromLocalstorage(stopNumber) {
  // run this function, only if the browser supports localstorage
  if (typeof Storage !== "undefined") {
    // localstorage is null, then return
    if (localStorage.getItem("favourite_stops") == null) {
      return;
    }

    let favourites_array = JSON.parse(localStorage.getItem("favourite_stops"));
    // remove the stop from localstorage, if the stop exists in localstorage
    if (favourites_array.includes(stopNumber)) {
      favourites_array = favourites_array.filter(function (item) {
        return item !== stopNumber;
      });
      if (favourites_array.length == 0) {
        localStorage.removeItem("favourite_stops");
      } else {
        let favourites_str = JSON.stringify(favourites_array);
        localStorage.setItem("favourite_stops", favourites_str);
      }
    }
    // reload buttons
    displayAddOrRemoveFavouritesButton(stopNumber);
  }
}

function addToLocalstorage() {
  let stop_num = document.getElementById("stop_name_box").innerHTML;
  if (stop_num != "") {
    addToLocalstorageByStopNum(stop_num);
  }
}

function displayAddOrRemoveFavouritesButton(stopNumber) {
  // run this function, only if the browser supports localstorage
  if (typeof Storage !== "undefined") {
    // clear all
    document.getElementById("add-to-favourites").style.display = "none";
    document.getElementById("remove-from-favourites").style.display = "none";

    let favourites_array = [];

    // to avoid NullPointerException
    if (localStorage.getItem("favourite_stops")) {
      favourites_array = JSON.parse(localStorage.getItem("favourite_stops"));
    }

    // if localstorage doesn't contain the stop number, then display "add to favourite" button
    if (
      favourites_array.length == 0 ||
      !favourites_array.includes(stopNumber)
    ) {
      let btn = document.getElementById("add-to-favourites");
      btn.style.display = "block";
      btn.addEventListener("click", function () {
        addToLocalstorageByStopNum(stopNumber);
      });
      // else display "remove from favourite" button
    } else {
      document.getElementById("remove-from-favourites").style.display = "block";
      let btn = document.getElementById("remove-from-favourites");
      btn.addEventListener("click", function () {
        removeFromLocalstorage(stopNumber);
      });
    }
  }
}

function hideFirstMenu() {
  document.getElementById("favourites").style.display = "none";
  document.getElementById("searchStopUI").style.display = "none";
  document.getElementById("back-to-stops").style.display = "block";
}

function goToStopsPage() {
  window.location.reload();
}

//Autocomplete
new Autocomplete("#autocomplete", {
  search: (input) => {
    const url = `/api/autocomple_stop?insert=${input}`;
    return new Promise((resolve) => {
      fetch(url)
        .then((response) => response.json())
        .then((data) => {
          resolve(data.data);
        });
    });
  },
});
