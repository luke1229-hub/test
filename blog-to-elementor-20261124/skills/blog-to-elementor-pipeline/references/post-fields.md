# 文章元数据：标题 / 摘要 / 日期 / 分类 / 标签 / 特色图

本文件是「博客复刻」专家相对「网页复刻」新增的能力说明。产出是 WordPress **文章（post）**，除正文外还要尽量还原这些元数据字段。**原则：能写就写，写不了就如实降级并在正文里保留可见信息，绝不伪造、绝不静默跳过。**

## 一、先从源 HTML 解析出来

用 Python 标准库（`re` / `html`，环境可能没有 bs4）。评论页由 Chrome 保存，`src`/链接里的 `&` 是 `&amp;`，需要 `html.unescape()`。

| 字段 | 来源（按优先级） | 解析示例 |
|---|---|---|
| 标题 `title` | JSON-LD `"@type":"Article"` 的 `headline` → `<h1>` → `og:title` → `<title>` 去掉 ` \| 站点名` 后缀 | 页面 `<h1>Big 5 Dubai 2026 Visitor Guide...` → 文章标题 |
| 摘要 `excerpt` | `<meta name="description">` → `<meta property="og:description">` → JSON-LD `description` → 正文第一段提炼 | 源页 meta description 直接取，作为 WordPress 摘要（编辑器右侧 `Add an excerpt...`）；**没有就留空，不臆造** |
| 发布日期 `date` | JSON-LD `datePublished` → `<time datetime="...">` → 页面可见日期文本 | `Nov.20 2026` → `2026-11-20`；`2026-11-20T09:30:00+00:00` 直接取 |
| 分类 `category` | 面包屑中间层（如 `Home / Company News / 文章标题` → `Company News`）→ 页面栏目标签 → JSON-LD `articleSection` | `Home/Company News/Big 5 Dubai...` → 分类 `Company News` |
| 标签 `tags` | 页面 tags/关键词区 → `<meta name="keywords">` → JSON-LD `keywords`（逗号分隔） | 无则不写，不臆造 |
| 特色图 `featured_media` | `og:image` → `twitter:image` → 正文首张内容大图（排除 logo/图标/头像）；取到 URL 后对应到已上传的附件 ID | 源图传到媒体库后拿到的附件 ID |

**注意排除**：正文里的"相关文章 / 最新文章 / 推荐阅读"列表（含日期、标题、缩略图）**不是本文元数据**，不要误当成当前文章的日期或特色图。判据：这些列表在 `<article>` 之外或带 `related`/`recent`/`recommended` 类名；本文日期通常在 `<article>` 内、`<h1>` 附近或 `<time>` 标签里。

## 二、标题写入（一定可做）

`elementor/create-page` 的 `title` 参数直接写入文章标题，**不依赖 REST**：

```
elementor/create-page { "title": "<标题>", "post_type": "post", "template": "elementor_canvas" }
```

## 二·补、摘要 excerpt 写入（2026-11-23 testdecor 实测可做，必须写）

**摘要不是可选项**：编辑器右侧 `Add an excerpt...` 空着会让用户以为漏了。只要源网页有 description/og:description，就要写进 WordPress 的 `excerpt` 字段。

- Elementor MCP 工具不改 `excerpt`，用和日期同一条 **REST 通道**：
  ```
  POST /wp/v2/posts/<文章ID>
  {"excerpt": "Plan your visit to Big 5 Dubai 2026. Explore exhibition dates, opening hours, floor plans, exhibitor lists, key halls, transport and visitor tips."}
  ```
- 写**纯文本**（不带 `<p>` 等 HTML 标签），WordPress 会在 `rendered` 里自动包 `<p>`。
- 实测：写入返回 200；`?context=edit` 回读 `excerpt.raw` 是纯文本、`excerpt.rendered` 是 `<p>...</p>`；publish 之后仍保留，侧栏显示摘要文字而不是 `Add an excerpt...`。
- **发布后复核**：`GET /wp/v2/posts/<ID>?context=edit` 确认 `excerpt.raw` 非空；若被 publish 覆盖，补写一次再验。
- 源网页确实没有描述性 meta 时留空，并在汇报里说明"源未提供摘要，未臆造"；不要拿正文长段硬塞进摘要框。

## 三、日期 / 分类 / 标签 / 特色图写入（尽力而为）

这些字段 Elementor MCP 工具**改不了**（`update-page-settings` 只管 Elementor 文档级设置，明确不支持 post 的 taxonomy/meta/date）。标准通道是 **WordPress 核心 REST API**：

