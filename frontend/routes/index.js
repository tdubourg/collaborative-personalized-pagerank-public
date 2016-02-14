'use strict';

var DOMAINS_LIMIT_PER_SERP = 2;

var express = require('express');
var router = express.Router();
var cst = require('../constants')
var se = require('../search_engine')
var shuffle = require('../shuffle').shuffle
var fs = require('fs')

var MongoClient = require('mongodb').MongoClient;
var mdb_host = fs.readFileSync('./conf/mdb_host.conf', 'utf8').replace("\n", "")

var TOP_N_RESULTS = 10

var DB_NAME = "user_study"
var SERP_COLLECTION_NAME = "serps"
var SERP_COLLECTION_NAME2 = "serps_tests"

var mdb = null
var serps_collection = null
var serps_collection_test = null
// Connect to the db
MongoClient.connect("mongodb://" + mdb_host + "/" + DB_NAME + "/", function(err, db) {
  if(!err) {
    console.log("We are connected");
    mdb = db
    serps_collection_test = db.collection(SERP_COLLECTION_NAME);
    serps_collection = db.collection(SERP_COLLECTION_NAME2);
  }
});

function do_borda_count (hits, req) {
    if (req.query.borda != "yes") {
        console.log("No borda!")
        return hits
    };
    console.log("Executing Borda Count!")
    var hits_es = hits.slice(0)
    var hits_pr = hits.slice(0)
    hits_es.sort(function (a, b) {
        return (a['score_es'] > b['score_es']) ? -1 : 1;
    })
    hits_es.sort(function (a, b) {
        return (a['score_pr'] > b['score_pr']) ? -1 : 1;
    })
    return borda_count(hits_es, hits_pr)
}

function borda_count (r1, r2) {
    var votes = {}
    for (var i = 0; i < r1.length; i++) {
        votes[r1[i]['url']] = r1.length - i;
    };

    for (var i = 0; i < r2.length; i++) {
        votes[r2[i]['url']] += r2.length - i;
    };

    var merged = r1.slice(0) // array copy
    merged.sort(function (item1, item2) {
        return ( votes[item1['url']] > votes[item2['url']] ) ? -1 : 1; // stupid JS, "-1" means "comes first"
    })
    console.log("Borda count finished")
    return merged
}

// A mapping uid, gid, query => result
// in order to speed up pages reloads...
// the cache can be bypassed by using the parameter ?nocache !!!! @TODO cache always disabled !!!!
var cache = {}

var add_to_cache = function (uid, gid, qid, hits) {
    if (!(uid in cache)) {
        cache[uid] = {}
    };

    if (!(gid in cache[uid])) {
        cache[uid][gid] = {}
    };

    cache[uid][gid][qid] = {
        'time': Date.now(),
        'hits': hits
    }
}

var cleanup_cache = function () {
    var time_limit = Date.now() - 1000*cst.CACHE_TIMEOUT_IN_SEC
    for(var uid in cache) {
        var cuid = cache[uid]
        for(var gid in cuid) {
            var cuidgid = cuid[gid]
            for(var qid in cuidgid) {
                var entry = cuidgid[qid]
                if (entry.time < time_limit) {
                    cuidgid[qid] = null // GC
                };
            }
        }
    }
}

var load_page_info = function (page_number) {
    page_number = parseInt(page_number)
    var path = './pages/' + page_number + '.txt'
    try {
        var content = fs.readFileSync(path).toString()
        var qid = parseInt(content.substring(0, content.indexOf('\n')))
        var text = content.substring(content.indexOf('\n'))
    } catch(e) {
        console.error("Error while loading page info file:", e)
        var qid = -1
        var text = 'Error'
    }

    return {'qid': qid, 'context': text}

}

var extract_domain = function (url) {
    var pattern="://"
    var domain = url.substring(url.indexOf(pattern)+pattern.length)
    domain = domain.substring(0, domain.indexOf("/"))
    // console.log("domain of", url, "is", domain)
    return domain
}

var set_relevance = function (resultEntry, pageData, algorithm) {
    if (pageData && pageData[algorithm][resultEntry.url]) {
        resultEntry.relevant = 'relevant'
    } else {
        resultEntry.relevant = undefined // in case the cache keeps previous data
    }
}

