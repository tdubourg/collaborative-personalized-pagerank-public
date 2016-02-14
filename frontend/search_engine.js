"use strict"

var elasticsearch = require('elasticsearch');
var fs = require('fs')
var cst = require('./constants')
var es_host = fs.readFileSync('conf/es_host.conf').toString().replace('\n', '')
var es_index_name = fs.readFileSync('conf/es_index.conf').toString().replace('\n', '')

console.log("Loaded ES host:", es_host)
console.log("Loaded ES index:", es_index_name)

var client = null

var connect = function () {
    client = elasticsearch.Client({
        host: es_host
    });
}

/**
 * @param query_string{string} The query string to search for in the documents
 * @param results_number{integer} Positive integer: The number of top hits to return
 * @param callback: function (err, data) {}
 * with data =
    [
        ['id': url_id{int}, 'score': score{float}],
        ['id': url_id{int}, 'score': score{float}],
        ...
    ]
*/
function retrieve (query_string, results_number, callback) {
    if (!client) {
        connect()
    };

    var s = client.search({
        index: es_index_name,
        size: results_number,
        body: {
            fields: ['_id', '_score', 'url', 'title', 'content'],
            query: {
                match: {
                    content: query_string
                }
            }
        }
    }).then(function (resp) {
        // console.log(resp.hits.hits)
        var data = resp.hits.hits.map(function (hit) {
            // Just want to say: wtf do we have to do toString() to get a string as a string... Java programmers...
            return {
                'id': hit._id,
                'score': hit._score,
                'snippet': hit.fields.content.toString().substr(0, cst.SNIPPET_SIZE),
                'url': hit.fields.url.toString(),
                'title': hit.fields.title.toString()
            }
        })
        callback(false, data)
    }, function (err) {
        callback(err, {})
    });
}

var test = function () {
    retrieve(
        "best online bank",
        10,
        function (err, data) {
            if (err) {
                console.error("Error happened:", err)
                console.trace()
            } else {
                console.log("Retrieved data:", data)
            }
        }
    )
}

if (require.main === module) {
    test()
}

exports.retrieve = retrieve