```
POST /wp-json/wp/v2/posts/<文章ID>
Authorization: Basic <base64(用户名:Application Password)>   # 或用登录后的 nonce
Content-Type: application/json

{
  "excerpt": "<源页 description，纯文本>",
  "date": "2026-11-20T09:30:00",
  "categories": [<分类term ID>],
  "tags": [<标签term ID 数组>],
  "featured_media": <附件ID>
}
```

配套端点（分类/标签不存在时先建）：
```
POST /wp-json/wp/v2/categories   {"name":"Company News"}   -> 返回 id
POST /wp-json/wp/v2/tags         {"name":"tradeshow"}      -> 返回 id
```

本地站用查询参数形式 `http://<站点>/index.php?rest_route=/wp/v2/...`，Windows curl 加 `--noproxy '*'`。

### 3.1 权限前提（实测记录，2026-11-23 / testdecor）

- **读**公开文章的 `/wp/v2/posts`、`/wp/v2/categories`、`/wp/v2/tags` 返回 200；
- 当前 `mcp.json` 里 `testdecor-elementor` 的 Basic 凭据（供 Elementor MCP 用）对 **核心 `/wp/v2/*` 的写操作返回 401 `rest_cannot_edit`**，对草稿的读也受限——它是"仅供 MCP 适配器"的凭据，不是标准 REST 管理员凭据；
- 因此**不能直接用这条连接写元数据**。执行时需任一可行凭据：
  1. 该站点某管理员账号的 **Application Password**（WP 后台 → 用户 → 个人资料 → Application Passwords 生成；本地非 HTTPS 站需 `define('WP_ENVIRONMENT_TYPE','local')`）；
  2. 登录后的 **REST nonce**（`X-WP-Nonce`）；
  3. 有写权限的其他认证插件通道。
- 换站点时先探活：`curl -u ... "http://<站点>/index.php?rest_route=/wp/v2/posts/<ID>"` 能读、`-X POST` 改一个字段能返回 200，才说明元数据通道可用。

### 3.2 写入顺序（避免被覆盖）

1. `elementor/create-page` 建文章壳（draft）→ 拿到 ID；
2. `elementor/build-composition` 搭正文 → `elementor/get-page-structure` 复核；
3. **在 publish 之前**用 REST 写元数据（excerpt/date/categories/tags/featured_media，摘要与其余字段同一批写入）；
4. `elementor/publish-document` 发布；
5. 发布后再用 REST **读回核对**（`/wp/v2/posts/<ID>?context=edit` 核对 `excerpt.raw`、date、categories、tags、featured_media）；若 publish 过程冲掉了某些字段，publish 后再补写一次并复验。

## 四、降级策略（REST 写不通时必做）

不要因为写不进元数据就报失败或装作完成：

1. **摘要**：源无 description 时不强造，留空并在汇报里说明；有描述但 REST 写不进时，把该句作为正文引言 `e-paragraph`，并给用户后台链接手填。
2. **日期 / 分类 / 标签**：作为可见文本写进正文顶部的一行，例如 Elementor `e-paragraph`：
   `Nov 20, 2026  ·  Company News  ·  Tradeshow, Dubai, Construction`
   ——用户肉眼能看到、也能在编辑器里手改成真正的 taxonomy。
3. **特色图**：把该图作为正文第一张 `e-image`（源页面本来也有主图，正好一致），不空着。
4. **汇报里如实写明**：哪些元数据字段已写入 WordPress 原生字段、哪些因站点权限只能放进正文、需要用户手动补的地方。给出后台编辑链接方便用户改。
5. **分类/标签**若站点尚未建立对应 term，不要在新站点凭空批量制造 taxonomy 污染；除非用户明确要求"新建分类/标签"，否则降级为正文文本更安全。

## 五、验收清单

- [ ] `title` = 源文章标题（`elementor/list-posts` 或 REST 核对）
- [ ] `post_type = post`
- [ ] `excerpt` = 源 description（`?context=edit` 核对 `excerpt.raw` 非空），或源无描述已说明未臆造
- [ ] `date` 与源一致，或已在正文可见呈现并已说明
- [ ] `categories` / `tags` 已关联，或已在正文可见呈现并已说明
- [ ] `featured_media` 已设置，或主图已作为正文首图
- [ ] 每张图 URL 都是本站 `wp-content/uploads`
- [ ] 三端横向溢出 0
- [ ] 汇总表里逐篇列出元数据状态（完整 / 部分降级 / 降级原因）
