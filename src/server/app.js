var createError = require('http-errors');
var express = require('express');
var path = require('path');
var cookieParser = require('cookie-parser');
var logger = require('morgan');
var cors = require('cors');
var fs = require('fs');
var AWS = require('aws-sdk');

// Custom path for .env config as it defaults to the server dir
require('dotenv').config({ path: `${path.resolve(process.cwd())}/../../.env` })

var app = express();

// View engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'jade');

// Tooling setup
app.use(cors());
app.use(logger('dev', {
  stream: fs.createWriteStream('./server.log', {flags: 'a'})
}));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

// AWS Setup
AWS.config.credentials = new AWS.SharedIniFileCredentials({profile: process.env.PROFILE_KEY});
AWS.config.update({region: process.env.PROFILE_REGION});

// Route setup
var indexRouter = require('./routes/index');
app.use('/', indexRouter);
var userRouter = require("./routes/user");
app.use('/user', userRouter);

// catch 404 and forward to error handler
app.use(function(req, res, next) {
  next(createError(404));
});

// error handler
app.use(function(err, req, res, next) {
  // set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // render the error page
  res.status(err.status || 500);
  res.render('error');
});

module.exports = app;
