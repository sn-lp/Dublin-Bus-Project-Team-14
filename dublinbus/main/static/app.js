// initialise map button tooltip
const mapToggle = document.getElementById("map_toggle");
const tooltip = new mdb.Tooltip(mapToggle);

displayMapButtonTooltip(tooltip);

// display the tooltip only the first time the user opens the app in one browser
function displayMapButtonTooltip(mapButtonTooltip) {
  if (typeof Storage !== "undefined") {
    if (localStorage.getItem("map_tooltip_displayed") == null) {
      tooltip.show();
      // display toggle map button for 4 seconds and then hide it
      setTimeout(function () {
        mapButtonTooltip.hide();
      }, 4000);
      localStorage.setItem("map_tooltip_displayed", true);
    }
  }
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

//Button to hide UI to just show map
const targetDiv = document.getElementById("over_map");
const toggleBtn = document.getElementById("map_toggle");

toggleBtn.onclick = function () {
  if (targetDiv.style.display !== "none") {
    targetDiv.style.display = "none";
    toggleBtn.style.backgroundColor = "#ffcc00";
  } else {
    targetDiv.style.display = "block";
    toggleBtn.style.backgroundColor = "";
  }
};

//Weather Widget
function getWeatherFromBackend() {
  weatherEndpoint = "/api/weather_widget";
  fetch(weatherEndpoint)
    .then((response) => {
      if (response.ok) {
        return response.json();
      }
    })
    .then((weatherDict) => {
      const weather_icon_id = weatherDict["_Weather__weather_icon"];
      const weather_temperature =
        Math.round(weatherDict["_Weather__temp"]) + "° C";

      var weather_widget_image = document.createElement("img");
      weather_widget_image.setAttribute(
        "src",
        "http://openweathermap.org/img/wn/" + weather_icon_id + "@2x.png"
      );
      weather_widget_image.setAttribute("alt", "weather widget");
      document
        .getElementById("weather_widget_top")
        .appendChild(weather_widget_image);

      var weather_widget_temperature = document.createElement("h5");
      weather_widget_temperature.innerText = weather_temperature;
      weather_widget_temperature.id = "temperature";
      weather_widget_temperature.setAttribute("aria-labelledby", "temperature");
      document
        .getElementById("weather_widget_top")
        .appendChild(weather_widget_temperature);
    })
    .catch((error) => {
      console.log(error);
    });
}

getWeatherFromBackend();
