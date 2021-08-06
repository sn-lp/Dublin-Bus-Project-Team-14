//Google Maps
let map;

function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 53.3498, lng: -6.2603 },
    zoom: 15,
    disableDefaultUI: true,
  });
  infowindow = new google.maps.InfoWindow();
  if (infowindow) {
    infowindow.close();
  }
}

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
          get_realtime(stop.id);
        });
      }
      new MarkerClusterer(map, markers, {
        imagePath:
          "https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m",
      });
    })
    .catch((error) => {
      console.log(error);
    });
}

getAllBusStops();

//Return time to the second at function run.
function get_time() {
  var current_time = new Date();
  var hour = current_time.getHours();
  var minute = current_time.getMinutes();
  var second = current_time.getSeconds();

  const date_vars = [hour, minute, second];

  for (var i = 0; i < date_vars.length; i++) {
    if (date_vars[i] < 10) {
      date_vars[i] = "0" + String(date_vars[i]);
    } else {
      date_vars[i] = String(date_vars[i]);
    }
  }

  var time = date_vars[0] + ":" + date_vars[1] + ":" + date_vars[2];

  return time;
}

//Realtime with GTFSR API and Backend
const bus_results_div = document.getElementById("realtime_buses");

function get_realtime(stop_id) {
  stopTimesEndpoint = "/api/get_bus_stop_times/?stop_id=" + stop_id;

  //Fetch request to backend
  fetch(stopTimesEndpoint)
    .then((response) => response.json())
    .then((data) => {
      GTFSR_matching(data);
    })
    .catch((error) => {
      console.log(error);
    });
}

function GTFSR_matching(backend_data) {
  //Set results table as empty.
  document.getElementById("realtime_buses").innerHTML = `
  <table class="table" id="results_table">
    <thead>
      <tr>
        <th scope="col">Route</th>
        <th scope="col">ETA (mins)</th>
      </tr>
    </thead>
  <tbody id='results_rows'>`;

  // Loop through backend data.
  for (const [key, values] of Object.entries(backend_data)) {
    backend_arrival_time = values.arrival_time;
    backend_trip_id = values.trip_id;
    bus_route = backend_trip_id.split("-")[1];

    push_realtime_update(backend_arrival_time, bus_route);
  }
  sortTable();
  make_table_data_readable();
}

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
