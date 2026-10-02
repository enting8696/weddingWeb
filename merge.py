# 用法：python merge.py
# 把 Claude Design 匯出的 HTML 補上以下設定，輸出成 index.html：
#   1. 手機 viewport + 分享預覽標籤        2. 高螢幕樣式只給桌機
#   3. 回函送到 Google 表單（rsvp_submit.js） 4. 社群 App 內引導外部瀏覽器（open_external.js）
#   5. 感謝文字依人數切換                   6. 飲食改成「葷食 / 素食人數」、兒童椅獨立一行
#   7. 背景婚紗照位置微調（只平移不放大）  8. 祝福欄灰色提示字
import re, json, glob, sys

# ===== 可調整的設定 =====
SITE        = "https://enting8696.github.io/weddingWeb/"
TITLE       = "Leo &amp; Julie 婚禮邀請函"
DESCRIPTION = "誠摯邀請與你分享喜悅"
IMAGE_URL   = "https://i.postimg.cc/GpmccCvQ/ting-en-ruo-wai-503.jpg"   # 分享縮圖（postimg 直接連結）
PHOTO_POS_X      = "47%"   # 背景照片位置（手機）：數字越小人物越往右，50% = 置中
PHOTO_POS_X_WIDE = "0%"    # 背景照片位置（電腦）：可移動空間有限，0% 已是最右
THANKS_COME = "期待與您在婚禮相見 ♡"          # 人數 > 0
THANKS_NOT  = "謝謝您的祝福，我們會想念您的 ♡"   # 人數 = 0
MSG_HINT    = "如果你有一些祝福的話不好意思當面說，就在這邊留言給我們吧!"   # 祝福欄的灰色提示字
# ========================

src = [f for f in glob.glob("*.html") if f != "index.html"]
if len(src) > 1:
    sys.exit(f"資料夾內只能有一個匯出的 HTML（不含 index.html），目前找到：{src}")
src = src[0] if src else "index.html"   # 沒有新匯出檔時，直接修補現有的 index.html
s = open(src, encoding="utf8", newline="").read()
nl = "\r\n" if "\r\n" in s[:500] else "\n"
VIEWPORT = "width=device-width, initial-scale=1, viewport-fit=cover"

def embed(s, fname):
    """把 js 檔貼進 </title> 後面；已貼過的舊版本先移除"""
    js = open(fname, encoding="utf8").read()
    first = js.strip().splitlines()[0]
    s = re.sub(r"\s*<script>\s*" + re.escape(first) + r".*?</script>", "", s, flags=re.S)
    return s.replace("</title>", "</title>" + nl + "  <script>" + nl + js + nl + "  </script>", 1)

# 1) 外層 head：viewport + 分享預覽（每次都重寫，改設定就會生效）
s = re.sub(r'\s*<meta (?:name="(?:viewport|description|twitter:card)"|property="og:[^"]*")[^>]*>', "", s)
META = [
    f'<meta name="viewport" content="{VIEWPORT}">',
    f'<meta name="description" content="{DESCRIPTION}">',
    '<meta property="og:type" content="website">',
    f'<meta property="og:url" content="{SITE}">',
    f'<meta property="og:title" content="{TITLE}">',
    f'<meta property="og:description" content="{DESCRIPTION}">',
    f'<meta property="og:image" content="{IMAGE_URL}">',
    '<meta name="twitter:card" content="summary_large_image">',
]
a = '<meta charset="utf-8">'
assert s.count(a) == 1, "找不到外層 <meta charset>"
s = s.replace(a, a + "".join(nl + "  " + m for m in META), 1)

# 2) 內層 template：viewport、高螢幕樣式只給桌機
vp = f'<meta name=\\"viewport\\" content=\\"{VIEWPORT}\\">'
if vp not in s:
    b = '<meta charset=\\"utf-8\\">'
    assert s.count(b) == 1, "找不到內層 template 的 <meta charset>"
    s = s.replace(b, b + vp, 1)
s = s.replace("@media (min-height:1400px){", "@media (min-height:1400px) and (min-width:1024px){")

