---
name: blog-to-elementor-pipeline
description: "Verified end-to-end pipeline for replicating a user-supplied blog article (saved HTML from any local folder, attached directly in chat or given by absolute path) into a hand-editable WordPress POST built with Elementor: parse the article including title/excerpt/date/categories/tags/featured image, resolve images from external URLs / companion _files / data URIs, upload them into the media library via Elementor MCP tokens, create the document with post_type=post, build native atomic elements with three-device responsive breakpoints inline, write post metadata (including excerpt) via REST, publish, and verify with real browser measurements. Use when replicating blog articles into posts, switching the target WordPress site, or auditing responsive output."
---

# 博客文章 → WordPress 文章（post）· 可编辑响应式流水线手册

> 本手册继承自 2026-11-23 在 `testdecor` 上**实跑验证**的网页复刻流水线，并针对"产出为文章（post）"做了扩展。凡标「实测」的结论都有状态码、像素值或截图佐证；标「坑」的是踩过并已定位根因的陷阱。

## 0. 这套流水线解决什么

用户给一篇/几篇博客文章的网页文件 → 每篇变成一个独立的 **WordPress 文章（post，不是 page）** → 文章标题/摘要/日期/分类/标签/特色图一起还原 → 图片进媒体库 → 正文从第一版就适配电脑/平板/手机 → 文章在 Elementor 编辑器里能逐层点开改。

**六条铁律**
1. 源文章由用户提供，不自己去公网找。
2. **不挑存放目录**：用户下载/保存到自己任意目录都行，直接把 `.html` 发进对话或给完整路径（zip/rar 整包也行，我自行解压），绝不要求挪进 `captured/` 等指定目录。
3. **产出必须是 post，不是 page**：建文档一律 `elementor/create-page` + `post_type:"post"`（2026-11-23 实测返回 `type:"post"`）。建成页面即算失败。
4. **布局忠实原版（用户硬要求，最高优先级）**：内容可以差一点，但布局必须尽量和原版一致——分栏、区块顺序、图片尺寸/比例、卡片列数、标题层级都贴合原版。用户要在原版式样基础上手改，布局一变就没法改。任何布局决策来自真实渲染+像素测量，不靠猜。见 `references/layout-fidelity.md`。
5. 响应式在建文章时一次写入，不留「事后调整」步骤。
6. 正文必须是 Elementor 原生可编辑元素，不是纯代码页、不是 3.x JSON 盲写。

## 1. 输入通道

用户把博客文章网页保存下来 → 把文件给我，且**用户爱存哪存哪**：

| 通道 | 适用 | 产出 | 结论 |
|---|---|---|---|
| **用户把下载的 `.html` 直接发进对话**（或给出任意本地绝对路径） | **默认且推荐**，含受验证墙保护的站点 | 完整 HTML；图片按来源分别取 | ✅ 一个文件即可开工、绕开验证墙；**不要求任何指定目录** |
| 用户 `Ctrl+S`「网页，全部」→ `.html` + 同名 `_files`，或打包成 zip/rar | 图片实体最齐的场景 | 完整 HTML、CSS、图片 | ✅ 我自行解压；`_files` 一起发来或给路径即可，仍不用挪目录 |
| 内置浏览器 / WebFetch | 无防护站点、快速取文案 | 精简 DOM / markdown | ⚠️ 拿不到 CSS 与图片 URL，不能单独支撑建文章 |
| `curl` / Node 直连 | 公网普通站点 | 原始 HTML | ⚠️ 沙箱代理常拦成 HTTP 000 / 超时 |

**给用户的话术（别说「丢进 captured/」这类黑话，也别指定目录）**：
> 文章网页你想保存到哪个目录都行，桌面、下载文件夹、D 盘都可以，不用管我。存好之后直接把那个 `.html` 文件在这条对话里发给我（或者把完整路径告诉我），我就能接着做。一次发几篇都行。如果保存时还多出来一个同名 `_files` 文件夹，一起发我或告诉我路径（图片实体在里面）；只发 HTML 也行，我先自检，真缺图片实体时才找你补要，不会让你为此整理目录。

### 收到文件后的输入自检

定位用户发来的 `.html` —— 对话附件、任意本地绝对路径，或 zip/rar 压缩包（先解压）。扫描 `<img src>` / `srcset` / CSS `url()`：

| 图片来源形态 | 处理方式 |
|---|---|
| 绝对外链 `http(s)://...` | 直接下载到本地（代理/超时按第 7 节处理） |
| 相对路径 `xxx_files/foo.png` | 在该 HTML **同目录**的同名 `_files` 里找实体；**必须先做 HTML 实体解码**（`html.unescape`）：src 里的 `&` 存的是 `&amp;`，不解码会 0 命中 |
| `data:` / base64 内联 | 直接解码落盘 |
| zip / rar 整包 | 先解压（WinRAR：`C:\Program Files\WinRAR\UnRAR.exe x ...`），再按上述规则处理 |
| 相对路径**且 `_files` 实体确实拿不到** | 一次性请用户把那个 `_files` 文件夹发来或告知路径；**不得**要求用户整理目录或挪文件，也不把它设为前置条件 |