var set_best_algorithm = function (data, pageData, left_algorithm, right_algorithm) {
    var bestAlgorithmClassName = 'relevant'

    if (! pageData || !pageData.best) return

    if (pageData.best === left_algorithm) {
        data.serp_left_relevant =  bestAlgorithmClassName
    }
    if (pageData.best === right_algorithm) {
        data.serp_right_relevant = bestAlgorithmClassName
    }
}

var compute_nav_data = function (data, page_idx) {
    data.nav = data.nav || {}
    data.nav.prev_href = (page_idx - 1) >= 0 ? '?page=' + (page_idx - 1) : '#'
    data.nav.next_href = '?page=' + (page_idx + 1)

    console.log('nav data:', data.nav);
}

// Execute the cleanup every tenth of the cache timeout value
// setInterval(cleanup_cache, cst.CACHE_TIMEOUT_IN_SEC*1000/10)


var response_with_data = function (data, res, page_index, content_page) {
    if (cst.THANK_MESSAGES[page_index]) {
        data['thank_message'] = cst.THANK_MESSAGES[page_index].replace("\n", "<br />")
    } else {
        data['thank_message'] = ""
    }

    compute_nav_data(data, page_index)

    res.render(content_page, data, function (err, html) {
        data['content_page'] = html;
        res.render('index', data);
    })
}

