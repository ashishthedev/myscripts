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
var FORM_DATA="__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE=%2FwEPDwUINjI1NjcyOTQPZBYCZg9kFgICAw9kFgICCQ9kFgYCAQ9kFgICAQ9kFgQCDA9kFgJmD2QWAgIBDzwrAA0AZAISDw8WAh4HVmlzaWJsZWhkZAICDw8WAh4EVGV4dGVkZAIDDw8WAh8BZWRkGAMFHl9fQ29udHJvbHNSZXF1aXJlUG9zdEJhY2tLZXlfXxYBBSdjdGwwMCRDbnRQbGFjZUhvbGRlckRldGFpbHMkaW1nYnRuVHJhY2sFJmN0bDAwJENudFBsYWNlSG9sZGVyRGV0YWlscyRNdWx0aVZpZXcxDw9kZmQFKWN0bDAwJENudFBsYWNlSG9sZGVyRGV0YWlscyRHcmlkVmlld091dGVyD2dkyjnzKNlK1F0lha2VPD203I0wnWY%3D&__EVENTVALIDATION=%2FwEWBwL5m5XfBgL49YzrBwL59YzrBwL3mqaFCwLjvLD3DQLX57OEBgKA6qoFptDBWKLK0LmchCP7GBi3QkiQbAA%3D&ctl00%24CntPlaceHolderDetails%24rdbListTrackType=1&ctl00%24CntPlaceHolderDetails%24txtAWB="+docket+"&ctl00%24CntPlaceHolderDetails%24ValidatorCalloutExtender6_ClientState=&ctl00%24CntPlaceHolderDetails%24imgbtnTrack.x=29&ctl00%24CntPlaceHolderDetails%24imgbtnTrack.y=7";


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

