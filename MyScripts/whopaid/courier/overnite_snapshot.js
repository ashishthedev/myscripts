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
var FORM_DATA=" __EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE=%2FwEPDwUKLTEzMzczODYzNw9kFgJmD2QWAgIDD2QWAgIHD2QWBgIBD2QWAgIBD2QWBAIMD2QWAmYPZBYCAgEPPCsADQBkAhIPDxYCHgdWaXNpYmxlaGRkAgIPDxYCHgRUZXh0ZWRkAgMPDxYCHwFlZGQYAwUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFgEFJ2N0bDAwJENudFBsYWNlSG9sZGVyRGV0YWlscyRpbWdidG5UcmFjawUmY3RsMDAkQ250UGxhY2VIb2xkZXJEZXRhaWxzJE11bHRpVmlldzEPD2RmZAUpY3RsMDAkQ250UGxhY2VIb2xkZXJEZXRhaWxzJEdyaWRWaWV3T3V0ZXIPZ2SAkijFHV4KgROH1qrBTpCqvZmq3g%3D%3D&__EVENTVALIDATION=%2FwEWBwL%2BooGlCQL49YzrBwL59YzrBwL3mqaFCwLjvLD3DQLX57OEBgKA6qoFNsCA5ggSoenQgEGOxo3BYbrplIs%3D&ctl00%24CntPlaceHolderDetails%24rdbListTrackType=1&ctl00%24CntPlaceHolderDetails%24txtAWB="+docket+"&ctl00%24CntPlaceHolderDetails%24ValidatorCalloutExtender6_ClientState=&ctl00%24CntPlaceHolderDetails%24imgbtnTrack.x=24&ctl00%24CntPlaceHolderDetails%24imgbtnTrack.y=3";

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

