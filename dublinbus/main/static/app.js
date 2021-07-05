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

//Setting datetime
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
  console.log(date_vars[i]);
}



//Navigation Drawer
const drawer = mdc.drawer.MDCDrawer.attachTo(
  document.querySelector(".mdc-drawer")
);
const topAppBar = mdc.topAppBar.MDCTopAppBar.attachTo(
  document.querySelector(".mdc-top-app-bar")
);
topAppBar.listen("MDCTopAppBar:nav", () => {
  drawer.open = !drawer.open;
});