# 3) 回函送到 Google 表單、4) 社群 App 引導外部瀏覽器
OLD_SEND = "send: () => this.setState({ sent: true })"
if OLD_SEND in s:
    s = s.replace(OLD_SEND, "send: () => window.__weddingSubmit(() => this.setState({ sent: true }))", 1)
assert "window.__weddingSubmit(" in s, "找不到回函的 send 函式，設計稿結構可能改了"
s = embed(s, "rsvp_submit.js")
s = embed(s, "open_external.js")

# 5) 感謝文字依人數切換
s = s.replace("已收到您的回覆，<br>期待與您在婚禮相見 ♡", "{{ thx1 }}<br>{{ thx2 }}", 1)
s = re.sub(r" thx1: '[^']*', thx2: \(Number\.isFinite\(n\) && n > 0 \? '[^']*' : '[^']*'\),", "", s)   # 移除舊的再加，文字改了才會生效
P = "p: this.state.p.toFixed(3),"
assert s.count(P) == 1, "找不到 renderVals，設計稿結構可能改了"
s = s.replace(P, P + f" thx1: '已收到您的回覆，', thx2: (Number.isFinite(n) && n > 0 ? '{THANKS_COME}' : '{THANKS_NOT}'),", 1)

# 6)、7) 需要改 template 內容：解開 → 修改 → 包回去
TPL_RE = r'(<script type="__bundler/template">\s*)(.*?)(\s*</script>)'
tm = re.search(TPL_RE, s, re.S)
tpl = json.loads(tm.group(2))

# 6a) 飲食需求下拉 → 葷食人數 / 素食人數
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

# 6b) 葷素一排兩欄（手機一欄），兒童椅獨立一整行
g = tpl.rfind('<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(', 0, tpl.find('<label for="f-meat"'))
assert g > 0, "找不到葷素欄位外框"
tpl = tpl[:g] + '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); column-gap: 18px">' + tpl[tpl.find('>', g) + 1:]
j = tpl.rfind('<div style="margin-bottom: 28px', 0, tpl.find('<label for="f-chair"'))
assert j > 0, "找不到兒童椅欄位"
tpl = tpl[:j] + '<div style="margin-bottom: 28px; grid-column: 1 / -1">' + tpl[tpl.find('>', j) + 1:]

# 7) 背景照片位置（移除舊的再加）
tpl = re.sub(r'/\* photo-pos \*/.*?/\* /photo-pos \*/\n?', '', tpl, flags=re.S)
css = ("/* photo-pos */"
       f".bg-sharp,.bg-blur{{background-position:{PHOTO_POS_X} center!important}}"
       f"@media (min-aspect-ratio:1/1){{.bg-sharp,.bg-blur{{background-position:{PHOTO_POS_X_WIDE} center!important}}}}"
       "/* /photo-pos */\n")
k = tpl.find('</style>', tpl.find('.photo{background-image:url('))
assert k > 0, "找不到背景照片樣式"
tpl = tpl[:k] + css + tpl[k:]

# 8) 祝福欄提示字：點進去就消失，清空後點別處會再出現
i = tpl.find('<textarea class="fi" id="f-msg"')
assert i > 0, "找不到祝福欄位"
tag_end = tpl.find('>', i)
tag = re.sub(r' placeholder="[^"]*"', '', tpl[i:tag_end])
tpl = tpl[:i] + tag + f' placeholder="{MSG_HINT}"' + tpl[tag_end:]
tpl = re.sub(r'/\* msg-hint \*/.*?/\* /msg-hint \*/\n?', '', tpl, flags=re.S)
k = tpl.find('</style>', tpl.find('.photo{background-image:url('))
tpl = tpl[:k] + ("/* msg-hint */#f-msg::placeholder{color:rgba(255,255,255,.45);font-size:.85rem;letter-spacing:.06em;line-height:1.7}"
                 "#f-msg:focus::placeholder{color:transparent}/* /msg-hint */\n") + tpl[k:]

s = s[:tm.start(2)] + json.dumps(tpl, ensure_ascii=False).replace("</", "<\\u002F") + s[tm.end(2):]
open("index.html", "w", encoding="utf8", newline="").write(s)
print(f"完成：{src} → index.html")