## 2. 解析文章网页

- 先做第 1 节的输入自检，图片来源判定完成后再解析 DOM。
- **先还原原版真实布局（强制）**：把 HTML 去掉脚本做成静态副本、图片指向已上传的本站附件、放站点根用 `http://` 打开并截图；注入测量脚本读每个标题/图片/区块的真实像素尺寸（内容宽度、字号、图片固定尺寸、区块顺序）。这是建文章正文的唯一布局依据。**方法与实测尺寸基线见 `references/layout-fidelity.md`。**
- 文章专属字段的解析（**本专家新增，详见 `references/post-fields.md`**）：
  - **标题**：`<h1>` 或 `<meta property="og:title">` 或 JSON-LD `Article.headline`；
  - **摘要**：`<meta name="description">` → `og:description` → JSON-LD `description`；写进 WordPress `excerpt`（编辑器侧栏 `Add an excerpt...`），纯文本、不臆造；实测可写，写法见 `references/post-fields.md`；
  - **发布日期**：`<time datetime>`、JSON-LD `datePublished`、或页面可见日期（如 `Nov.20 2026` → `2026-11-20`）；
  - **分类**：面包屑中间层（如 `Home / Company News / <标题>` → 分类 `Company News`）、或页面栏目标签；
  - **标签**：页面 tags 区、关键词 meta；
  - **特色图片**：`<meta property="og:image">` 或正文首张大图。
- 只取正文主体：`<main>` / `<article>` 容器，**排除**页眉、页脚、"相关文章/最新文章"列表、全局联系表单、导航、Cookie 提示。
- 按 DOM 顺序记录：主标题、小标题（`<h2>/<h3>`）、正文段落、图片、列表……直到正文结尾。
- 文案按源语言逐字保留（通常英文），不改、不翻译、不润色。**但与布局冲突时优先保布局**。
- **图片尺寸用实测固定值**，不要一概 `width:100%` 撑满；标题层级、区块顺序严格对齐测量数据。

## 3. 图片上传媒体库

用 Elementor MCP：

1. `elementor/request-media-upload` 为每张图申请一次性 token。
2. `curl --noproxy '*' -X POST` 把本地图片传到
   `http://<站点>/index.php?rest_route=/elementor/v1/mcp-media-upload`
   带上 `X-Elementor-Mcp-Upload-Token` / `Filename` / `Title` 头。
3. 确认 **HTTP 201**，记录返回的附件 ID 与 URL。
4. WordPress 会自动生成响应式缩略图，前台 `srcset` 自动生效。

**环境坑**
- Windows 的 `curl` 不认 Git Bash 的 `/e/...` 路径，传 Windows 路径。
- 本地站点必须加 `--noproxy '*'`，否则被沙箱代理拦成 HTTP 000。
- 非 HTTPS 本地站若提示 Application Password 不可用，在 `wp-config.php` 加 `define('WP_ENVIRONMENT_TYPE','local')`。

## 4. 建文章：post_type=post + 原生元素 + 响应式一次写入

**4.1 先建文章壳（本专家核心差异）**

```
elementor/create-page  {
  "title": "<文章标题>",
  "post_type": "post",          ← 关键：必须是 post，不能是 page
  "template": "elementor_canvas"
}
```
- 2026-11-23 实测：传 `post_type:"post"` 返回 `id` / `type:"post"` / `status:"draft"` / `edit_url`。**建成后务必核对返回的 `type` 是 `post`。**
- `elementor_canvas` 让主题页眉页脚与主题标题都不渲染，正文完全由元素树控制；若用户要保留主题文章头图/面包屑，改用 `elementor_theme` 并相应少建标题。
- 记下返回的 `id`（post ID）——后续 build-composition 的 `post_id`、元数据写入、发布都用这一个 ID。

**4.2 搭正文结构**

用 `elementor/build-composition`（`post_id` = 文章 ID），不要用 `html2elementor`（产出 3.x 容器 JSON，本站 V4 Atomic Editor 兼容性未验证）。

