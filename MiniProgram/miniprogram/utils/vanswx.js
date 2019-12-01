"use strict";var VANS_CONFIG={appid:"",api_base:"https://lingshou.tencent.com/vans",prefix:"_vans_",version:"1.0.0"};function onlineTime(){try{if(!VANS.Data.loaded){VANS.Data.loaded=1,VANS.Data.intervalId||(VANS.Data.intervalId=setInterval(function(){VANS.Data.appShow&&VANS.Page.page("auto")},5e3));try{wx.onAppShow(function(){VANS.Data.appShow=1}),wx.onAppHide(function(){VANS.Data.appShow=0})}catch(a){}try{wx.Show(function(){VANS.Data.appShow=1}),wx.Hide(function(){VANS.Data.appShow=0})}catch(a){}}}catch(a){}}function getUID(){var a=_getUID();return a=a||setUID()}function _getUID(){try{return wx.getStorageSync(VANS_CONFIG.prefix+"auid")}catch(a){}}function setUID(){try{var a=getRandom();return wx.setStorageSync(VANS_CONFIG.prefix+"auid",a),a}catch(a){}}function getRandom(a){for(var e=[0,1,2,3,4,5,6,7,8,9],t=10;1<t;t--){var n=Math.floor(10*Math.random()),r=e[n];e[n]=e[t-1],e[t-1]=r}for(t=n=0;t<5;t++)n=10*n+e[t];return(a||"")+(n+"")+ +new Date}function getPagePath(){try{var a=getCurrentPages(),e="/";return 0<a.length&&(e=a.pop().__route__),e}catch(a){console.log("get current page path error:"+a)}}function initOnload(){var t=Page;Page=function(a){var e=a.onLoad;a.onLoad=function(a){e&&e.call(this,a),VANS.Data.lastPageQuery=VANS.Data.pageQuery,VANS.Data.pageQuery=a,VANS.Data.lastPageUrl=VANS.Data.pageUrl,VANS.Data.pageUrl=getPagePath(),VANS.Data.show=!1,VANS.Page.init()},t(a)}}function setSharePath(){var a=0<arguments.length&&void 0!==arguments[0]?arguments[0]:{};try{VANS.Page.share()}catch(a){}try{return a.path?0<=a.path.indexOf("?")?("&"!=a.path[a.path.length-1]&&(a.path+="&"),a.path+=VANS_CONFIG.prefix+"uid="+getUID()):a.path+="?"+VANS_CONFIG.prefix+"uid="+getUID():a.path=getPagePath()+"?"+VANS_CONFIG.prefix+"uid="+getUID(),a}catch(a){return console.error(a),{}}}var VANS={App:{init:function(a){"appid"in a&&(VANS_CONFIG.appid=a.appid);try{"lauchOpts"in a&&(VANS.Data.lanchInfo=a.lauchOpts),a&&a.lauchOpts&&a.lauchOpts.query&&(VANS.Data.source=a.lauchOpts.query[VANS_CONFIG.prefix+"uid"]||"")}catch(a){}try{initOnload()}catch(a){}onlineTime(),VANS.Page.stat()}},Page:{init:function(){var e,a,t=getCurrentPages()[getCurrentPages().length-1];t.onShow&&(e=t.onShow,t.onShow=function(){if(!0===VANS.Data.show){var a=VANS.Data.lastPageQuery;VANS.Data.lastPageQuery=VANS.Data.pageQuery,VANS.Data.pageQuery=a,VANS.Data.lastPageUrl=VANS.Data.pageUrl,VANS.Data.pageUrl=getPagePath()}VANS.Data.show=!0,e.apply(this,arguments)}),t.onShareAppMessage?(a=t.onShareAppMessage,t.onShareAppMessage=function(){return setSharePath(a.apply(this,arguments))}):t.onShareAppMessage=function(){return setSharePath({})},VANS.Page.page()},page:function(a){if(""!=VANS_CONFIG.app_id){var e=[];e=["uid="+getUID(),"page="+(a=a||encodeURIComponent(VANS.Data.pageUrl)),"appid="+VANS_CONFIG.appid],wx.request({url:VANS_CONFIG.api_base+"/sdk/page?"+e.join("&").toLowerCase()})}},stat:function(){if(""!=VANS_CONFIG.app_id){var a=[];a=["uid="+getUID(),"page="+encodeURIComponent(VANS.Data.pageUrl),"appid="+VANS_CONFIG.appid],wx.request({url:VANS_CONFIG.api_base+"/sdk/stat?"+a.join("&").toLowerCase()})}},share:function(){if(""!=VANS_CONFIG.app_id){var a=[];a=["uid="+getUID(),"page="+encodeURIComponent(VANS.Data.pageUrl),"appid="+VANS_CONFIG.appid],wx.request({url:VANS_CONFIG.api_base+"/sdk/share?"+a.join("&").toLowerCase()})}}},saveInfo:function(a){var e=0<arguments.length&&void 0!==a?a:{},t=e.openid||"",n=e.nickname||"",r=e.gender||"",o=e.avatar||"",p=e.tel||"",i=e.extr||"",u=getUID(),g=VANS_CONFIG.appid;g?u?wx.request({url:VANS_CONFIG.api_base+"/api/saveInfo",method:"post",data:{appid:g,uid:u,openid:t,nickname:n,gender:r,avatar:o,tel:p,extr:i}}):console.error("没有uid"):console.error("没有appid")},getInfo:function(e,a){"function"!=typeof e&&(e=function(){}),"function"!=typeof a&&(a=function(){});var t=getUID(),n=VANS_CONFIG.appid;wx.request({url:VANS_CONFIG.api_base+"/api/getInfo?appid="+n+"&uid="+t,method:"get",success:function(a){e(a.data)},fail:function(a){e(a)}})},Data:{source:"",openid:"",lanchInfo:null,pageQuery:null,lastPageQuery:null,pageUrl:"",lastPageUrl:"",show:!1,intervalId:0,loaded:0,appShow:1}};module.exports=VANS;