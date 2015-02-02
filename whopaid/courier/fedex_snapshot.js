//A phantom script that will open the fedex page for a particular
//docketNumber and saves the final screenshot as a local file
//with .jpeg/pdf/png/gif extension
//

var system = require('system');

var destinationFile = system.args[1];
var docket = system.args[2];
var FORM_DATA = system.args[3];
var REQUEST_URL = system.args[4];




function renderPage(url, formData) {
  var page = require('webpage').create();
  var redirectURL = null;

page.onConsoleMessage = function (msg) {
  console.log(msg);
};


  page.customHeaders = {
    "Host": "www.fedex.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
  };

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

  page.onResourceReceived = function(resource) {
    if (url == resource.url && resource.redirectURL) {
      redirectURL = resource.redirectURL;
    }
  };

  page.open(REQUEST_URL, function (status) {
    console.log("Phantom| Page opened");
    if (redirectURL) {
      console.log("Phantom| Redirection detected");
      renderPage(redirectURL, formData);
    } else if (status == 'success') {
      console.log("Phantom| Saving Snapshot for docket: " + docket);
      window.setTimeout( function(){
        page.render(destinationFile);
        page.close();
        phantom.exit();
      }, 20000);

    } else {
      if(status !== 'success') {
        console.log("Phantom| Unable to access network - status: " + status);
        phantom.exit(status);
      }
    }
  });
}

//


try {
  console.log("Phantom| destinationFile: " + destinationFile);
  console.log("Phantom| docket:          " + docket);
  console.log("Phantom| FORM_DATA:       " + FORM_DATA);
  console.log("Phantom| RequestURL:      " + REQUEST_URL);
  renderPage(REQUEST_URL, FORM_DATA);

}
catch(err)
{
  console.log("Outer Error: " + err.messge);
  console.log("Error: " + err.messge);
  phantom.exit(1);
}

