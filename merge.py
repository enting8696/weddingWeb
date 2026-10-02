# 用法：python merge.py
# 把 Claude Design 匯出的 HTML 補上以下設定，輸出成 index.html：
#   1. 手機 viewport   2. 分享預覽標籤   3. 高螢幕樣式只給桌機
#   4. 回函送到 Google 表單（需要 rsvp_submit.js）
#   5. 社群 App 內引導外部瀏覽器（需要 open_external.js）
import re, json, glob, sys

src = [f for f in glob.glob("*.html") if f != "index.html"]
if len(src) > 1:
    sys.exit(f"資料夾內只能有一個匯出的 HTML（不含 index.html），目前找到：{src}")
src = src[0] if src else "index.html"   # 沒有新匯出檔時，直接修補現有的 index.html
s = open(src, encoding="utf8", newline="").read()
nl = "\r\n" if "\r\n" in s[:500] else "\n"

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
if "__weddingSubmit = function" not in s:
    js = open("rsvp_submit.js", encoding="utf8").read()
    a = "</title>"
    assert s.count(a) >= 1
    s = s.replace(a, a + nl + "  <script>" + nl + js + nl + "  </script>", 1)

# 5) 社群 App 內開啟 → 引導外部瀏覽器（放在最前面，越早執行越好）
if "__openExternal" not in s:
    js = open("open_external.js", encoding="utf8").read()
    a = "</title>"
    s = s.replace(a, a + nl + "  <script>" + nl + js + nl + "  </script>", 1)

# 檢查 template JSON 沒壞
json.loads(re.search(r'<script type="__bundler/template">\s*(.*?)\s*</script>', s, re.S).group(1))
open("index.html", "w", encoding="utf8", newline="").write(s)
print(f"完成：{src} → index.html")
