# 用法：python merge.py
# 把 Claude Design 匯出的 HTML 補上以下設定，輸出成 index.html：
#   1. 手機 viewport   2. 分享預覽標籤   3. 高螢幕樣式只給桌機
#   4. 回函送到 Google 表單（需要 rsvp_submit.js）
#   5. 社群 App 內引導外部瀏覽器（需要 open_external.js）
#   6. 分享縮圖用 IMAGE_URL
#   7. 回函送出後的感謝文字，依人數顯示不同內容
#   8. 飲食需求改成「葷食人數 / 素食人數」兩格數字
#   9. 兒童椅欄位獨立一整行（對齊）
#  10. 背景婚紗照位置微調（PHOTO_POS_X / PHOTO_POS_X_WIDE，只平移不放大）
import re, json, glob, sys

src = [f for f in glob.glob("*.html") if f != "index.html"]
if len(src) > 1:
    sys.exit(f"資料夾內只能有一個匯出的 HTML（不含 index.html），目前找到：{src}")
src = src[0] if src else "index.html"   # 沒有新匯出檔時，直接修補現有的 index.html
s = open(src, encoding="utf8", newline="").read()
nl = "\r\n" if "\r\n" in s[:500] else "\n"

SITE = "https://enting8696.github.io/weddingWeb/"
# 分享縮圖網址（postimg 的「直接連結」）；網頁背景仍用設計稿內嵌的照片
IMAGE_URL = "https://i.postimg.cc/GpmccCvQ/ting-en-ruo-wai-503.jpg"
OG_IMAGE_URL = IMAGE_URL
# 背景照片位置（只平移、不放大）：數字越小人物越往右，範圍 0%~100%，50% = 置中
PHOTO_POS_X      = "47%"   # 手機（直式螢幕）
PHOTO_POS_X_WIDE = "0%"    # 電腦（橫式螢幕）；可移動的空間有限，0% 已是最右
THANKS_COME = "期待與您在婚禮相見 ♡"          # 人數 > 0
THANKS_NOT  = "謝謝您的祝福，我們會想念您的 ♡"   # 人數 = 0

VIEWPORT = "width=device-width, initial-scale=1, viewport-fit=cover"
META = [
    f'<meta name="viewport" content="{VIEWPORT}">',
    '<meta name="description" content="誠摯邀請與你分享喜悅">',
    '<meta property="og:type" content="website">',
    '<meta property="og:url" content="https://enting8696.github.io/weddingWeb/">',
    '<meta property="og:title" content="Leo &amp; Julie 婚禮邀請函">',
    '<meta property="og:description" content="誠摯邀請與你分享喜悅">',
    '<meta property="og:image" content="https://i.postimg.cc/pLTPQC4z/F9B927E3-6884-405F-B9A0-C259D6E86757.jpg">',
    '<meta name="twitter:card" content="summary_large_image">',
]

def embed(s, fname):
    """把 js 檔貼進 </title> 後面；已經貼過的舊版本會先移除，確保是最新版"""
    js = open(fname, encoding="utf8").read()
    first = js.strip().splitlines()[0]
    s = re.sub(r"\s*<script>\s*" + re.escape(first) + r".*?</script>", "", s, flags=re.S)
    a = "</title>"
    assert a in s
    return s.replace(a, a + nl + "  <script>" + nl + js + nl + "  </script>", 1)

# 1) 外層 head：viewport + 分享預覽
if "og:description" not in s:
    a = '<meta charset="utf-8">'
    assert s.count(a) == 1, "找不到外層 <meta charset>"
    s = s.replace(a, a + "".join(nl + "  " + m for m in META), 1)

# 2) 內層 template head：viewport
b = '<meta charset=\\"utf-8\\">'
vp = f'<meta name=\\"viewport\\" content=\\"{VIEWPORT}\\">'
if vp not in s:
    assert s.count(b) == 1, "找不到內層 template 的 <meta charset>"
    s = s.replace(b, b + vp, 1)

# 3) 高螢幕樣式只給桌機
s = s.replace("@media (min-height:1400px){", "@media (min-height:1400px) and (min-width:1024px){")

# 4) 出席回函：改成真的送到 Google 表單
OLD_SEND = "send: () => this.setState({ sent: true })"
NEW_SEND = "send: () => window.__weddingSubmit(() => this.setState({ sent: true }))"
if NEW_SEND not in s:
    assert s.count(OLD_SEND) == 1, "找不到回函的 send 函式，設計稿結構可能改了"
    s = s.replace(OLD_SEND, NEW_SEND, 1)
s = embed(s, "rsvp_submit.js")

# 5) 社群 App 內開啟 → 引導外部瀏覽器（放在最前面，越早執行越好）
s = embed(s, "open_external.js")

