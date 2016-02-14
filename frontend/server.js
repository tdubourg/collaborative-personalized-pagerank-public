'use strict';

var DBG = true

var readConfig = function () {
    var fs = require('fs')
    var config = {
        mdbHost: fs.readFileSync('./conf/mdb_host.conf', 'utf8'),
        cookieSecret: 'secret used to sign the cookies'
    }

    console.log('config:', config)

    return config
}

var setup = function (host, port) {
    var config = readConfig()

    var path = require('path')
    var pjoin = path.join
    var express = require('express')

    var session = require('express-session')
    var MongoStore = require('connect-mongo')(session)
    var logger = require('morgan')
    var cookieParser = require('cookie-parser')
    var bodyParser = require('body-parser')
    var mustacheExpress = require('mustache-express')

    var indexRoutes = require('./routes/index')
    var progressRoutes = require('./routes/progress')
    var sessionRoutes = require('./routes/session')
    var cst = require('./constants')

    var app = express()

    // view engine setup
    var mE = mustacheExpress()
    if (DBG) {
        mE.cache = null
    }
    // app.engine('mustache', mE)
    app.engine('html', mE)
    app.set('view engine', 'html')
    app.set('views', pjoin(__dirname, 'views'))

    // Middleware to serve the favicon
    app.use(logger('dev'))
    // Middleware to parse json bodies
    app.use(bodyParser.json())
    // Middleware to parse urlencoded bodies...
    app.use(bodyParser.urlencoded())
    // Middleware to process cookies
    app.use(cookieParser(config.cookieSecret))
    // Middleware to use sessions, here stored in memory.
    app.use(session({
        secret: config.cookieSecret,
        cookie: {maxAge: 3600*24*7*52*1000}, // 52 weeks cookie expiration 
        store: new MongoStore({url: 'mongodb://' + config.mdbHost + '/user_study/' + cst.SESSION_COLLECTION_NAME})
    }))

    // "express.static" is a middleware for serving static files
    app.use(express.static(pjoin(__dirname, 'public')))


    // Define the application's routes
    app.use('/', sessionRoutes)          // creates and prints the session
    app.use('/', indexRoutes)            // displays the pages
    app.use('/progress', progressRoutes) // saves the user's progress to the session

    // app.disable('view cache'); this does not seem to work
    return app
}


function setup_error_handlers (app) {
    /// catch 404 and forward to error handler
    app.use(function(req, res, next) {
        var err = new Error('Not Found')
        err.status = 404
        next(err)
    })

    /// error handlers
    app.use(function(err, req, res, next) {
        res.status(err.status || 500)
        res.render(err.status == 404 ? '404' : 'error', {
            message: err.message,
            error: err
        })
    })
}

function start (host, port) {
    var app = setup()
    setup_error_handlers(app)
    var server = app.listen(parseInt(port, 10), host, function() {
        console.log('Express.js is now listening on port %d', server.address().port)
    })
}

exports.start = start