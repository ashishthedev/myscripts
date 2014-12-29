//A phantom script that will open the trackon page for a particular
//docketNumber and saves the final screenshot as a local file
//with .jpeg/pdf/png/gif extension
//
var page = require('webpage').create(),
    system = require('system'),
    fs = require('fs');

page.customHeaders = {
    "Content-Type" : "application/x-www-form-urlencoded",
    'Referer': 'http://trackoncourier.com/Default.aspx',
    'Origin': 'http://trackoncourier.com',
}

page.onConsoleMessage = function (msg) {
    console.log(msg);
};

var destinationFile = system.args[1]
var docket = system.args[2]
var FORM_DATA = system.args[3]
var reqUrl = system.args[4]

try {
  page.open(reqUrl, 'POST', FORM_DATA, function (status) {
    if (status !== 'success') {
      console.log("Unable to access network");
      phantom.exit(1);
    }

    console.log("Saving Snapshot for docket: " + docket);
    //Wait for 10 seconds and take a snapshot
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
