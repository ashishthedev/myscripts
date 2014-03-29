//A phantom script that will open the overnite page for a particular
//docketNumber, click on the hyperlink which invokes xhr request and saves the
//final screenshot as a local file with .jpeg/pdf/png/gif extension
//
var page = require('webpage').create(),
    system = require('system'),
    fs = require('fs');

page.customHeaders = {
    "Content-Type" : "application/x-www-form-urlencoded",
    'Referer': 'http://www.overnitenet.com/WebTrack.aspx',
    'Origin': 'http://www.overnitenet.com',
}
page.onConsoleMessage = function (msg) {
    console.log(msg);
};
var destinationFile = system.args[1]
var docket = system.args[2]
var FORM_DATA = system.args[3]


try {
    page.open("http://www.overnitenet.com/WebTrack.aspx", 'POST', FORM_DATA, function (status) {
        if(status !== 'success') {
            console.log("Unable to access network - status: " + status);
            phantom.exit(1);
        }

        page.evaluate(function(){
            var el = document.getElementById('ctl00_CntPlaceHolderDetails_GridViewOuter_ctl02_lnkbtnAwb');
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

