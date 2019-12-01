//app.js
const Vans = require('./utils/vanswx.js')
App({
  onLaunch: function (options) {
    this.vans = Vans;
    Vans.App.init({ appid: 'mp5fe6he2bdh0b5f36', lauchOpts: options }) //appid为有数平台为参赛者提供的appid
    this.globalData = {}
  }
});