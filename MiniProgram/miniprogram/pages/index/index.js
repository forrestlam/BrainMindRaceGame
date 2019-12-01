//index.js
const app = getApp()

Page({
  data: {
    avatarUrl: './user-unlogin.png',
    userInfo: {},
    logged: false,
    takeSession: false,
    requestResult: '',
    userID: '',
    code: '',
    nickName: '未登录',
    hideScore: true,
    topScore: 0,
    localAvatarUrl: './user-unlogin.png',
    showModal: false,
    openID: ''
  },

  context2d: undefined,
  canvasWidth: 0,
  canvasHeight: 0,

  setUserInfo: function(res) {
    console.log(res);
    this.setData({
      avatarUrl: res.userInfo.avatarUrl,
      userInfo: res.userInfo,
      nickName: res.userInfo.nickName
    });
    if (this.data.openID.length > 0) {
      app.vans.saveInfo({
        openid: this.data.openID,
        nickname: res.userInfo.nickName,
        gender: res.userInfo.gender,
        avatar: res.userInfo.avatarUrl,
        extr: this.data.userID,
        tel: ""
      });
    }
    var that = this;
    wx.downloadFile({
      url: res.userInfo.avatarUrl,
      success: res => {
        // 只要服务器有响应数据，就会把响应内容写入文件并进入 success 回调，业务需要自行判断是否下载到了想要的内容
        if (res.statusCode === 200) {
          that.setData({
            localAvatarUrl: res.tempFilePath//将下载下来的地址给data中的变量变量
          });
        }
      }, fail: res => {
        console.log(res);
      }
    });
  },

  requestUserId: function(code) {
    wx.request({
      url: 'https://forrestlin.cn/users/login/' + code,
      success: res => {
        console.log(res);
        if (res.data.success) {
          if (res.data.user.userId.length) {
            this.data.userID = res.data.user.userId;
            if (res.data.user.openId.length > 0) {
              this.data.openID = res.data.user.openId;
              app.vans.saveInfo({
                openid: res.data.user.openId,
                nickname: "",
                gender: "male",
                avatar: "",
                extr: this.data.userID,
                tel: ""
              });
            }
          }
        } else {
          if (res.data.errMsg == 'invalid code') {
            this.data.code = "";
            console.error('login failed, invalid code');
          }
        }
      }
    })
  },

  checkUserId: function() {
    if (this.data.userID.length == 0) {
      if (this.data.code.length == 0) {
        // 还没登录
        wx.login({
          success: res => {
            if (res.code) {
              this.data.code = res.code;
              this.requestUserId(res.code);
            }
          }
        });
      } else {
        this.requestUserId(this.data.code);
      }
      setTimeout(this.checkUserId, 1000);
    }
  },

  // 获取用户信息
  getUserInfo: function() {
    wx.getSetting({
      success: res => {
        if (res.authSetting['scope.userInfo']) {
          // 已经授权，可以直接调用 getUserInfo 获取头像昵称，不会弹框
          wx.getUserInfo({
            success: res => {
              this.setUserInfo(res);
            }
          })
        }
      }, 
      fail: e => {
        console.log(e);
      },
      complete: () => {
        console.log('complte authorize');
      }
    })
  },

  onLoad: function() {
    this.checkUserId();
    this.getUserInfo();
  },

  // 扫码
  doScan: function(e) {
    if (this.data.userID.length == 0) {
      wx.showToast({
        title: '未登录服务器，请稍后再试',
      });
      console.error('还没登录服务器，请稍后再试');
      return;
    }
    if (e.detail.userInfo) {
      this.setUserInfo(e.detail);
      wx.scanCode({
        scanType: ['qrCode'],
        success: res => {
          console.log(res);
          var clientId = res.result;
          if (clientId.startsWith('alicia:')) {
            clientId = clientId.substr(7);
            wx.request({
              url: 'https://forrestlin.cn/users/bindClient',
              method: 'POST',
              data: {
                clientId: clientId,
                userId: this.data.userID,
                nickname: this.data.nickName,
                avatar: this.data.avatarUrl,
                city: this.data.userInfo.city,
                province: this.data.userInfo.province,
                country: this.data.userInfo.country
              },
              success: res => {
                if (!res.data.success) {
                  console.error(res);
                  wx.showToast({
                    title: '连接失败',
                    icon: 'none'
                  })
                } else {
                  wx.showToast({
                    title: '连接成功',
                  });
                }
              }
            })
          } else {
            console.error('扫码错误，res=' + res.result);
          }
        },
        fail: e => {
          console.error(e);
        },
        complete: () => {

        }
      });
    } else {
      console.error('授权失败');
    }
  },

  showScore: function(e) {
    if (this.data.userID.length == 0) {
      wx.showToast({
        title: '未登录服务器，请稍后再试',
        icon: 'none'
      });
      console.error('还没登录服务器，请稍后再试');
      return;
    }
    wx.request({
      url: 'https://forrestlin.cn/users/getScore/' + this.data.userID,
      success: res => {
        console.log(res);
        if (res.data.success) {
          this.setData({
            hideScore: false,
            showModal: true
          });
          // this.drawSharePic(res.data.result.maxScore, res.data.result.concen);
          var topScore = res.data.result.maxScore;
          var concen = res.data.result.concen;
          var waves = res.data.result.waves;
          if (topScore == undefined || concen == undefined || waves == undefined) {
            // make fake score
            topScore = 80;
            concen = 90;
            waves = [5, 6, 8, 10, 8, 4, 3, 5, 3, 7, 5, 6, 8, 10, 8, 4, 3, 5, 3, 7];
          }
          this.drawSharePic(topScore, concen, waves);
          // wx.showToast({
          //   title: '最高成绩是' + res.data.result.maxScore,
          // });
        } else {
          wx.showToast({
            title: '获取成绩失败',
            icon: 'none'
          });
        }
      }
    })
  },

  drawSharePic: function(topScore, concen, waves) {
    var that = this;
    var systemInfo = wx.getSystemInfoSync();
    var windowWidth = systemInfo.windowWidth;
    var windowHeight = systemInfo.windowHeight;
    var canvasWidth = 0.8 * windowWidth;
    var left = (windowWidth - canvasWidth) / 2;
    var canvasHeight = 0.7 * windowHeight;
    this.canvasWidth = canvasWidth;
    this.canvasHeight = canvasHeight;
    var context = wx.createCanvasContext("rankpic");
    this.context2d = context;
    var gap = windowWidth * 0.05;
    var scale = windowWidth / 320;
    context.drawImage("./rankbg.png", 0 + left, 0, canvasWidth, canvasHeight);
    var topScoreWidth = 106 * scale, topScoreHeight = 13 * scale;
    context.drawImage('./top-score.png', (canvasWidth - topScoreWidth) / 2 + left, 
      gap, topScoreWidth, topScoreHeight);
    var avatarWidth = 40 * scale, avatarHeight = 40 * scale;
    context.drawImage(this.data.localAvatarUrl, (canvasWidth - avatarWidth) / 2 + left, 
      gap * 2 + topScoreHeight, avatarWidth, avatarHeight);
    var typeWidth = 522/4 * scale, typeHeight = 96/4 * scale;
    var typeId = Math.floor(topScore / 20) + 1;
    if (topScore > 100) {
      typeId = 6;
    }
    context.drawImage('./type'+typeId+'.png', (canvasWidth - typeWidth) / 2 + left, 
      gap * 3 + avatarHeight + topScoreHeight, typeWidth, typeHeight);
    context.setFontSize(12);
    context.setFillStyle('white');
    context.fillText("游戏得分: " + topScore + '分', (canvasWidth - typeWidth) / 2 - 23 + left, 
      gap * 3 + avatarHeight + topScoreHeight + typeHeight + 15);
    context.fillText("专注度: " + Math.round(concen) + '分', canvasWidth / 2 + 10 + left, 
      gap * 3 + avatarHeight + topScoreHeight + typeHeight + 15);

    // draw waves
    var waveX = 20, waveY = gap * 3 + avatarHeight + topScoreHeight + typeHeight + 15 + 30, waveWidth = canvasWidth - waveX * 2, waveHeight = canvasHeight - waveY - 10;
    // draw max 20 wave
    context.setStrokeStyle('white');
    var count = waves.length;
    context.beginPath()
    context.moveTo(waveX + left, waveY + waveHeight / 2);
    var waveUnitWidth = waveWidth / count;
    console.log('waves='+waves);
    for (var i = 0; i < count; i++) {
      var waveValue = waves[i] - 1;
      waveValue = Math.max(waveValue, 0.5);
      waveValue = Math.min(waveValue, 10);
      context.lineTo(waveX + waveUnitWidth * (i + 1) + left, waveY + (10 - waveValue) * waveHeight / 10);
    }
    context.stroke()
    context.draw();
  },

  doShare: function(e) {
    var that = this;
    if (this.context2d) {
      wx.canvasToTempFilePath({
        x: 0,
        y: 0,
        destWidth: this.canvasWidth * 3,
        destHeight: this.canvasHeight * 3,
        canvasId: 'rankpic',
        success(res) {
          wx.saveImageToPhotosAlbum({
            filePath: res.tempFilePath,
            success(res) {
              wx.showToast({
                title: '保存成功，赶快去分享吧^_^',
                icon: 'none'
              });
              setTimeout(() => {
                that.setData({
                  hideScore: true,
                });
              }, 2000);
            }
          });
        }
      });
    }
  },

  cancelShare: function(e) {
    this.setData({
      hideScore: true,
      showModal: false,
    });
  },

  onShareAppMessage: function () {

  }
})
