//Google Maps
let map;
const chicago = { lat: 41.85, lng: -87.65 };

function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 53.3498, lng: -6.2603 },
    zoom: 12,
    disableDefaultUI: true,
  });
}

const drawer = mdc.drawer.MDCDrawer.attachTo(
  document.querySelector(".mdc-drawer")
);
const topAppBar = mdc.topAppBar.MDCTopAppBar.attachTo(
  document.querySelector(".mdc-top-app-bar")
);
topAppBar.listen("MDCTopAppBar:nav", () => {
  drawer.open = !drawer.open;
});
