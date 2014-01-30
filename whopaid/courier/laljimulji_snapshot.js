//A phantom script that will open the lalji mulji page for a particular
//docketNumber and saves the final screenshot as a local file
//with .jpeg/pdf/png/gif extension
//

var page = require('webpage').create(),
    system = require('system'),
    fs = require('fs');

page.customHeaders = {
    'Host': 'lmtco.com',
    'Cookie' : '__utma=224089990.452415162.1391067021.1391067021.1391067021.1; __utmc=224089990; __utmz=224089990.1391067021.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)',
};
page.onConsoleMessage = function (msg) {
    console.log(msg);
};
var destinationFile = system.args[1]
var docket = system.args[2]


try {
    page.open("http://lmtco.com/", function (status) {
        if(status !== 'success') {
            console.log("Unable to access network - status: " + status);
            console.log(status);
            phantom.exit(1);
        }
        page.customHeaders = {
            'Referer': 'http://lmtco.com/',
        'Host': 'lmterp.com',
        'JSESSIONID' : 'AAABC21CA9AE706377FCC12D81C9AA10',
        };

        page.evaluate(function(docket){
            console.log("Searching for docket: " + docket);
            document.querySelector('input[name=FieldData]').value = docket;
            document.querySelector('input[name=sameButton]').click()
        }, docket);
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

