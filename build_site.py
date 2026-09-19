"""把 mhtml/ 下的 MHTML 快照转换成可托管在 GitHub Pages 的静态站点。

用法:
    python build_site.py            # 构建（含原始 MHTML 副本）
    python build_site.py --no-raw   # 不复制原始 MHTML
    python build_site.py --clean    # 先清空 docs/ 再构建

产物 (docs/):
    index.html            主页 = 大类学科索引 + 三个入口按钮
    megajournal.html      Mega-Journal 列表
    meso/index.html       小类学科索引 (254 个链接)
    macro/<大类名>.html   21 个大类期刊列表
    meso/<代码>.html      254 个小类期刊列表
    viewer.html           MHTML 预览器（方案 A）
    raw/**/*.mhtml        原始 MHTML 快照（方案 A，供 viewer 加载）
    assets/*.css          去重后的样式表
    assets/vendor/*.js    第三方库（mhtml2html）
    .nojekyll             禁用 Jekyll，避免下划线文件被吞
"""

import email
import hashlib
import html as htmllib
import os
import posixpath
import re
import shutil
import sys
from urllib.parse import parse_qs, parse_qsl, quote, urljoin, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "mhtml")
SITE_SRC = os.path.join(ROOT, "site_src")
OUT = os.path.join(ROOT, "docs")
ASSETS_REL = "assets"

SITE_HOST = "advanced.fenqubiao.com"

# 主页三个文件 -> 输出路径
HOME_PAGES = {
    "期刊分区表升级版 - 大类学科.mhtml": "index.html",
    "小类学科 - 期刊分区表升级版.mhtml": "meso/index.html",
    "Mega-Journal 列表 - 期刊分区表升级版.mhtml": "megajournal.html",
}

# 主页三个文件 -> 原始 MHTML 副本路径（viewer 靠这套命名定位）
HOME_RAW = {
    "期刊分区表升级版 - 大类学科.mhtml": "raw/home_macro.mhtml",
    "小类学科 - 期刊分区表升级版.mhtml": "raw/home_meso.mhtml",
    "Mega-Journal 列表 - 期刊分区表升级版.mhtml": "raw/home_megaj.mhtml",
}

# 需要拷进 docs/ 的静态源文件: (site_src 内相对路径, docs 内相对路径)
STATIC_FILES = [
    ("viewer.html", "viewer.html"),
    ("vendor/mhtml2html.js", "assets/vendor/mhtml2html.js"),
]

MACRO_SUFFIX = " - 期刊分区表升级版.mhtml"

COPY_RAW = True

EXT_BY_TYPE = {
    "text/css": ".css",
    "text/javascript": ".js",
    "application/javascript": ".js",
    "application/x-javascript": ".js",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
    "image/x-icon": ".ico",
    "image/vnd.microsoft.icon": ".ico",
    "font/woff": ".woff",
    "font/woff2": ".woff2",
    "application/font-woff": ".woff",
    "application/x-font-woff": ".woff",
    "font/ttf": ".ttf",
    "application/octet-stream": ".bin",
    "text/html": ".html",
}


# --------------------------------------------------------------------------- #
# 工具
# --------------------------------------------------------------------------- #
def log(msg):
    print(msg)


def decode_mhtml(path):
    """返回 (html文本, [资源分片])；资源分片 = dict(type, loc, data)。"""
    with open(path, "rb") as f:
        msg = email.message_from_binary_file(f)

    html = None
    resources = []
    for part in msg.walk():
        ct = part.get_content_type()
        if ct.startswith("multipart/"):
            continue
        loc = part.get("Content-Location") or ""
        if ct == "text/html" and html is None:
            payload = part.get_payload(decode=True) or b""
            html = payload.decode("utf-8", "replace")
        else:
            resources.append(
                {"type": ct, "loc": loc, "data": part.get_payload(decode=True) or b""}
            )
    return html or "", resources


def asset_key(url):
    """资源去重键：忽略 http/https 差异，只比 host + path + query。"""
    p = urlparse(url)
    return (
        p.netloc.lower(),
        p.path,
        tuple(sorted(parse_qsl(p.query, keep_blank_values=True))),
    )


def relurl(page_dir, target):
    """把站点根相对路径 target 转成相对于 page_dir 的 URL（含中文百分号编码）。"""
    base = page_dir if page_dir else "."
    rel = posixpath.relpath(target, base)
    return quote(rel, safe="/")


