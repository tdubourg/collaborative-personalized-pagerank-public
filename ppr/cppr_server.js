#!/usr/bin/env node
"use strict"

var http = require("http"),
    port = process.argv[2] || 4242;

http.createServer(function(req, resp) {
	var post_data = ""
	req.on("data", function (data) {
		post_data += data
	})
	req.on("end", function () {
		post_data = JSON.parse(post_data)
		console.log("Received data:")
		var resp_data = JSON.stringify({"status": "BLORG!!", "scores": [42, 43, 44, 24]})
		console.log("Answering:", resp_data)
		resp.end(resp_data)
	})
}).listen(parseInt(port, 10), "0.0.0.0");

console.log("CPPR Server running on http://0.0.0.0:" + port + "/\nCTRL + C to shutdown");

