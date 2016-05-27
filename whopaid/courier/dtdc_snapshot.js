//A phantom script that will open the overnite page for a particular
//docketNumber, click on the hyperlink which invokes xhr request and saves the
//final screenshot as a local file with .jpeg/pdf/png/gif extension
//
var page = require('webpage').create(),
    system = require('system'),
    fs = require('fs');

var destinationFile = system.args[1];
var docket = system.args[2];
var FORM_DATA = system.args[3];
var reqUrl = system.args[4];

page.viewportSize = { width: 1024, height: 768 };
page.customHeaders = {
    "Host": "dtdc.in",
    "Content-Type" : "application/x-www-form-urlencoded",
    'Referer': reqUrl,
    'Origin': 'http://dtdc.in',
}
page.onConsoleMessage = function (msg) {
    console.log(msg);
};
try {
  page.open(reqUrl, 'POST', FORM_DATA, function (status) {
    if(status !== 'success') {
      console.log("Unable to access network - status: " + status);
      phantom.exit(1);
    }

    page.evaluate(function(){
      var el = document.querySelector('#box-table-a > tbody > form').submit();
    });
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

