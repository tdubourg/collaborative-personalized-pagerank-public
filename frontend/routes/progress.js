'use strict';

var express = require('express')
var router = express.Router()
var cst = require('../constants')



var createPage = function () {
    return {
        cppr: {},
        standard: {},
        best: null,
        submitted: false
    }
}

var isAlgorithmValid = function (algorithm) {
    return algorithm == 'cppr' || algorithm == 'standard'
}

var getPageData = function (req) {
    return req.session.pages[req.params.pageId]
}



var actionHandlers = {
    relevant : function relevantHandler (req, res) {
        var errors = []
        var pageData = getPageData(req)

        // Validating the input
        if (! req.body.link)  {
            errors.push('No link.')
        }

        if (! isAlgorithmValid(req.body.algorithm)) {
            errors.push('Invalid algorithm. Must be "cppr" or "standard".')
        }

        if (req.body.relevant === true && (1*req.body.index !== req.body.index)) {
            errors.push("Index error. If the input is relevant, it must be a number.")
        }

        if ( errors.length > 0 ) {
            return errors
        }

        // Updating the session
        if (req.body.relevant === true) {
            pageData[req.body.algorithm][req.body.link] = req.body.index
        } else {
            delete pageData[req.body.algorithm][req.body.link]
        }
    },

    submit : function submitHandler (req, res) {
        getPageData(req).submitted = true

        if (req.params.pageId >= cst.SURVEY_PAGE_COUNT) {
            req.session.completed = true
        }
    },

    best: function bestHandler (req, res) {
        if (! isAlgorithmValid(req.body.algorithm)) {
            return 'Invalid algorithm. Must be "cppr" or "standard".'
        }

        getPageData(req).best = req.body.algorithm
    }
}


// Stuff is actually done starting here.

router.put('/page/:pageId/:action', function (req, res) {
    var handler = actionHandlers[req.params.action]
    var errors = []

    if (handler) {
        errors.concat(handler(req, res))
    } else {
        errors.push('Unrecognized action: ' + req.params.action)
    }

    if (errors.length > 0) {
        res.json(400, errors)
    } else {
        res.send(200)
    }
})

router.param('pageId', function (req, res, next, pageId) {
    if (! req.session.pages[pageId]) {
        req.session.pages[pageId] = createPage()
    }

    next()
})



module.exports = router
