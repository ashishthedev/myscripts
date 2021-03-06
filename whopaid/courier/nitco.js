//A phantom script that will open the nitco page for a particular
//docketNumber and saves the final screenshot as a local file
//with .jpeg/pdf/png/gif extension

var page = require('webpage').create(),
    system = require('system');

var destinationFile = system.args[1];
var docket = system.args[2];
var FORM_DATA = system.args[3];
var REQUEST_URL = system.args[4];

page.customHeaders = {
  'Host': '202.177.175.171',
  'Origin': 'http://202.177.175.171',
  "Content-Type" : "application/x-www-form-urlencoded",
  'Referer':  REQUEST_URL
}
page.onConsoleMessage = function (msg) {
  console.log(msg);
};


try {
  page.open(REQUEST_URL, 'POST', FORM_DATA, function (status) {

    if(status !== 'success') {
      console.log("Unable to access network - status: " + status);
      phantom.exit(1);
    }

    console.log("Saving Snapshot for docket: " + docket);
    window.setTimeout( function(){
      page.render(destinationFile);
      page.close();
      phantom.exit();
    }, 10000);
  });
}
catch(err)
{
  console.log("Error: " + err.messge);
  phantom.exit(1);
}