def absolutize_css(text, base_url):
    """把 CSS 里的相对 url(...) 改写成原站绝对地址，保证字体/图标仍能加载。"""

    def repl(m):
        raw = m.group(1).strip()
        if raw[:1] in ("'", '"'):
            raw = raw[1:]
        if raw[-1:] in ("'", '"'):
            raw = raw[:-1]
        s = raw.strip()
        if not s or s.startswith(("data:", "http://", "https://", "//", "#")):
            return "url(%s)" % raw
        return "url(%s)" % urljoin(base_url, s)

    return re.sub(r"url\(([^)]*)\)", repl, text)


# 右下角“看原档”胶囊按钮
RAW_PILL = (
    '<a href="{href}" title="查看存在本站的原始 MHTML 快照" style="'
    "position:fixed;right:14px;bottom:14px;z-index:2147483646;"
    "padding:7px 14px;border-radius:999px;background:#3c8dbc;color:#fff;"
    "font:13px/1.4 -apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',sans-serif;"
    'text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,.25)">原始 MHTML</a>'
)


def copy_raw(src_path, raw_rel):
    """原封不动复制一份 MHTML 到 docs/raw/ 下。"""
    dst = os.path.join(OUT, raw_rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src_path, dst)


def inject_raw_link(html, page_dir, raw_rel):
    """在页面右下角挂一个指向 viewer 的入口。"""
    href = "%s?f=%s" % (relurl(page_dir, "viewer.html"), quote(raw_rel, safe="/"))
    pill = RAW_PILL.format(href=href)
    if "</body>" in html:
        return html.replace("</body>", pill + "\n</body>", 1)
    return html + pill


# --------------------------------------------------------------------------- #
# 构建映射
# --------------------------------------------------------------------------- #
def build_maps():
    """返回 macro_map(中文名->输出路径), meso_map(代码->输出路径), 源文件清单。"""
    macro_map = {}
    macro_files = []
    for name in sorted(os.listdir(os.path.join(SRC, "大类"))):
        if not name.endswith(".mhtml"):
            continue
        cn = name[: -len(MACRO_SUFFIX)] if name.endswith(MACRO_SUFFIX) else name[:-6]
        macro_map[cn] = "macro/%s.html" % cn
        macro_files.append(os.path.join(SRC, "大类", name))

    meso_map = {}
    meso_files = []
    for name in sorted(os.listdir(os.path.join(SRC, "小类"))):
        if not name.endswith(".mhtml"):
            continue
        m = re.match(r"^小类_([A-Z]{2})_", name)
        if not m:
            log("  [警告] 无法识别小类文件名: %s" % name)
            continue
        code = m.group(1)
        meso_map[code] = "meso/%s.html" % code
        meso_files.append(os.path.join(SRC, "小类", name))

    home_files = []
    for name, dst in HOME_PAGES.items():
        p = os.path.join(SRC, "主页", name)
        if os.path.exists(p):
            home_files.append((p, dst))
        else:
            log("  [警告] 缺少主页文件: %s" % name)

    return macro_map, meso_map, macro_files, meso_files, home_files


# --------------------------------------------------------------------------- #
# 链接改写
# --------------------------------------------------------------------------- #
def rewrite_page_url(u, page_dir, macro_map, meso_map):
    """把指向原站、且本地有对应页面的 URL 改成站内相对链接；其余原样返回。"""
    if not u.startswith(("http://", "https://")):
        return u
    p = urlparse(u)
    if p.netloc.lower() != SITE_HOST:
        return u

    path = p.path
    low = path.lower()
    try:
        # href 里可能带 &amp; 等实体，先还原再解析参数
        qs = parse_qs(htmllib.unescape(p.query))
    except Exception:
        qs = {}
    name = (qs.get("name") or [None])[0]
    year = (qs.get("year") or [None])[0]

    if low.startswith("/macro/journal"):
        if name in macro_map and year in (None, "2025"):
            return relurl(page_dir, macro_map[name])
    elif low.startswith("/meso/journal"):
        if name in meso_map and year in (None, "2025"):
            return relurl(page_dir, meso_map[name])
    elif low.startswith("/meso/index"):
        return relurl(page_dir, "meso/index.html")
    elif low.startswith("/megaj/index"):
        return relurl(page_dir, "megajournal.html")
    elif low.startswith("/macro/index"):
        return relurl(page_dir, "index.html")
    elif path in ("", "/"):
        return relurl(page_dir, "index.html")
    return u


