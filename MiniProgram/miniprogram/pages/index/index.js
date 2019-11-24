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
    // if (!wx.cloud) {
    //   wx.redirectTo({
    //     url: '../chooseLib/chooseLib',
    //   })
    //   return
    // }

    // // 获取用户信息
    // wx.getSetting({
    //   success: res => {
    //     if (res.authSetting['scope.userInfo']) {
    //       // 已经授权，可以直接调用 getUserInfo 获取头像昵称，不会弹框
    //       wx.getUserInfo({
    //         success: res => {
    //           this.setUserInfo(res);
    //         }
    //       })
    //     }
    //   }, 
    //   fail: e => {
    //     console.log(e);
    //   },
    //   complete: () => {
    //     console.log('complte authorize');
    //   }
    // })
    this.checkUserId();
  },

  onGetUserInfo: function(e) {
    if (!this.data.logged && e.detail.userInfo) {
      this.setData({
        logged: true,
        avatarUrl: e.detail.userInfo.avatarUrl,
        userInfo: e.detail.userInfo
      })
    }
  },
 
  onGetOpenid: function() {
    // 调用云函数
    wx.cloud.callFunction({
      name: 'login',
      data: {},
      success: res => {
        console.log('[云函数] [login] user openid: ', res.result.openid)
        app.globalData.openid = res.result.openid
        wx.navigateTo({
          url: '../userConsole/userConsole',
        })
      },
      fail: err => {
        console.error('[云函数] [login] 调用失败', err)
        wx.navigateTo({
          url: '../deployFunctions/deployFunctions',
        })
      }
    })
  },

  // 上传图片
  doUpload: function () {
    // 选择图片
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: function (res) {

        wx.showLoading({
          title: '上传中',
        })

        const filePath = res.tempFilePaths[0]
        
        // 上传图片
        const cloudPath = 'my-image' + filePath.match(/\.[^.]+?$/)[0]
        wx.cloud.uploadFile({
          cloudPath,
          filePath,
          success: res => {
            console.log('[上传文件] 成功：', res)

            app.globalData.fileID = res.fileID
            app.globalData.cloudPath = cloudPath
            app.globalData.imagePath = filePath
            
            wx.navigateTo({
              url: '../storageConsole/storageConsole'
            })
          },
          fail: e => {
            console.error('[上传文件] 失败：', e)
            wx.showToast({
              icon: 'none',
              title: '上传失败',
            })
          },
          complete: () => {
            wx.hideLoading()
          }
        })

      },
      fail: e => {
        console.error(e)
      }
    })
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
  },

  doLogin: function() {
    wx.login({
      success: res => {
        if (res.code) {
          wx.request({
            url: 'http://forrestlin.cn:3000/users/login/' + res.code,
            success: res => {
              console.log(res);
            }
          })
        }
      }
    })
  }
})
