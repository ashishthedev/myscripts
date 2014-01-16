//A phantom script that will open the bluedart page for a particular
//docketNumber, click on the hyperlink which invokes xhr request and saves the
//final screenshot as a local file with .jpeg/pdf/png/gif extension
//
var page = require('webpage').create(),
    system = require('system'),
    fs = require('fs');

page.customHeaders = {
    "Content-Type" : "application/x-www-form-urlencoded",
    'Referer': 'http://www.bluedart.com/',
    'Origin': 'http://www.bluedart.com',
}
page.onConsoleMessage = function (msg) {
    console.log(msg);
};
var REQUEST_URL= "http://www.bluedart.com/servlet/RoutingServlet";
var destinationFile = system.args[1]
var docket = system.args[2]
var FORM_DATA="handler=tnt&action=awbquery&awb=awb&numbers=" + docket;

try {
    page.open(REQUEST_URL, 'POST', FORM_DATA, function (status) {

        if(status !== 'success') {
            console.log("Unable to access network - status: " + status);
            phantom.exit(1);
        }

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