def rewrite_html(
    html, page_dir, resolve_asset, cid_styles, macro_map, meso_map, warnings, page_label
):
    # 1) 去掉浏览器扩展注入的样式（chrome-extension://），网页上无意义
    html, n = re.subn(r'<link[^>]*href="chrome-extension://[^"]*"[^>]*/?>', "", html)
    html, n2 = re.subn(
        r'<script[^>]*src="chrome-extension://[^"]*"[^>]*>\s*</script>', "", html
    )
    if n or n2:
        warnings.append("%s: 移除 %d 个扩展样式/脚本" % (page_label, n + n2))

    # 2) 把 <link href="cid:..."> 还原成内联 <style>（Chromium 把内联样式拆成了分片）
    def inline_cid(m):
        href = m.group("href")
        if href in cid_styles:
            return "<style>\n%s\n</style>" % cid_styles[href]
        return ""

    html, n = re.subn(r'<link[^>]*href="(?P<href>cid:[^"]+)"[^>]*/?>', inline_cid, html)
    if n:
        warnings.append("%s: 内联 %d 个 cid 样式" % (page_label, n))

    # 3) 样式表 / 图片等资源 -> assets/xxx
    def fix_asset(m):
        attr, url = m.group(1), m.group(2)
        target = resolve_asset(url)
        if target:
            return '%s="%s"' % (attr, relurl(page_dir, target))
        return m.group(0)

    html = re.sub(r'\b(href|src)="(https?://[^"]+)"', fix_asset, html)

    # 4) <a> 标签：改站内链接 + 去掉 target="_blank"
    def fix_anchor(m):
        tag = m.group(0)
        hm = re.search(r'href="([^"]*)"', tag)
        if not hm:
            return tag
        old = hm.group(1)
        new = rewrite_page_url(old, page_dir, macro_map, meso_map)
        if new != old:
            tag = tag.replace('href="%s"' % old, 'href="%s"' % new, 1)
        if not new.startswith(("http://", "https://", "//")):
            tag = re.sub(r'\s+target="_blank"', "", tag)
            tag = re.sub(r'\s+rel="noopener[^"]*"', "", tag)
        return tag

    html = re.sub(r"<a\b[^>]*>", fix_anchor, html)

    # 5) “大类学科”按钮（原站点里是 <button>，没有 href）改成指向主页的链接
    index_href = relurl(page_dir, "index.html")

    def fix_button(m):
        attrs = m.group(1)
        attrs = re.sub(r'\s*type="button"', "", attrs)
        return '<a%s href="%s">大类学科</a>' % (attrs, index_href)

    html = re.sub(
        r'<button([^>]*\bclass="btn[^"]*"[^>]*)>\s*大类学科\s*</button>',
        fix_button,
        html,
    )

    return html


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def main():
    global COPY_RAW
    if "--no-raw" in sys.argv:
        COPY_RAW = False
    if "--clean" in sys.argv and os.path.isdir(OUT):
        shutil.rmtree(OUT)
        log("已清空 docs/")

    macro_map, meso_map, macro_files, meso_files, home_files = build_maps()
    log("大类映射: %d 个" % len(macro_map))
    log("小类映射: %d 个" % len(meso_map))
    log("原始 MHTML 副本: %s" % ("开" if COPY_RAW else "关"))

    os.makedirs(os.path.join(OUT, ASSETS_REL), exist_ok=True)
    # .nojekyll：否则 Jekyll 会忽略 assets 里以 _ 开头的文件
    with open(os.path.join(OUT, ".nojekyll"), "w") as f:
        f.write("")

    # 拷贝 viewer 与第三方库
    for src_rel, out_rel in STATIC_FILES:
        s = os.path.join(SITE_SRC, src_rel.replace("/", os.sep))
        if not os.path.exists(s):
            log("  [警告] 缺少静态文件: %s" % s)
            continue
        d = os.path.join(OUT, out_rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copyfile(s, d)
    log("已拷贝静态文件: %d 个" % len(STATIC_FILES))

    saved_assets = {}  # asset_key -> 输出相对路径
    warnings = []

    def process(src_path, out_rel, page_label, raw_rel=None):
        html, resources = decode_mhtml(src_path)
        page_dir = posixpath.dirname(out_rel) or "."
        cid_styles = {}
        local_assets = {}  # asset_key -> 输出相对路径（本页副本，兜底用）

        for r in resources:
            loc = r["loc"]
            if not loc:
                continue
            if loc.startswith("chrome-extension:"):
                continue
            if loc.startswith("cid:"):
                if r["type"] == "text/css":
                    cid_styles[loc] = r["data"].decode("utf-8", "replace")
                continue
            if not loc.startswith(("http://", "https://")):
                continue

            key = asset_key(loc)
            if key not in saved_assets:
                ext = EXT_BY_TYPE.get(r["type"], ".bin")
                fname = hashlib.sha1(repr(key).encode("utf-8")).hexdigest()[:16] + ext
                out_rel_asset = "%s/%s" % (ASSETS_REL, fname)
                data = r["data"]
                if r["type"] == "text/css":
                    text = data.decode("utf-8", "replace")
                    p = urlparse(loc)
                    base = "%s://%s%s" % (p.scheme, p.netloc, p.path)
                    text = absolutize_css(text, base)
                    data = text.encode("utf-8")
                with open(os.path.join(OUT, ASSETS_REL, fname), "wb") as f:
                    f.write(data)
                saved_assets[key] = out_rel_asset
            local_assets[key] = saved_assets[key]

        def resolve_asset(url):
            """按规范化键查表，忽略 http/https 写法差异。"""
            return local_assets.get(asset_key(url))

        html = rewrite_html(
            html,
            page_dir,
            resolve_asset,
            cid_styles,
            macro_map,
            meso_map,
            warnings,
            page_label,
        )

        # 方案 A：保留原档 + 右下角入口
        if raw_rel and COPY_RAW:
            copy_raw(src_path, raw_rel)
            html = inject_raw_link(html, page_dir, raw_rel)

        dst = os.path.join(OUT, out_rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)

        rows = len(re.findall(r"<span class=\"class\"", html))
        return rows

    total_rows = 0
    counts = []

    for src_path, out_rel in home_files:
        label = os.path.basename(src_path)
        rows = process(src_path, out_rel, label, HOME_RAW.get(label))
        counts.append((out_rel, rows, os.path.getsize(src_path)))
        total_rows += rows

    for src_path in macro_files:
        cn = os.path.basename(src_path)[: -len(MACRO_SUFFIX)]
        rows = process(
            src_path,
            macro_map[cn],
            os.path.basename(src_path),
            "raw/macro/%s.mhtml" % cn,
        )
        counts.append((macro_map[cn], rows, os.path.getsize(src_path)))
        total_rows += rows

    for src_path in meso_files:
        code = re.match(r"^小类_([A-Z]{2})_", os.path.basename(src_path)).group(1)
        rows = process(
            src_path,
            meso_map[code],
            os.path.basename(src_path),
            "raw/meso/%s.mhtml" % code,
        )
        counts.append((meso_map[code], rows, os.path.getsize(src_path)))
        total_rows += rows

    log("")
    log("=" * 60)
    log(
        "生成页面: %d   去重资源: %d   分区单元格总数: %d"
        % (len(counts), len(saved_assets), total_rows)
    )
    empty = [c for c in counts if c[1] == 0]
    if empty:
        log("⚠️  以下页面没有分区数据（可能未展开）:")
        for c in empty[:20]:
            log("   %s" % c[0])
    if warnings:
        log("提示 (%d 条，仅显示前 10):" % len(warnings))
        for w in warnings[:10]:
            log("   %s" % w)

    # 体积统计（按子目录拆分，方便判断 raw/ 占了多少）
    def dir_size(path):
        n = 0
        for dirpath, _, files in os.walk(path):
            for fn in files:
                n += os.path.getsize(os.path.join(dirpath, fn))
        return n

    total = dir_size(OUT)
    log("体积明细:")
    for sub in ("macro", "meso", "raw", ASSETS_REL):
        p = os.path.join(OUT, sub)
        if os.path.isdir(p):
            log("   %-8s %7.1f MB" % (sub + "/", dir_size(p) / 1024 / 1024))
    top = dir_size(OUT) - sum(
        dir_size(os.path.join(OUT, s))
        for s in ("macro", "meso", "raw", ASSETS_REL)
        if os.path.isdir(os.path.join(OUT, s))
    )
    log("   %-8s %7.1f MB" % ("(根)", top / 1024 / 1024))
    log("docs/ 总体积: %.1f MB" % (total / 1024 / 1024))


if __name__ == "__main__":
    main()
