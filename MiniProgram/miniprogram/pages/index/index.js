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
    showScore: false
  },

  setUserInfo: function(res) {
    console.log(res);
    this.setData({
      avatarUrl: res.userInfo.avatarUrl,
      userInfo: res.userInfo,
      nickName: res.userInfo.nickName
    })
  },

  requestUserId: function(code) {
    wx.request({
      url: 'https://forrestlin.cn/users/login/' + code,
      success: res => {
        console.log(res);
        if (res.data.success) {
          this.data.userID = res.data.user.userId
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
      });
      console.error('还没登录服务器，请稍后再试');
      return;
    }
    wx.request({
      url: 'https://forrestlin.cn/users/getScore/' + this.data.userID,
      success: res => {
        console.log(res);
        if (res.data.success) {
          wx.showToast({
            title: '最高成绩是' + res.data.result.maxScore,
          });
        } else {
          wx.showToast({
            title: '获取成绩失败',
            icon: 'none'
          });
        }
      }
    })
  },
})
