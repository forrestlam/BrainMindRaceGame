// handle the request from the game client

var express = require('express');
var router = express.Router();

/* GET game client listing. */
router.get('/', function(req, res) {
  res.send({'connections': global.connections});
});

router.get('/isReadyToPlay/:clientId', function(req, res) {
    var clientId = req.params.clientId;
    if (global.connections[clientId]) {
        var user = global.connections[clientId];
        res.send({'success': true, 'user': user})
    } else {
        res.send({'success': false, 'errMsg': 'connection is not exist.'});
    }
});

var bodyParser = require('body-parser');
// 创建 application/x-www-form-urlencoded 编码解析
var urlencodedParser = bodyParser.urlencoded({ extended: false });
router.post('/finishGame', urlencodedParser, function(req, res) {
    var clientId = req.body.clientId;
    var score = req.body.score;
    var userId = req.body.userId;
    var concen = req.body.concen;
    var waves = req.body.waves;
    console.log('score='+score);
    if (global.connections[clientId] && global.connections[clientId].userId == userId && global.users[userId]) {
        // delete global.connections[clientId];
        user = global.users[userId];
        if (user.maxScore != undefined) {
            user.maxScore = Math.max(user.maxScore, score);
        } else {
            user.maxScore = score;
        }
        user.lastScore = score;
        user.concen = concen;
        user.waves = waves;
        res.send({'success': true});
    } else {
        res.send({'success': false, 'errMsg': 'connection is not legal.'});
        console.log('Failed to finish game. Connection is not legal.');
    }
});

router.get('/closeConnection/:clientId/:userId', function(req, res) {
    var clientId = req.params.clientId;
    var userId = req.params.userId;
    if (global.connections[clientId] && global.connections[clientId].userId == userId && users[userId]) {
        delete global.connections[clientId];
        res.send({'success': true});
    } else {
        res.send({'success': false, 'errMsg': 'connection is not legal.'});
        console.log('Failed to close connection. Connection is not legal.');
    }
});

module.exports = router;