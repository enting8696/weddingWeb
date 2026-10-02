/* 出席回函：隱藏式 iframe 送到 Google 表單（由 merge.py 自動嵌入 index.html） */
(function () {
  var FORM_ID = '1FAIpQLSeGo9noyiMKCWlhBp0oxbXpVHgvHpkkURV1CQATke9u-acWtw';
  var E = { name: 'entry.214103667', email: 'entry.1165468626', rel: 'entry.189367968',
            guests: 'entry.380447004', meat: 'entry.2101957223', veg: 'entry.384739430',
            chair: 'entry.880669736', msg: 'entry.1023712468' };
  var busy = false;

  function toast(text) {
    var t = document.getElementById('__rsvp_toast');
    if (!t) {
      t = document.createElement('div');
      t.id = '__rsvp_toast';
      t.style.cssText = 'position:fixed;left:50%;bottom:28px;transform:translateX(-50%);z-index:9999;' +
        'background:rgba(40,32,28,.92);color:#f5d7ae;padding:12px 22px;border-radius:999px;' +
        'font:15px/1.4 "Noto Serif TC",serif;letter-spacing:.1em;box-shadow:0 8px 24px rgba(0,0,0,.25);' +
        'transition:opacity .3s;white-space:nowrap;max-width:92vw';
      document.body.appendChild(t);
    }
    t.textContent = text; t.style.opacity = '1';
    clearTimeout(t._h); t._h = setTimeout(function () { t.style.opacity = '0'; }, 2600);
  }

  window.__weddingSubmit = function (done) {
    if (busy) return;
    var $ = function (id) { return document.getElementById(id); };
    var v = function (id) { var el = $(id); return el ? String(el.value || '').trim() : ''; };
    var fail = function (id, text) {
      toast(text);
      var el = $(id);
      if (el) { el.scrollIntoView({ block: 'center', behavior: 'smooth' }); setTimeout(function () { el.focus(); }, 300); }
    };

    var d = { name: v('f-name'), email: v('f-email'), rel: v('f-rel'), guests: v('f-guests'),
              meat: v('f-meat'), veg: v('f-veg'), chair: v('f-chair'), msg: v('f-msg') };
    var n = parseInt(d.guests, 10);

    if (!d.name) return fail('f-name', '請填寫姓名');
    if (d.email && !/^\S+@\S+\.\S+$/.test(d.email)) return fail('f-email', 'Email 格式不正確');
    if (!d.rel) return fail('f-rel', '請選擇與新人關係');
    if (!Number.isFinite(n) || n < 0) return fail('f-guests', '請填寫參加人數（不克出席請填 0）');
    var meat = d.meat === '' ? 0 : parseInt(d.meat, 10);
    var veg  = d.veg  === '' ? 0 : parseInt(d.veg, 10);
    if (n > 0) {
      if (!Number.isFinite(meat) || meat < 0) return fail('f-meat', '葷食人數請填 0 以上的數字');
      if (!Number.isFinite(veg)  || veg  < 0) return fail('f-veg',  '素食人數請填 0 以上的數字');
      if (meat + veg !== n) return fail(d.meat === '' ? 'f-meat' : 'f-veg', '葷食＋素食需等於參加人數（' + n + ' 位）');
    }

    busy = true;
    toast('傳送中…');

    var iframe = document.createElement('iframe');
    iframe.name = '__rsvp_iframe_' + Date.now();
    iframe.style.display = 'none';
    document.body.appendChild(iframe);

    var form = document.createElement('form');
    form.method = 'POST';
    form.action = 'https://docs.google.com/forms/d/e/' + FORM_ID + '/formResponse';
    form.target = iframe.name;
    form.style.display = 'none';

    var add = function (key, val) {
      if (val === '' || val == null) return;
      var i = document.createElement('input');
      i.type = 'hidden'; i.name = E[key]; i.value = val; form.appendChild(i);
    };
    add('name', d.name); add('email', d.email); add('rel', d.rel); add('guests', String(n));
    add('meat', String(n > 0 ? meat : 0)); add('veg', String(n > 0 ? veg : 0));
    if (n > 0) add('chair', d.chair);
    add('msg', d.msg);

    var finished = false;
    var finish = function () {
      if (finished) return; finished = true; busy = false;
      var t = document.getElementById('__rsvp_toast'); if (t) t.style.opacity = '0';
      if (typeof done === 'function') done();
      setTimeout(function () { form.remove(); iframe.remove(); }, 1000);
    };
    iframe.addEventListener('load', finish);
    setTimeout(finish, 5000); // 保險：iframe 沒觸發 load 也會結束

    document.body.appendChild(form);
    form.submit();
  };
})();
