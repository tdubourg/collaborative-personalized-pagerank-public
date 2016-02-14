"use strict"


var http = require('http')
var baseURL = "/scores"
var cpprHost = 'localhost'
var cpprPort = 4242

/**
 * @param uid{int} user id
 * @param gid{int} group id, or null if not group id
 * @param urls_ids{array} list of the URLs which we want the CPPR scores of
 * @param callback: the callback to be executed when data is returned
    callback: function (err{bool}, data{dict}) {}
*/
var retrieve_scores = function (uid, gid, url_ids, callback) {
    var result = {}
    var post_data = JSON.stringify({
        'uid': uid,
        'gid': gid,
        'url_ids': url_ids
    })
    var req = http.request({
        host: cpprHost, 
        path: baseURL,
        port: cpprPort,
        method: 'POST'
    }, function (resp) {
        var body = ""
        resp.on("data", function (chunk) {
            body += chunk
        });
        resp.on("error", function (err) {
            console.log('Unable to get CPPR score')
            callback(err, result)
        })
        resp.on("end", function () {
            // console.log("Text answer: ", body)
            callback(false, JSON.parse(body))
        })
    })

    req.on("error", function (err) {
        console.log('Unable to get CPPR scores')
        callback(err, result)
    })

    req.write(post_data)
    req.end()
}

var test = function () {
    retrieve_scores(1, null, [1, 2, 3, 4], function (e, d) {
        if (e) {
            console.error(":( ", e);
        } else { 
            console.log("ANSWER!!", d)
         }
    })
}

if (require.main === module) {
    test()
}

exports.retrieve_scores = retrieve_scores