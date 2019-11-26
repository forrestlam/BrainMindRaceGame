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
    nickName: ''
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

  onLoad: function() {
    this.checkUserId();
  },

  // 扫码
  doScan: function(e) {
    if (this.data.userID.length == 0) {
      console.error('还没登录服务器，请稍后再试');
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
                avatar: this.data.avatarUrl
              },
              success: res => {
                if (!res.data.success) {
                  console.error(res);
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
  }
})
