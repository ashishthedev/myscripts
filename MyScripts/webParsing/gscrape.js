var Gscrape = function(domain) {
    var domain = domain || 'com',
        searchURL = 'http://www.google.' + domain + '/search?q=',
        searchInProgress = false,
        cache = {
            error: '',
            success: true,
            pages: 0,
            urls: {}
        };
    var caughtURL = function(page) {
        return page.evaluate(function(){
            if (window.location.host.substring(0, 5) === 'sorry') {
                return window.location.href;
            } else {
                return false;
            }
        });
    };
    var search = function(address, callback) {

        ++cache.pages;
        var page = new WebPage();
        page.onConsoleMessage = function(message) {
            console.log(message);
        };
        page.onLoadFinished = function(status) {
            if (status === 'success' && caughtURL(page)) {
                cache.success = false;
                cache.error = 'Google has caught you! Check this url: ' + caughtURL(page);
                callback();
                return;
            }
            if (status !== 'success') {
                cache.success = false;
                cache.error = 'Failed to load address: ' + address;
                callback();
                return;
            }
            var next = page.evaluate(function(){
                var a = document.getElementById('pnnext');
                return a ? a.href : false;
            });
            var links = page.evaluate(function(){
                var a = document.querySelectorAll('a.l'),
                arr = [];

            for (var i = 0; i < a.length; i++)
                if (a[i].href) arr.push(a[i].href);

            return arr;
            });
            for (i in links) {
                cache.urls[links[i]] = null;
            };
            if (next) {
                // delay next search every 10 pages 20 seconds else 1 second.
                setTimeout(function(){
                    search(next, callback);
                }, cache.pages % 10 === 0 ? 20000 : 1000);

            } else {
                callback();
            }

        };
        page.open(address);
    };
    var api = {
        reset: function() {
                   cache.error = '';
                   cache.success = true;
                   cache.pages = 0;
                   cache.urls = [];
               },
        search: function(query, callback) {
                    if (searchInProgress) {
                        console.log('Another search in progress. Please wait for the current search to end!');
                        return false;
                    }
                    searchInProgress = true;
                    var startTime = Date.now();
                    search(searchURL + query, function(){
                        searchInProgress = false;
                        var results = {};
                        for (i in cache) {
                            if (i == 'urls') {
                                results.urls = [];
                                for (x in cache.urls) results.urls.push(x);
                            } else {
                                results[i] = cache[i];
                            }
                        }
                        callback(results, Date.now() - startTime);
                    });
                }
    };
    return api;
};

if (phantom.args.length < 1) {
    console.error('Usage: gscrape.js [domain] <query>');
    phantom.exit(1);
} else {
    var domain, query;
    if (phantom.args.length > 1) {
        domain = phantom.args[0];
        query = phantom.args[1]; }
    else {
        domain = 'com';
        query = phantom.args[0];
    }
    var gscrape = new Gscrape(domain);
    gscrape.search(query, function(result, time) {
        console.log();
        console.log('--------------------------------');
        console.log('Total pages scanned: ' + result.pages );
        console.log('Total urls found: ' + result.urls.length );
        console.log('Time taken: ' + (time / 1000) + ' seconds');
        console.log('--------------------------------');
        if (result.success) {
            for (i in result.urls) {
                console.log(result.urls[i]);
            }
        } else {
            console.log();
            console.log('Error!!');
            console.log(result.error);
            console.log('--------------------------------');
        }
        phantom.exit();
    });
}
