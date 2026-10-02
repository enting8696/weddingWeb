/* 社群 App 內開啟時，引導改用外部瀏覽器（由 merge.py 自動嵌入 index.html） */
(function () {
  var ua = navigator.userAgent || '';
  var isLine = /\bLine\//i.test(ua);
  var isFB = /FBAN|FBAV|FB_IAB|FBIOS|Messenger/i.test(ua);
  var isIG = /Instagram/i.test(ua);
  var isThreads = /Barcelona/i.test(ua);
  var isWeChat = /MicroMessenger/i.test(ua);
  var isAndroid = /Android/i.test(ua);
  var isIOS = /iPhone|iPad|iPod/i.test(ua);
  var inApp = isLine || isFB || isIG || isThreads || isWeChat || (isAndroid && /; wv\)/.test(ua));
  if (!inApp) return;

  var url = new URL(location.href);

  // 1) LINE：官方支援的參數，加上就會自動跳外部瀏覽器
  if (isLine && !url.searchParams.has('openExternalBrowser')) {
    url.searchParams.set('openExternalBrowser', '1');
    location.replace(url.toString());
    return;
  }

  // 2) Android 的 FB / IG / Messenger / Threads：用 intent 叫 Chrome 開
  if (isAndroid && !isLine && !url.searchParams.has('_ext')) {
    var back = new URL(location.href); back.searchParams.set('_ext', '1');
    location.href = 'intent://' + location.host + location.pathname + location.search +
      '#Intent;scheme=https;package=com.android.chrome;S.browser_fallback_url=' +
      encodeURIComponent(back.toString()) + ';end';
    // 沒裝 Chrome 或被擋時，下面的提示條仍會出現
  }

  // 3) iPhone 的 FB / IG / Messenger 等：無法強制跳出，顯示提示條
  var clean = location.origin + location.pathname;
  var menu = isIOS ? '右上角 ⋯ 或右下角 Safari 圖示' : '右上角 ⋮';
  function showBar() {
    if (!document.body || document.getElementById('__ext_bar')) return;
    var bar = document.createElement('div');
    bar.id = '__ext_bar';
    bar.style.cssText = 'position:fixed;left:12px;right:12px;bottom:calc(14px + env(safe-area-inset-bottom));z-index:99999;' +
      'display:flex;align-items:center;gap:10px;padding:12px 14px;border-radius:16px;' +
      'background:rgba(40,32,28,.94);color:#f5e6d3;font:14px/1.5 "Noto Serif TC",serif;letter-spacing:.04em;' +
      'box-shadow:0 10px 30px rgba(0,0,0,.3);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px)';
    bar.innerHTML =
      '<div style="flex:1">建議用瀏覽器開啟，畫面與回函更順暢<br>' +
      '<small style="opacity:.75">點 ' + menu + ' →「在瀏覽器中開啟」</small></div>' +
      '<button id="__ext_copy" style="flex:0 0 auto;border:1px solid #ecd5bd;background:transparent;color:#ecd5bd;' +
      'border-radius:999px;padding:6px 12px;font:inherit;font-size:13px;white-space:nowrap">複製連結</button>' +
      '<button id="__ext_close" aria-label="關閉" style="flex:0 0 auto;border:0;background:transparent;color:#f5e6d3;font-size:18px;padding:0 4px">✕</button>';
    document.body.appendChild(bar);
    document.getElementById('__ext_close').onclick = function () { bar.remove(); window.__extBarClosed = true; };
    document.getElementById('__ext_copy').onclick = function () {
      var btn = this;
      var ok = function () { btn.textContent = '已複製 ✓'; };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(clean).then(ok, function () { prompt('請複製此連結', clean); });
      } else { prompt('請複製此連結', clean); }
    };
  }
  // 網頁載入時整個畫面會被替換，所以持續確認提示條還在（約 20 秒）
  var tries = 0;
  var timer = setInterval(function () {
    if (window.__extBarClosed || ++tries > 40) return clearInterval(timer);
    showBar();
  }, 500);
})();
