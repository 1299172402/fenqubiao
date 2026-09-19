# 期刊分区表升级版 · 离线镜像

把 `advanced.fenqubiao.com`（中科院期刊分区表升级版，2025 年）抓下来的 **278 份 MHTML 快照**
转换成可托管在 GitHub Pages 的静态站点，并保留原始 MHTML 供核对。

线上站点：https://1299172402.github.io/fenqubiao/

## 两条路线（方案 A：并存）

| | 转换版 | 原档 |
|---|---|---|
| 路径 | `docs/index.html`、`docs/macro/*.html`、`docs/meso/*.html` | `docs/raw/**/*.mhtml` |
| 生成方式 | Python 离线解码 MHTML → 真 HTML | 原封不动复制 |
| 站点内跳转 | 普通 `<a href>`，**不需要 JS** | 后端无 JS 可用，需开 viewer |
| 浏览入口 | 直接打开 | `docs/viewer.html?f=raw/macro/化学.mhtml` |
| 双向切换 | 右下角悬浮「原始 MHTML」→ viewer | 顶栏「转换版」→ 对应 HTML |
| 体积 | 18 MB | 112 MB |

原始 MHTML 不能直接当网页用：它是 `multipart/related` 邮件格式，浏览器只在 `file://`
下渲染，通过 http(s) 取回会被当成下载。所以原档统一走 `viewer.html`
（本地化引用了 [mhtml2html](https://github.com/msindwan/mhtml2html)，把 `cid:` 资源内联成
`data:` URL，再把站内链接改写成本站的 `raw/` 路径）。

## 构建

```powershell
python build_site.py            # 构建到 docs/（含原始 MHTML 副本）
python build_site.py --clean    # 先清空 docs/ 再构建
python build_site.py --no-raw   # 只出转换版，不复制 raw/（体积 18MB）
```

本地预览（**必须走 HTTP**，`file://` 下 viewer 的 fetch 会被浏览器拦掉）：

```powershell
cd docs
python -m http.server 8899
# 然后打开 http://127.0.0.1:8899/
```

## 发布到 GitHub Pages

1. 提交并推送 `docs/`：

   ```powershell
   git add docs build_site.py site_src README.md
   git commit -m "feat(站点): 生成 GitHub Pages 静态镜像（转换版 + 原始 MHTML 预览）"
   git push
   ```

2. 仓库 **Settings → Pages**：
   - Source: `Deploy from a branch`
   - Branch: `main`，目录选 **`/docs`**
   - 保存，等 1~2 分钟，访问 `https://<用户名>.github.io/fenqubiao/`

`docs/.nojekyll` 已生成，避免 Jekyll 处理下划线开头的资源文件。

> 注意：`docs/` 约 130 MB。GitHub Pages 单站上限 1 GB，没问题；但仓库总体积会到
> 250 MB 左右（`mhtml/` 另占 112 MB），首次 clone 会偏慢。如果介意，可以用
> `--no-raw` 只发转换版。

## 产物结构

```
docs/
├── index.html            主页：大类学科索引 + 三个入口按钮
├── megajournal.html      Mega-Journal 列表
├── viewer.html           原始 MHTML 预览器
├── macro/<大类名>.html   21 个大类期刊列表
├── meso/index.html       小类学科目录（254 个链接）
├── meso/<两字母代码>.html 254 个小类期刊列表
├── raw/**/*.mhtml        原始快照（viewer 加载）
├── assets/*.css          去重后的样式表（3 个）
├── assets/vendor/        mhtml2html.js
└── .nojekyll
```

## 抓取 / 抓取辅助脚本（历史）

| 脚本 | 作用 |
|---|---|
| `main.py` | 纯 `requests` 试探接口（拿不到分区，已弃用） |
| `save_server.py` | 本地落盘服务，配合浏览器 CDP 截 MHTML |
| `json2csv.py` | 从工具落盘的 `content.txt` 里解析 JSON 转 CSV |
| `normalize.py` | 统一小类文件名，报告缺失清单 |
| `verify_mhtml.py` | 校验每份 MHTML 的期刊数 / 分区数 |

## 数据说明

- 年份 **2025**，共 21 个大类、254 个小类。
- 分区号不在可见文本里，在 `<span class="class" data-attr="3">` 的 `data-attr` 中；
  页面上看到的「区」字是 CSS 加的。
- 期刊详情链接仍指向官网（本地没有详情页数据）。
- 微信 / 石墨表单等外链保持原样。
