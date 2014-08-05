//A phantom script that will open the professional page for a particular
//docketNumber and saves the final screenshot as a local file
//with .jpeg/pdf/png/gif extension
//

var page = require('webpage').create(),
    system = require('system');

var destinationFile = system.args[1]
var docket = system.args[2]
var FORM_DATA = system.args[3]

var REQUEST_URL = system.args[4];

page.onConsoleMessage = function (msg) {
    console.log(msg);
};

page.customHeaders = {
    'Host':'www.tpcindia.com',
    'Referer': REQUEST_URL,
}
try {
    page.open(REQUEST_URL, 'POST', FORM_DATA, function (status) {
        if(status !== 'success') {
            console.log("Unable to access network - status: " + status);
            phantom.exit(1);
        }
        page.evaluate(function(){
            var el = document.getElementById('ctl00_ContentPlaceHolder1_Button8')
            var ev = document.createEvent("MouseEvents");
            ev.initEvent("click", true, true);
            el.dispatchEvent(ev);
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
