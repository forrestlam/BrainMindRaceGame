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

router.get('/finishGame/:clientId/:userId/:score', function(req, res) {
    var clientId = req.params.clientId;
    var score = req.params.score;
    var userId = req.params.userId;
    if (global.connections[clientId] && global.connections[clientId] == userId && users[userId]) {
        delete global.connections[clientId];
        user = global.users[userId];
        if (global.user.maxScore != undefined) {
            global.user.maxScore = Math.max(global.user.maxScore, score);
        } else {
            global.user.maxScore = score;
        }
        global.user.lastScore = score;
        res.send({'success': true});
    } else {
        res.send({'success': false, 'errMsg': 'connection is not legal.'});
    }
});

module.exports = router;