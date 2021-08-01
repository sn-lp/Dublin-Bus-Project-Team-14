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
        let contentString = stopName + "|" + stop.id;
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
          console.log(contentString);
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


var parsedGTFSR;
var xmlhttp1 = new XMLHttpRequest();

xmlhttp1.onreadystatechange = function() {
    if (xmlhttp1.readyState == 4 && xmlhttp1.status == 200) { 
        parsedGTFSR = JSON.parse(xmlhttp1.responseText);
        console.log(parsedGTFSR['entity']);
    }
}

xmlhttp1.open("GET", "https://arcane-woodland-84034.herokuapp.com/https://gtfsr.transportforireland.ie/v1/?format=json", true);
xmlhttp1.setRequestHeader('Cache-Control', 'no-cache');
xmlhttp1.setRequestHeader('x-api-key', 'APIKEY');
xmlhttp1.send();

