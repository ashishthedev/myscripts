//A phantom script that will open the firstflight page for a particular
//docketNumber and saves the final screenshot as a local file
//with .jpeg/pdf/png/gif extension
//

//var page = require('webpage').create(),
//    system = require('system'),
//    fs = require('fs');

var page = require('webpage').create(),
    system = require('system');

page.customHeaders = {
    'Host': 'www.firstflight.net',
}
page.onConsoleMessage = function (msg) {
    console.log(msg);
};
var destinationFile = system.args[1]
var docket = system.args[2]
var REQUEST_URL = "http://www.firstflight.net/n_contrac_new_12Digit_New.asp?tracking1=" + docket;

try {
    page.open(REQUEST_URL, function (status) {

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
