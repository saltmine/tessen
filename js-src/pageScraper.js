#!/usr/bin/env phantomjs
/**
 * Crawl some pages
 */

(function() {
  // Imports
  var page = require('webpage').create();
  var system = require('system');


  // Globals
  var result = {success: false, args: system.args};
  var url;


  // Runit
  if (system.args.length === 2){
    system.stderr.writeLine(system.args); // debug
    url = system.args[1];
  }


  function dumpResults(exitCode) {
    exitCode = typeof exitCode !== 'undefined' ? exitCode : 0;
    console.log(JSON.stringify(result, null, 4));
    phantom.exit(exitCode);
  }


  // Register document object listener
  page.onInitialized = function() {
    page.evaluate(function() {
      document.addEventListener('DOMContentLoaded', function() {
        window.callPhantom('DOMContentLoaded');
      }, false);
    });
  };


  page.onResourceReceived = function(request) {
    if (request.url === url) {
      result.status = request.status;
      if (request.status >= 300 && request.status < 400) {
        url = request.redirectURL;
        result.redirectURL = url;
        console.log('Redirect!!! New: ' + url);
      } else if (request.status < 200 || request.status >= 300) {
        // Fail here
        dumpResults(1);
      }
      // Sucess
      result.headers = request.headers;
    }
  };


  page.onCallback = function(data) {
    if (data === "DOMContentLoaded") {
      result.html = page.content;
      dumpResults();
    }
  };

  page.settings.resourceTimeout = 5000; // 5 seconds
  page.onResourceTimeout = function(r) {
    console.log(r);
    console.log("He's dead");
    phantom.exit(1);
  };

  page.open(url);
}());
