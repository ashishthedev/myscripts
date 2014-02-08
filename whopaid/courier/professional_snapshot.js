//A phantom script that will open the professional page for a particular
//docketNumber and saves the final screenshot as a local file
//with .jpeg/pdf/png/gif extension
//

var page = require('webpage').create(),
    system = require('system');

var destinationFile = system.args[1]
var docket = system.args[2]
var REQUEST_URL = "http://www.tpcindia.com/Tracking.aspx?id=" + docket + "&type=0";
var FORM_DATA="__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE=%2FwEPDwUKLTM3NDUzMjIyNg9kFgJmD2QWAgIDD2QWAgIDD2QWAmYPZBYCAgEPZBYEAgEPZBYCAgEPDxYCHgRUZXh0BShUaGUgc3RhdHVzIGZvciBOREEzMjkwMDQ2IGlzIG9uIHRyYW5zaXQuZGQCAw9kFgICAQ9kFgJmD2QWAmYPZBYCAgEPZBYEZg9kFgJmD2QWAgIBDw8WAh4HVmlzaWJsZWhkZAIUD2QWAmYPZBYCAgEPZBYCAgEPPCsADQBkGAEFI2N0bDAwJENvbnRlbnRQbGFjZUhvbGRlcjEkR3JpZFZpZXcxD2dk%2BuWMXCDls2KmgtMV5KYg9keKshc%3D&__EVENTVALIDATION=%2FwEWDQKsksTXBAKJ4sljAojiyWMCt961iQEC4%2Fe37Q0CjeS4ngYC54zy4QQCpMCk%2BQQCt97BiQEC5fe37Q0C0sXRsQQC2dPevgsC5Pe37Q0H4BnviAbBN2o62NwnXXWsKdqfvw%3D%3D&ctl00%24ContentPlaceHolder1%24Button8=View+all+details&ctl00%24TextBox2=&textfield2=&ctl00%24rdbTrack=C%2Fn+No.&ctl00%24TextBox1=&ctl00%24txt_uid=&ctl00%24txt_pwd=";

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
