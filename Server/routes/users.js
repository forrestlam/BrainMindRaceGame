// handle the wechat user request
var express = require('express');
var router = express.Router();
var request = require('request');
var crypto = require('crypto');

/* GET users listing. */
router.get('/', function (req, res, next) {
  res.send({ 'users': global.users });
});

router.get('/login/:code', function (req, res) {
  var code = req.params.code;
  if (global.code2User[code]) {
    res.send({ 'success': true, 'user': global.code2User[code] });
  } else {
    request('https://api.weixin.qq.com/sns/jscode2session?appid=' + global.appID + '&secret=' + global.appSecret + '&js_code=' + code + '&grant_type=authorization_code',
      function (error, response, body) {
        if (!error && response.statusCode == 200) {
          console.log('login success, code=' + code + ', body=' + body) // 请求成功的处理逻辑
          var res = JSON.parse(body);

          var md5 = crypto.createHash('md5');
          md5.update(res.openid + res.session_key);
          var userId = md5.digest('hex');

          var newUser = { 'userId': userId, 'openId': res.openid, 'session_key': res.session_key };
          global.code2User[code] = newUser;
          global.users[newUser.userId] = newUser;
        } else {
          console.log('login failed');
        }
      }
    );
    res.send({ 'success': false });
  }
});

var bodyParser = require('body-parser');
 
// 创建 application/x-www-form-urlencoded 编码解析
var urlencodedParser = bodyParser.urlencoded({ extended: false });

router.post('/bindClient', urlencodedParser, function (req, res) {
  var clientId = req.body.clientId;
  var userId = req.body.userId;
  var nickname = req.body.nickname;
  var avatar = req.body.avatar;
  var user = { 'userId': userId, 'nickname': nickname, 'avatar': avatar };
  if (global.connections[clientId] == undefined) {
    global.connections[clientId] = user;
  }
  if (global.users[userId] == undefined) {
    // create a new user
    global.users[userId] = user;
  } else {
    // update the user info
    global.users[userId].nickname = nickname;
    global.users[userId].avatar = avatar;
  }
  console.log('connect client: ' + clientId + ' and user:' + userId);
  res.send({ 'success': true });
});

router.get('/getScore/:userId', function (req, res) {
  var userId = req.params.userId;
  if (global.users[userId] != undefined) {
    var user = global.users[userId];
    var lastScore = user.lastScore != undefined ? user.lastScore : 0;
    var maxScore = user.maxScore != undefined ? user.maxScore : 0;
    var hasUpdateScore = user.hasUpdateScore != undefined ? user.hasUpdateScore : false;
    var result = {
      'userId': userId,
      'lastScore': lastScore,
      'maxScore': maxScore,
      'title': '是个狼人',
      'rank': 0.98,
      'shape': [1, 2, 3],
      'hasUpdateScore': hasUpdateScore
    };
    res.send({ 'success': true, 'result': result });
  } else {
    res.send({ 'success': false, 'errMsg': 'user is not exist.' });
  }
});


module.exports = router;