/* GET home page. */
router.get('/', function(req, res) {

    // @TODO CHANGE THAT
    var qid = parseInt(req.query.query) || null
    var uid = req.query.uid || -1
    var gid = req.query.gid || -1
    if (typeof req.query.page == 'object') {
        req.query.page = req.query.page[req.query.page.length-1]
    };
    var page_index = Math.abs(req.query.page) || 0
    console.log('"page" get parameter is:', req.query.page)
    console.log('"page" get parameter is:', typeof req.query.page)

    var nocache = true /*'nocache' in req.query*/ // @TODO
    console.log("Cache disabled:", nocache)

    var existingPageData = req.session.pages[page_index]

    var data = {'serp_right_results': [], 'serp_left_results': []}
    var serp_standard = null,
        serp_perso = null
    if (Math.random() > 0.5) {
        serp_standard = data.serp_right_results
        data.serp_right_algorithm = 'standard'

        serp_perso = data.serp_left_results
        data.serp_left_algorithm = 'cppr'

    } else {
        serp_standard = data.serp_left_results
        data.serp_left_algorithm = 'standard'

        serp_perso = data.serp_right_results
        data.serp_right_algorithm = 'cppr'
    }

    set_best_algorithm(
        data,
        existingPageData,
        data.serp_left_algorithm,
        data.serp_right_algorithm)

    // Retrieve the original, non-modified results
    var callback = function (err, hits) {
        if (err) {
            console.error("Error happened:", err)
            console.trace()
        } else {
            var domain_limit = DOMAINS_LIMIT_PER_SERP
            if (typeof req.query.limit != 'undefined') {
                domain_limit = parseInt(req.query.limit)
            }
            // console.log("Received", hits.length, "results")
            console.log("Received results")
            add_to_cache(uid, gid, qid, hits)
            data['query_string'] = hits['query_string']
            var perso_reranked = do_borda_count(hits['perso'], req)
            var already_seen_domains = {'lol': -1}
            for (var i = 0; serp_perso.length < TOP_N_RESULTS && i < perso_reranked.length; i++) {
                var hit = perso_reranked[i]
                var domain = extract_domain(hit.url)
                if (typeof already_seen_domains[domain] != 'undefined') {
                    already_seen_domains[domain] += 1
                } else {
                    already_seen_domains[domain] = 1
                }
                if (already_seen_domains[domain] >= domain_limit) {
                    console.log("alredy seen too much time, skipping")
                    continue;
                };
                if (hit.title.length > cst.TITLE_LENGTH) {
                    hit.title = hit.title.substr(0, cst.TITLE_LENGTH) + '...'
                };
                if (hit.snippet.length > cst.SNIPPET_LENGTH) {
                    hit.snippet = hit.snippet.substr(0, cst.SNIPPET_LENGTH) + '...'
                };

                hit.index = serp_perso.length + 1;
                set_relevance(hit, existingPageData, 'cppr');

                serp_perso.push(hit)
            };
            var noperso_reranked = do_borda_count(hits['noperso'], req)
            already_seen_domains = {'lol': -1}
            for (var i = 0; serp_standard.length < TOP_N_RESULTS && i < noperso_reranked.length; i++) {
                var hit = noperso_reranked[i]
                var domain = extract_domain(hit.url)

                if (typeof already_seen_domains[domain] != 'undefined') {
                    already_seen_domains[domain] += 1
                } else {
                    already_seen_domains[domain] = 1
                }

                if (already_seen_domains[domain] >= domain_limit) {
                    console.log("alredy seen too much time, skipping")
                    continue;
                };
                if (hit.title.length > cst.TITLE_LENGTH) {
                    hit.title = hit.title.substr(0, cst.TITLE_LENGTH) + '...'
                };
                if (hit.snippet.length > cst.SNIPPET_LENGTH) {
                    hit.snippet = hit.snippet.substr(0, cst.SNIPPET_LENGTH) + '...'
                };

                hit.index = serp_standard.length + 1;
                set_relevance(hit, existingPageData, 'standard');

                serp_standard.push(hit)
            };
        }

        // shuffle(serp2)

        var content_page = 'user_study_content_page'
        data['user_study'] = true

        response_with_data(data, res, page_index, content_page)

    }; // end of callback

    if (page_index > cst.SURVEY_PAGE_COUNT) {
        var content_page = 'hooray'
        data['user_study'] = false
        response_with_data(data, res, page_index, content_page)
    } else {

        var cache_hit = null
        if (!nocache) {
            try {
                cache_hit = cache[uid][gid][qid]
            } catch (e) {
                // There's only one line in the try{}, the only catchable exception is about key not in the dict
                // and in this case the exact thing we want to do is... NOTHING!
                // so, as a consequence, this is a catchall and empty!
            }
        }
        if (cache_hit) {
            console.log("Cache hit")
            callback(false, cache_hit.hits)
        } else {
            console.log("Cache miss")
            // se.retrieve(qid, cst.SERP_RESULTS_NUMBER, callback)
            var pageinfo = load_page_info(page_index)
            data['pageinfo_context'] = pageinfo['context']
            var query_id = pageinfo['qid']
            if (qid !== null) {
                query_id = qid
            } else {
                qid = query_id  // so that if this global is used somewhere else, at least it is holding the right value now...
            }
            var serp = req.query.test == "test" ? serps_collection_test : serps_collection;

            serp.findOne({'_id': query_id}/*).toArray(*/, function(err, result) {
                if (err) {
                    console.error("THINGS SUCK!")
                    console.error(err)
                    return
                } else {
                    // console.log(result)
                    if (!result || (typeof result.length != 'undefined' && result.length == 0)) {
                        console.log("No results returned")
                        return
                    };
                }
                console.log("Received results.")
                var process = function (item) {
                    // Just want to say: wtf do we have to do toString() to get a string as a string... Java programmers...
                    return {
                        'id': item.urlid,
                        'score': item.score,
                        'snippet': (item.desc.toString() != ""  ? item.desc.toString().substr(0, cst.SNIPPET_SIZE) : "No descriptions provided."),
                        'url': item.url.toString(),
                        'url_display': item.url.toString().length > cst.MAX_LENGTH_URL_DISP ? item.url.toString().substring(0, cst.MAX_LENGTH_URL_DISP) + "..." : item.url.toString(),
                        'title': item.title.toString(),
                        'score_es': parseFloat(item['score_es']),
                        'score_pr': (typeof item['score_ppr'] != 'undefined') ? parseFloat(item['score_ppr']) : parseFloat(item['score_cppr']),
                    }
                };
                var data_perso = result['ranking_perso'].map(process)
                var data_noperso = result['ranking_noperso'].map(process)

                // console.log("DATA PERSO:", data_perso)
                // console.log("DATA NOPERSO:", data_noperso)

                callback(false, {'query_string': result['qstr'], 'perso': data_perso, 'noperso': data_noperso})
            });
            // });
        }
    }
});

module.exports = router;
