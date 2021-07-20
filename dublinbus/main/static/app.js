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

//Button to hide UI to just show map
const targetDiv = document.getElementById("over_map");
const toggleBtn = document.getElementById("map_toggle");

toggleBtn.onclick = function () {
  if (targetDiv.style.display !== "none") {
    targetDiv.style.display = "none";
  } else {
    targetDiv.style.display = "block";
  }
};


//Weather Widget
function getWeatherFromBackend() {
  weatherEndpoint = "/api/weather_widget";
  fetch(weatherEndpoint)
    .then((response) => {
      if (response.ok) {
        console.log(response);
        return response.json();
      }
    })
    .catch((error) => {
      console.log(error);
    });
}

getWeatherFromBackend()