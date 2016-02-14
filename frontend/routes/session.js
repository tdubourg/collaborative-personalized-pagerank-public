'use strict';

var express = require('express')
var router = express.Router()
var cst = require('../constants')


router.use('/', function (req, res, next) {
    console.log(new Date().toString())
    var do_not_redirect = false  // this bool is used only in one case for now, but it could come handy later
    if (req.query.named_session) {
        req.session.named = escape(req.query.named_session)
        do_not_redirect = true
    }
    if (!req.session.pages) { // Session is not yet initialized
        console.log('Creating a new session');
        req.session.created = new Date().toString()
        req.session.remote_addr = req.connection.remoteAddress
        req.session.pages = {}
        req.session.requests = 1
        req.session.completed = false
        if (!do_not_redirect) {
            // No session means it is the first visit of the user on the platform
            // So we redirect it to the start page, so that the help shows up
            res.writeHead(302, {
              'Location': '/#start'
            });
            res.end();            
            return
        };
    } else {
        req.session.updated = new Date().toString()
        req.session.requests++
        console.log('The user already did ' +  req.session.requests + ' requests.')
    }

    console.log('sessionid:', req.sessionID)

    next()
})

// @TODO used for debug: prints session in the browser!
router.get('/session', function (req, res) {
    res.json(req.session)
})

module.exports = router
