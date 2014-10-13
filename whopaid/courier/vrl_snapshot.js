//A phantom script that will open the vrl page for a particular
//docketNumber and saves the final screenshot as a local file
//with .jpeg/pdf/png/gif extension
//

//var page = require('webpage').create(),
//    system = require('system'),
//    fs = require('fs');

var page = require('webpage').create(),
    system = require('system');

page.customHeaders = {
  'Host': 'vrlgroup.in'
}
page.onConsoleMessage = function (msg) {
  console.log(msg);
};

var destinationFile = system.args[1];
var docket = system.args[2];
var REQUEST_URL = system.args[4];

try {
  page.open(REQUEST_URL, function (status) {

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
