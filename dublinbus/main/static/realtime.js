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
      for (const [stopName, coordinates] of Object.entries(busStopsResponse)) {
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
          stop_name_heading.innerText = contentString;
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

$.ajax({
  type: "GET",
  url: "https://arcane-woodland-84034.herokuapp.com/https://gtfsr.transportforireland.ie/v1/?format=json",

  // Request headers
  beforeSend: function(xhrObj) {
      xhrObj.setRequestHeader("x-api-key", "GTFSR_API_KEY");
      xhrObj.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
      },
  })
.done(function (data) {
  console.log(data);
})
.fail(function () {
  alert("Error: No Realtime Info could be retrieved.");
});

