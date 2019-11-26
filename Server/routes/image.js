// handle the wechat user request
var express = require('express');
var router = express.Router();
var fs = require('fs');
var path = require('path');
var app = express();

var config = app.get('read');
var targetDir = app.get('targetDir');

router.get('/:filename', function (req, res) {
    var filePath = './images/'+(req.params.filename);
    console.log('filePath='+filePath);
    fs.exists(filePath, function (exists) {
        if (exists) {
            res.sendfile(filePath);
        } else {
            res.send({'success': false, 'errMsg': 'file not exists.'});
        }
    });
});

module.exports = router;