结构形状：
```xml
<e-flexbox configuration-id="文章主体">
  <e-div-block configuration-id="内容容器">
    <e-heading configuration-id="文章标题"></e-heading>
    <e-paragraph configuration-id="发布日期与分类"></e-paragraph>
    <e-paragraph configuration-id="引言"></e-paragraph>
    <e-image configuration-id="主图"></e-image>
    <e-heading configuration-id="小标题1"></e-heading>
    <e-paragraph configuration-id="正文A"></e-paragraph>
    <e-image configuration-id="图片2"></e-image>
    <e-heading configuration-id="小标题2"></e-heading>
    <e-paragraph configuration-id="正文B"></e-paragraph>
  </e-div-block>
</e-flexbox>
```
- 每个标签都要有唯一 `configuration-id`，且它就是编辑器结构面板里的层名，用人类可读名称。
- 图片配置：`{"image":{"src":{"id":<附件ID>},"size":"full"}}` —— 用**媒体库 ID**，不要 URL。
- 断点用 Elementor 原生 `@media(--tablet)` / `@media(--mobile)`，不写 `@media (max-width: 768px)`。
- 建完 `elementor/get-page-structure` 复核树完整、`staged` 状态、图片 ID 正确。详见 `references/responsive-recipe.md`。

## 5. 文章元数据 + 发布

- **先补元数据再发布**（顺序见 `references/post-fields.md`）：摘要（`excerpt`）、发布日期、分类、标签、特色图片通过站点 REST API 写入文章；分类/标签不存在先创建再关联；特色图用附件 ID。摘要源网页有 description 就必写，写完 publish 后用 `?context=edit` 回读 `excerpt.raw` 复核。
- 现场若无 REST 写权限或字段解析不到：**不伪造**，明确记录未还原项并告知用户。
- `elementor/publish-document`（`post_id` = 文章 ID）发布。
- 注意：已发布文章上的 MCP 改动是**暂存草稿**，必须显式发布才生效。

## 6. 验收（不做则不算完成）

| 检查 | 合格标准 |
|---|---|
| 前台 HTTP | 200 |
| 内容类型 | `post_type = post`（`elementor/list-posts` 或 REST 核对） |
| 图片来源 | 全部 `wp-content/uploads`；外站 CDN 残留数 = 0 |
| 结构树 | 原生 `e-` 元素，`staged:false` |
| 元数据 | 标题/摘要/日期/分类/标签/特色图与源一致（或未还原项已明确标注） |
| 三端横向溢出 | 1440 / 768 / 390 全部 `0px` |
| 三端实测值 | 字号、行高、图片尺寸符合配方 |
| 截图 | 文字不被硬截断、图片不裁切变形 |

批量任务输出汇总表：文章 ID / 标题 / 前台 URL / 后台编辑 URL / 图片数 / 元数据状态 / 三端溢出结果。

## 7. 换目标站点

默认 `testdecor`（`http://testdecor`，MCP 连接 `testdecor-elementor`）。用户给新地址时：
1. `elementor/list-posts` 探活，`elementor/get-system-info` 确认 Elementor 版本与 Atomic Editor 状态。
2. 新连接建立方式见 `references/target-site-config.md`；REST 端点详见 `references/post-fields.md`（元数据写入需要）。
3. Phase 1–6 不变；地址、文章 ID、附件 ID 全部动态取，不写死 `testdecor`。

## 8. 验证工具与陷阱

- 三端实测用同源 iframe 测量页：`templates/measure-iframe.html`（放目标站根，Chrome headless `--dump-dom` 读 `RESULT_JSON`）。
- 前台快速核验：`scripts/verify_front.py`。
- 陷阱清单见 `references/troubleshooting.md`，尤其：
  - headless `--window-size=390` 被钳到 **504px** → 假「文字被切断」；用 390px iframe + ≥600px 窗口截图再裁。
  - 站点 `body` 常有 `overflow-x:clip` → `documentElement.scrollWidth` 假阴性，要遍历元素比 `scrollWidth > clientWidth`。
  - 中文固定链接曾把 `?page_id=8` 301 到 404：置空 `wp_options.permalink_structure` 可解。

## 9. 版权边界

本地测试站作还原底稿没问题；**正式对外上线前**必须换成自有或已获授权的文字与图片，并主动提醒用户。

## References

- `references/post-fields.md` — **文章元数据（标题/摘要/日期/分类/标签/特色图）解析与 REST 写入方法（本专家新增，动手前必读）**
- `references/layout-fidelity.md` — 布局忠实原版铁律 + 真实渲染测量还原方法 + 实测尺寸基线（最高优先级）
- `references/responsive-recipe.md` — 三档响应式参数配方（实测数值 + 可直接复制的 style 字符串）
- `references/troubleshooting.md` — 踩坑手册（通道、代理、容器、断点、固定链接、兼容性）
- `references/target-site-config.md` — 目标站点配置与切换
- `templates/measure-iframe.html` — 三端同源 iframe 实测页
- `templates/batch-intake.md` — 批量任务清单模板
- `scripts/verify_front.py` — 前台图片本地化与可访问性核验
