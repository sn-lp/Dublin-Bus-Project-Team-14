//Google Maps
let map;

function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 53.3498, lng: -6.2603 },
    zoom: 15,
    disableDefaultUI: true,
  });
}

function getAllBusStops() {
  busStopsEndpoint = "/api/get_all_bus_stops";

  fetch(busStopsEndpoint)
    .then((response) => {
      if (response.ok) {
        console.log(typeof (response.json));
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
            scaledSize: new google.maps.Size(50, 50),
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



    })
    .catch((error) => {
      console.log(error);
    });

}




getAllBusStops();