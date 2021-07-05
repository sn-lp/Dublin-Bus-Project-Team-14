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

var datetime_string = date_vars[0] + "-" + date_vars[1] + "-" + date_vars[2] + "T" + date_vars[3] + ":" + date_vars[4];

document.getElementById("departure-time").value = datetime_string;
document.getElementById("departure-time").min = datetime_string;