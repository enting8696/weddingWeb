# 用法：python merge.py
# 把 Claude Design 匯出的 HTML 加上手機 viewport 與分享預覽標籤，輸出成 index.html
import re, json, glob, sys

src = [f for f in glob.glob("*.html") if f != "index.html"]
if len(src) != 1:
    sys.exit(f"資料夾內要剛好一個匯出的 HTML（不含 index.html），目前找到：{src}")
src = src[0]
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

# 檢查 template JSON 沒壞
json.loads(re.search(r'<script type="__bundler/template">\s*(.*?)\s*</script>', s, re.S).group(1))
open("index.html", "w", encoding="utf8", newline="").write(s)
print(f"完成：{src} → index.html")
