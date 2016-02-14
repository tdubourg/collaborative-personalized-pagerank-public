"use strict"

var server = require('./server')

var host = process.argv[2] || "0.0.0.0";
var port = process.argv[3] || 8080;

console.log("Starting server on", host + ":" + port)

server.start(host, port)