# 6) 分享縮圖：換成 OG_IMAGE_URL
s = re.sub(r'<meta property="og:image" content="[^"]*">', f'<meta property="og:image" content="{OG_IMAGE_URL}">', s, count=1)
s = re.sub(r'\s*<meta property="og:image:(width|height)"[^>]*>', '', s)

# 7) 感謝文字依人數切換
OLD_THX = "已收到您的回覆，<br>期待與您在婚禮相見 ♡"
if OLD_THX in s:
    s = s.replace(OLD_THX, "{{ thx1 }}<br>{{ thx2 }}", 1)
P = "p: this.state.p.toFixed(3),"
if "thx2:" not in s:
    assert s.count(P) == 1, "找不到 renderVals，設計稿結構可能改了"
    s = s.replace(P, P + f" thx1: '已收到您的回覆，', thx2: (Number.isFinite(n) && n > 0 ? '{THANKS_COME}' : '{THANKS_NOT}'),", 1)

# 8) 飲食需求：下拉選單 → 葷食人數 / 素食人數
TPL_RE = r'(<script type="__bundler/template">\s*)(.*?)(\s*</script>)'
tm = re.search(TPL_RE, s, re.S)
tpl = json.loads(tm.group(2))
if 'id="f-veg"' not in tpl:
    i = tpl.find('<label for="f-diet"')
    assert i > 0, "找不到飲食需求欄位，設計稿結構可能改了"
    j = tpl.rfind('<div', 0, i); k = tpl.find('</div>', i) + 6
    label_style = re.search(r'<label for="f-guests" (style="[^"]*")>', tpl).group(1)
    input_style = re.search(r'<input class="fi" type="number" id="f-guests"[^>]*?(style="[^"]*")', tpl).group(1)
    en = "<span style=\"font-family: 'Cormorant Garamond', serif; font-size: .78rem; color: #ecd5bd; letter-spacing: .28em\">"
    def field(fid, tc, eng):
        return (f'<div style="margin-bottom: 28px">\n<label for="{fid}" {label_style}>{tc} {en}{eng}</span></label>\n'
                f'<input class="fi" type="number" id="{fid}" min="0" max="10" step="1" inputmode="numeric" {input_style}>\n</div>')
    tpl = tpl[:j] + field("f-meat", "葷食人數", "NON-VEG") + "\n" + field("f-veg", "素食人數", "VEGETARIAN") + tpl[k:]
    enc = json.dumps(tpl, ensure_ascii=False).replace("</", "<\\u002F")
    s = s[:tm.start(2)] + enc + s[tm.end(2):]

# 9) 兒童椅獨立一整行，避免跟葷素欄位擠在一排、標題換行對不齊
tm = re.search(TPL_RE, s, re.S)
tpl = json.loads(tm.group(2))
i = tpl.find('<label for="f-chair"')
assert i > 0, "找不到兒童椅欄位"
j = tpl.rfind('<div style="margin-bottom: 28px', 0, i)
open_tag_end = tpl.find('>', j)
if 'grid-column' not in tpl[j:open_tag_end]:
    tpl = tpl[:j] + '<div style="margin-bottom: 28px; grid-column: 1 / -1">' + tpl[open_tag_end+1:]
# 葷素那一排固定兩欄（手機自動變一欄）
im = tpl.find('<label for="f-meat"')
g = tpl.rfind('<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(', 0, im)
assert g > 0
g_end = tpl.find('>', g)
tpl = tpl[:g] + '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); column-gap: 18px">' + tpl[g_end+1:]

# 10) 背景照片位置（先移除舊的再加，確保參數是最新）
tpl = re.sub(r'/\* photo-pos \*/.*?/\* /photo-pos \*/', '', tpl, flags=re.S)
css = ("/* photo-pos */"
       f".bg-sharp,.bg-blur{{background-position:{PHOTO_POS_X} center!important}}"
       "@media (min-aspect-ratio:1/1){"
       f".bg-sharp,.bg-blur{{background-position:{PHOTO_POS_X_WIDE} center!important}}"
       "}/* /photo-pos */")
k = tpl.find('.photo{background-image:url(')
assert k > 0
k_end = tpl.find('</style>', k)
tpl = tpl[:k_end] + css + "\n" + tpl[k_end:]
s = s[:tm.start(2)] + json.dumps(tpl, ensure_ascii=False).replace("</", "<\\u002F") + s[tm.end(2):]

# 檢查 template JSON 沒壞
json.loads(re.search(r'<script type="__bundler/template">\s*(.*?)\s*</script>', s, re.S).group(1))
open("index.html", "w", encoding="utf8", newline="").write(s)
print(f"完成：{src} → index.html")
