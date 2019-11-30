var createError = require('http-errors');
var express = require('express');
var path = require('path');
var cookieParser = require('cookie-parser');
var logger = require('morgan');
var fs = require('fs');

global.connections = {};
global.users = {};
global.appID = 'wx5e66ea49aa7fda33';
global.appSecret = '24aa81ecf9b469250a4ffa74f8b27182';
global.code2User = {};

fs.exists('./data/users.txt', function(exists) {
  if (exists) {
    fs.readFile('./data/users.txt', 'utf-8', function(err, data) {
      if (err) {
        throw(err);
      }
      try {
        global.users = JSON.parse(data.toString());
      } catch(error) {
        console.log('parse users data error');
      }
    });
  }
});

var indexRouter = require('./routes/index');
var usersRouter = require('./routes/users');
var gamesRouter = require('./routes/games');
var imageRouter = require('./routes/image');

var app = express();

// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'jade');

app.use(logger('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

app.use('/', indexRouter);
app.use('/users', usersRouter);
app.use('/games', gamesRouter);
app.use('/image', imageRouter);

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
