//A phantom script that will open the trackon page for a particular
//docketNumber and saves the final screenshot as a local file
//with .jpeg/pdf/png/gif extension
//
var page = require('webpage').create(),
    system = require('system'),
    fs = require('fs');

page.customHeaders = {
    "Content-Type" : "application/x-www-form-urlencoded",
    'Referer': 'http://trackoncourier.com/Default.aspx',
    'Origin': 'http://trackoncourier.com',
}
page.onConsoleMessage = function (msg) {
    console.log(msg);
};
var destinationFile = system.args[1]
var docket = system.args[2]
var FORM_DATA="__VIEWSTATE=%2FwEPDwUKMTM2ODMyNjQ5NA9kFgJmD2QWAgICD2QWCAIFDw8WAh4HVmlzaWJsZWhkZAIHDw8WAh8AaGRkAgkPDxYCHgRUZXh0ZWRkAgsPZBYEAgEPZBYCAgEPFgIeA3NyYwUafi9pbWFnZXMvdHJhY2tTaGlwbWVudC5qcGdkAgMPFgIeC18hSXRlbUNvdW50AgEWAgIBD2QWBGYPFQQJMzQ1MTM4MDAwCURFTElWRVJFRAswMSBKdWwgMjAxMw53aXRoIFNJR05BVFVSRWQCAQ8WAh8DAgMWBgIBD2QWAmYPFQYJR0hBWklBQkFEABFERUxISSBIRUFEIE9GRklDRQwxMDAzNDA5NDkxNDkKMjkvMDYvMjAxMwUxOTozOWQCAg9kFgJmDxUGCkRFTEhJIEguTy4AFVBBVEhBTktPVC0wMTg2MjIzNDM1MgwxMDAwMzA0MTIyMjAKMzAvMDYvMjAxMwUyMDowN2QCAw9kFgJmDxUGCVBBVEhBTktPVAAFICAtICABMAowMS8wNy8yMDEzBTE1OjA2ZBgBBR5fX0NvbnRyb2xzUmVxdWlyZVBvc3RCYWNrS2V5X18WAQUdY3RsMDAkTG9naW4yJGltZ3RyYWNrb25TdWJtaXRTjdVBMrmra84ziY%2F00Eqw1oHLhA%3D%3D&ctl00%24Login2%24txtUsername=&ctl00%24Login2%24txtPassword=&ctl00%24ContentPlaceHolder1%24Tracking1%24hidAWB=1" + docket + "&ctl00%24ContentPlaceHolder1%24Tracking1%24trackno=" + docket + "&ctl00%24ContentPlaceHolder1%24Tracking1%24trackonSubmit=&ctl00%24ContentPlaceHolder1%24Tracking1%24primetrackno=&__EVENTVALIDATION=%2FwEWCQLUq4iMCAK00vXCBwLx3cW8DwKtpJblAwL4ya2YBgK5jN%2BIBgL8nsXZCgLCs5bTDALIlpeaCdsVYmlvDIpNyXh9yAT0H9sQIYi4"

try {
    page.open("http://trackoncourier.com/TrackonConsignment.aspx", 'POST', FORM_DATA, function (status) {
        if (status !== 'success') {
            console.log("Unable to access network");
            phantom.exit(1);
        }

        console.log("Saving Snapshot for docket: " + docket);
        //Wait for 10 seconds and take a snapshot
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
