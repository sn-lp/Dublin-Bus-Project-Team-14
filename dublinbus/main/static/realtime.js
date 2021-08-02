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

const bus_results_div = document.getElementById("realtime_buses");

function get_realtime(stop_id) {
  stopTimesEndpoint = "/api/get_bus_stop_times/?stop_id=" + stop_id;

  console.log(stopTimesEndpoint);

  fetch(stopTimesEndpoint)
    .then((response) => {
      if (response.ok) {
        console.log(response.json());
      }
    })
    .then((stopTimesEndpoint) => {
    });
    

  var parsedGTFSR;
  var xmlhttp1 = new XMLHttpRequest();

  xmlhttp1.onreadystatechange = function () {
    if (xmlhttp1.readyState == 4 && xmlhttp1.status == 200) {
      parsedGTFSR = JSON.parse(xmlhttp1.responseText);

      for (var i = 0; i < parsedGTFSR["entity"].length; i++) {
        try {
          var stop_time_update_object =
          parsedGTFSR["entity"][i]["trip_update"]["stop_time_update"];
          var trip_id = parsedGTFSR["entity"][i]["trip_update"]["trip"].trip_id;
          var bus_route = trip_id.split('-')[1];

          for (var x = 0; x < stop_time_update_object.length; x++) {
            var stop_id_response = stop_time_update_object[x].stop_id;
            var delay = stop_time_update_object[x].departure["delay"];
            if (stop_id_response == stop_id) {
              console.log("STOP ID | " + stop_id_response);
              console.log("DELAY | " + delay);
              console.log("TRIP | " + trip_id);
              console.log("ROUTE | " + bus_route);
            }
          }
        } catch (e) {
          //All error are caught. Must be mroe careful with this - come back to.
        }
      }
    }
  };

  xmlhttp1.open(
    "GET",
    "https://arcane-woodland-84034.herokuapp.com/https://gtfsr.transportforireland.ie/v1/?format=json",
    true
  );
  xmlhttp1.setRequestHeader("Cache-Control", "no-cache");
  xmlhttp1.setRequestHeader("x-api-key", "APIKEY");
  xmlhttp1.send();
}
