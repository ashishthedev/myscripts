//A phantom script that will open the firstflight page for a particular
//docketNumber and saves the final screenshot as a local file
//with .jpeg/pdf/png/gif extension
//

var page = require('webpage').create(),
    system = require('system');

page.onConsoleMessage = function (msg) {
  console.log(msg);
};

var destinationFile = system.args[1];
var docket = system.args[2];
var FORM_DATA = system.args[3];
var REQUEST_URL = system.args[4];
page.viewportSize = { width: 640, height: 480 };
page.customHeaders = {
    "Host": "firstflight.net:8081",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": REQUEST_URL,
    "Origin": "http://firstflight.net:8081",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
    };


try {
  console.log("Phantom| Opening First Flight page for docket: " + docket);
  page.open(REQUEST_URL, 'POST', FORM_DATA, function (status) {
    console.log("Phantom| Page openend");

    if(status !== 'success') {
      console.log("Phantom| Unable to access network - status: " + status);
      phantom.exit(1);
    }

    console.log("Phantom| Saving Snapshot for docket: " + docket);
    window.setTimeout( function(){
      page.render(destinationFile);
      page.close();
      phantom.exit();
    }, 10000);
  });
}
catch(err)
{
  console.log("Outer Error: " + err.messge);
  console.log("Error: " + err.messge);
  phantom.exit(1);
}
