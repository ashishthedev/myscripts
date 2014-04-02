//A phantom script that will open the professional page for a particular
//docketNumber and saves the final screenshot as a local file
//with .jpeg/pdf/png/gif extension
//

var page = require('webpage').create(),
    system = require('system');

var destinationFile = system.args[1]
var docket = system.args[2]
var REQUEST_URL = "http://www.tpcindia.com/Tracking2014.aspx?id=" + docket + "&type=0&service=0";
var FORM_DATA = "__EVENTTARGET=&__EVENTARGUMENT=&__LASTFOCUS=&__VIEWSTATE=%2FwEPDwUJLTExMjYyNTgyD2QWAmYPZBYCAgMPZBYCAgMPZBYCZg9kFgQCAQ9kFgQCAQ9kFgICAQ8PFgIeBFRleHQFbU5EQTMyOTAwNjQgaXMgZGVsaXZlcmVkIGF0IENIRU5OQUkgb24gVHVlc2RheSwgQXByaWwgMDEsIDIwMTQgYXQgMTA6MjU6MDEgYW5kIGlzIGFja25vd2xlZGdlZCAgd2l0aCBTSUdOQVRVUkVkZAIDD2QWAgIBD2QWAmYPZBYCZg9kFgICAQ9kFgRmD2QWAmYPZBYCAgEPDxYCHgdWaXNpYmxlaGRkAhQPZBYCZg9kFgICAQ9kFgICAQ88KwANAGQCCQ8QZGQWAWZkGAEFI2N0bDAwJENvbnRlbnRQbGFjZUhvbGRlcjEkR3JpZFZpZXcxD2dkvI3%2B0yVBkELD093UcWgPtRjDd90%3D&__EVENTVALIDATION=%2FwEWEQLbk%2B3yCgKJ4sljAojiyWMCt961iQEC4%2Fe37Q0C6Lzuuw4C0%2BDW%2FwQC4%2FzBxQ4C7eHz9wkCsejxlA0C54zy4QQCpMCk%2BQQCt97BiQEC5fe37Q0C0sXRsQQC2dPevgsC5Pe37Q1CL3YzvC4Odo6F28Ab%2FwIdNONsAg%3D%3D&ctl00%24ContentPlaceHolder1%24Button8=View+all+details&ctl00%24TextBox2=&textfield2=&ctl00%24rdbService=Domestic%C2%A0%C2%A0%C2%A0%C2%A0&ctl00%24rdbTrack=C%2Fn+No.+%C2%A0%C2%A0&ctl00%24TextBox1=&ctl00%24txt_uid=&ctl00%24txt_pwd=";

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
