//Google Maps
let map;
const chicago = { lat: 41.85, lng: -87.65 };

function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 53.3498, lng: -6.2603 },
    zoom: 12,
    disableDefaultUI: true,
  });

  const journeyWindowDiv = document.createElement("div");
  journeyWindowDiv.id = "journeyWindowDiv";
  const journeyWindowDivContents = document.createElement("div");
  journeyWindowDivContents.id = "journeyWindowDivContents";
  journeyWindowDivContents.innerHTML = `<div class="input-group">
  <input type="search" class="form-control rounded" placeholder="Search" aria-label="Search"
    aria-describedby="search-addon" />
</div>
<button type="button" class="btn btn-primary" id="myLocationButton">My Location</button>
`;

  journeyWindowDiv.appendChild(journeyWindowDivContents);

  map.controls[google.maps.ControlPosition.LEFT_CENTER].push(journeyWindowDiv);
}
