//A phantom script that will open the fedex page for a particular
//docketNumber and saves the final screenshot as a local file
//with .jpeg/pdf/png/gif extension
//

var page = require('webpage').create();
var system = require('system');

var lastReceived = new Date().getTime();
var requestCount = 0;
var responseCount = 0;
var requestIds = [];
var startTime = new Date().getTime();

page.onConsoleMessage = function (msg) {
  console.log(msg);
};

var destinationFile = system.args[1];
var docket = system.args[2];
var FORM_DATA = system.args[3];
var REQUEST_URL = system.args[4];
//page.viewportSize = { width: 640, height: 480 }; //TODO set the appropriate viewport
page.customHeaders = {
  "Host": "www.fedex.com",
  "Origin": "www.fedex.com",
  "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
};


page.onResourceReceived = function (response) {
  if(requestIds.indexOf(response.id) !== -1) {
    lastReceived = new Date().getTime();
    responseCount++;
    requestIds[requestIds.indexOf(response.id)] = null;
  }
};
page.onResourceRequested = function (request) {
  if(requestIds.indexOf(request.id) === -1) {
    requestIds.push(request.id);
    requestCount++;
  }
};

// Open the page
console.log("Phantom REQUEST_URL: ");
console.log(REQUEST_URL);
page.open(REQUEST_URL,  function () {});

function waitFor(testFx, onReady, timeOutMillis) {
  var maxtimeOutMillis = timeOutMillis ? timeOutMillis : 3000, //< Default Max Timout is 3s
      start = new Date().getTime(),
      condition = false,
      interval = setInterval(function() {
        if ( (new Date().getTime() - start < maxtimeOutMillis) && !condition ) {
          // If not time-out yet and condition not yet fulfilled
          condition = (typeof(testFx) === "string" ? eval(testFx) : testFx()); //< defensive code
        } else {
          if(!condition) {
            // If condition still not fulfilled (timeout but condition is 'false')
            console.log("'waitFor()' timeout");
            phantom.exit(1);
          } else {
            // Condition fulfilled (timeout and/or condition is 'true')
            console.log("'waitFor()' finished in " + (new Date().getTime() - start) + "ms.");
            typeof(onReady) === "string" ? eval(onReady) : onReady(); //< Do what it's supposed to do once the condition is fulfilled
            clearInterval(interval); //< Stop this interval
          }
        }
      }, 250); //< repeat check every 250ms
};


var checkComplete = function () {
  // We don't allow it to take longer than 30 seconds but
  // don't return until all requests are finished
  //console.log("Requested = " + requestCount + " Received = " + responseCount + "Pending = " + (requestCount - responseCount));
  if((new Date().getTime() - lastReceived > 300 && requestCount === responseCount) || new Date().getTime() - startTime > 30000)  {
    clearInterval(checkCompleteInterval);
    window.setTimeout( function(){
      console.log("Phantom| Setting viewport_______________________________________________________________");
      page.viewportSize = { width: 1024, height: 768 }; //TODO set the appropriate viewport
      page.render(destinationFile);
      window.setTimeout( function(){
        console.log("Phantom| Inside TImeout after rendering_______________________________________________________________");
      }, 10000);
      console.log("Phantom| Page closed_______________________________________________________________");
      page.close();
      phantom.exit();
    }, 40000);
  }
}

// Let us check to see if the page is finished rendering
var checkCompleteInterval = setInterval(checkComplete, 1);



//___________________________________________________________
//var page = require('webpage').create(),
//    system = require('system');
//
//page.onConsoleMessage = function (msg) {
//  console.log(msg);
//};
//
//var destinationFile = system.args[1];
//var docket = system.args[2];
//var FORM_DATA = system.args[3];
//var REQUEST_URL = system.args[4];
////page.viewportSize = { width: 640, height: 480 }; //TODO set the appropriate viewport
//page.customHeaders = {
//  "Host": "www.fedex.com",
//  "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
//};
//
//
//try {
//  console.log("Phantom| Opening Fedex page for docket: " + docket);
//  console.log("Phantom| RequestURL:\n " + REQUEST_URL);
//
//  //page.open(REQUEST_URL);
//  //page.onLoadFinished = function() {
//  //  page.render(destinationFile);
//  //  page.close();
//  //  phantom.exit();
//  //}
//
//  page.open(REQUEST_URL, 'GET', FORM_DATA, function (status) {
//    console.log("Phantom| Page openend");
//
//    if(status !== 'success') {
//      console.log("Phantom| Unable to access network - status: " + status);
//      phantom.exit(1);
//    }
//
//    console.log("Phantom| Saving Snapshot for docket: " + docket);
//    console.log("Phantom| waiting for 20 secs");
//    window.setTimeout( function(){
//      page.render(destinationFile);
//      page.close();
//      console.log("Phantom| wait over");
//      phantom.exit();
//    }, 30000);
//  });
//}
//catch(err)
//{
//  console.log("Outer Error: " + err.messge);
//  console.log("Error: " + err.messge);
//  phantom.exit(1);
//}
