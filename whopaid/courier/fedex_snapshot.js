//A phantom script that will open the fedex page for a particular
//docketNumber and saves the final screenshot as a local file
//with .jpeg/pdf/png/gif extension
//

var page = require('webpage').create(),
    system = require('system');

page.onConsoleMessage = function (msg) {
  console.log(msg);
};

var destinationFile = system.args[1];
var docket = system.args[2];
var FORM_DATA = system.args[3];
var REQUEST_URL = system.args[4];
//
page.customHeaders = {
  "Host": "www.fedex.com",
  "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
};


try {
  console.log("Phantom| Opening Fedex page for docket: " + docket);
  console.log("Phantom| RequestURL:\n " + REQUEST_URL);

  page.onInitialized = function(){
    page.evaluate(function(){
      var isFunction = function(o) {
        return typeof o == 'function';
      };

      var bind,
      slice = [].slice,
      proto = Function.prototype,
      featureMap;

    featureMap = {
      'function-bind': 'bind'
    };

    function has(feature) {
      var prop = featureMap[feature];
      return isFunction(proto[prop]);
    }

    // check for missing features
    if (!has('function-bind')) {
      // adapted from Mozilla Developer Network example at
      // https://developer.mozilla.org/en/JavaScript/Reference/Global_Objects/Function/bind
      bind = function bind(obj) {
        var args = slice.call(arguments, 1),
            self = this,
            nop = function() {
            },
            bound = function() {
              return self.apply(this instanceof nop ? this : (obj || {}), args.concat(slice.call(arguments)));
            };
        nop.prototype = this.prototype || {}; // Firefox cries sometimes if prototype is undefined
        bound.prototype = new nop();
        return bound;
      };
      proto.bind = bind;
    }
    });
  }

  page.open(REQUEST_URL, 'GET', FORM_DATA, function (status) {
    console.log("Phantom| Page openend");

    if(status !== 'success') {
      console.log("Phantom| Unable to access network - status: " + status);
      phantom.exit(status);
    }

    console.log("Phantom| Saving Snapshot for docket: " + docket);
    window.setTimeout( function(){
      page.render(destinationFile);
      page.close();
      phantom.exit();
    }, 10000);

  });
}
catch(err)
{
  console.log("Outer Error: " + err.messge);
  console.log("Error: " + err.messge);
  phantom.exit(1);
}
