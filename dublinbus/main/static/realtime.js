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
        let contentString = stopName + stop.id;
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
  var backend_dict = {};

  //Populate the Backend Dictionary.
  for (var i = 0; i < Object.keys(backend_data).length; i++) {
    key = Object.keys(backend_data)[i];
    backend_trip_id = backend_data[key]['trip_id'];
    backend_arrival_time = backend_data[key]['arrival_time'];

    backend_dict[backend_trip_id] = {
      "arrival_time": backend_arrival_time,
    }
  }

  console.log("BACKEND DICTIONARY");
  console.log(backend_dict);

}


function push_realtime_update(estimated_arrival, bus_route) {
  var card = document.createElement("div");
  card.setAttribute("class", "card-body");

  var bus_route_text = document.createElement("p");
  bus_route_text.setAttribute("class", "card-text");
  bus_route_text.innerText = bus_route;

  var eta_text = document.createElement("p");
  eta_text.setAttribute("class", "card-text");
  eta_text.innerText = estimated_arrival;

  card.appendChild(bus_route_text);
  card.appendChild(eta_text);

  document.getElementById("realtime_buses").appendChild(card);
}