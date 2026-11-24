# 踩坑手册（全部实跑定位过根因）

## A. 抓取通道

| 现象 | 根因 | 处理 |
|---|---|---|
| agent-browser 无头/有头/复用 profile 全部「无法验证您的浏览器，代码 21」 | Vercel Security Checkpoint 拦的是「被 CDP 自动化驱动」这一特征，与 cookie/profile 无关 | 别硬扛，请用户在真实 Chrome `Ctrl+S` 保存网页，把存下来的 `.html` **直接发进对话**（存任意目录都行） |
| 只发来一个 `.html`，图片取不到 | Chrome「网页，全部」会把 `<img src>` 改写成指向同名 `_files` 的相对路径，实体在那个文件夹里。**2026-11-23 实测**：用户保存的 SPC Wall Panels 页共 8 个 `<img>`，**8 个全是相对路径**、0 个外链、0 个 data URI | 先扫图片来源：外链直接下载、data URI 直接解码；确为相对路径且 `_files` 实体拿不到时，**一次性**请用户把该文件夹发来或告知路径。不要求用户重新保存或整理目录；「网页，仅 HTML」通常保留外链，可直接下载 |
| 相对路径明明在 `_files` 里却 0 命中 | HTML 属性里的 `&` 是实体编码 `&amp;`，文件名里是真实 `&`；不解码直接拼路径必然找不到 | 拿到 src 先 `html.unescape()` 再拼路径。实测同一包：不解码 0/8，解码后 8/8 全命中 |
| 用户把整页文件夹打成 zip 发来 | 这是推荐交付形态之一，不是麻烦 | 直接解压到工作区，按「外链/相对路径/data URI」规则处理；实测 7.4 MB zip → 52 文件 → 8/8 图片实体全命中，解压后按原相对路径定位即可 |
| 用户说「保存的网页点开报错，打不开」 | 常见是 `Application error: a client-side exception has occurred while loading (see the browser console...)` —— **Next.js 站点本地 `file://` 打开时客户端 hydration 脚本加载失败**，错误页是浏览器运行时临时渲染的，**不在保存的 HTML 源码里**。2026-11-23 实测：两个报错页源码里该字样出现次数均为 **0**，且 `<title>` / `<h1>` / 正文段落 / 图片引用全部完整 | **不要据此判定存档损坏**。直接读 HTML 源码验收内容，而不是让用户重存或去打开它。复刻只读源码 + 取图片实体，完全不依赖页面 JS 能否运行，所以照样能成功 |
| 少数图片实体为 `image` / `image(1)` 且本地找不到 | Next.js `/_next/image?url=...` 图片优化接口的资源，Chrome 保存时只落地成占位名，真实文件没存下来。实测 125 张里 2 张属于此类（认证小图标 ISO 14001、技术图纸），`srcset` 里保留原相对路径 | 这类多为站点级装饰/图标，按「排除页眉页脚/站点级区块」规则本就不进正文；若确需，可从 `srcset` 解出原路径提示用户，或跳过。**不要因为 2 张占位图就判定整页不可复刻**，其余 123/125 命中即可开工 |
| `--auto-connect` 不可用 | 需要 Chrome 以 `--remote-debugging-port` 启动，用户日常 Chrome 没开 | 不作为主通道 |
| 内置浏览器能过验证但导不出源码 | 只给 screenshot + 精简可见 DOM（无 class/style/img src，上限约 2 万字符 / 200 元素，滚动后返回空） | 只用于确认页面存在，不用于建页 |
| WebFetch 时好时坏 | 服务端通道间歇可用，且只给 markdown 正文，追问图片 URL / CSS 链接无返回 | 不单独依赖 |
| 本机 curl / Node fetch 直连超时 | 沙箱注入失效代理 `http://127.0.0.1:59285`，报 `ERR_TUNNEL_CONNECTION_FAILED` | 跑前 `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY`；本地站点加 `--noproxy '*'` |

**结论**：受保护站点的可用通道是「用户在真实 Chrome 里保存网页 → 把 `.html` 文件直接发给我」。文件存在用户任意自己目录都行，不要求挪进 `captured/` 或任何指定目录。这一步不是能力缺陷，是通道选择，已在流水线里固化。

## B. WordPress / Elementor 环境

| 现象 | 根因 | 处理 |
|---|---|---|
| Application Password 报「站点不是 HTTPS」 | 本地非 HTTPS | `wp-config.php` 加 `define('WP_ENVIRONMENT_TYPE','local')` |
| MCP 配置写了但工具不出现 | 自定义连接器需要 Trust，且要在**新会话**中生效 | 写入 `~/.workbuddy/mcp.json` → Trust → 完全退出重开同文件夹新会话 |
| 前台 `?page_id=8` 被 301 到 404 | 中文固定链接规则 | MySQL：`UPDATE wp_options SET option_value='' WHERE option_name='permalink_structure';` |
| MCP 改动后前台没变 | 已发布页面上的改动是 **staged 草稿** | 必须 `elementor/publish-document` |
| 用 `html2elementor` 生成的 JSON 不敢用 | 它产 3.x 容器结构，本站是 Elementor **V4 Atomic Editor**，兼容性未验证 | 用 `elementor/build-composition` 建原生 `e-` 元素 |

**MCP 连接配置形状**（`~/.workbuddy/mcp.json`）：
```json
"<连接名>": {
  "type": "http",
  "url": "http://<站点>/wp-json/mcp/mcp-adapter-default-server",
  "headers": { "Authorization": "Basic <base64(user:app-password)>" }
}
```

## C. 本地上传

| 现象 | 根因 | 处理 |
|---|---|---|
| 图片上传 HTTP 000 | 沙箱代理拦截 | `curl --noproxy '*'` |
| curl 找不到文件 | Windows `curl` 是 `C:\windows\system32\curl`，不认 Git Bash 的 `/e/...` 路径 | 传 Windows 风格路径 |
| 上传端点 | Elementor MCP 媒体上传 | `http://<站点>/index.php?rest_route=/elementor/v1/mcp-media-upload`，头：`X-Elementor-Mcp-Upload-Token` / `Filename` / `Title`；成功 HTTP 201 |

## D. 响应式验证（最容易误判的两个坑）

### 坑 1：Chrome headless 最小窗口宽度 504px
`--window-size=390,1500` 时，headless Chrome 把 **CSS 视口钳到 504px**，但**截图画布仍是 390px**，于是把 504px 排版的内容硬裁掉右边，看起来像「手机端文字被切断 / 单词被切开」。这是**工具假象，不是页面问题**。

实测证据：
```
--window-size=390,1500  →  topViewport.innerWidth = 504, clientWidth = 504
iframe 宽 390           →  clientWidth = 375, h1Font = 24px, overflowCount = 1（仅 1px 无障碍元素）
```

**正确做法**：把目标页放进一个 **390px 宽的 iframe**，用 `--window-size=600,1700`（≥600 才不会被钳）截「容器页」，再裁左 390px。见 `templates/measure-iframe.html` 与同目录说明。
> 同理，别用「直接给目标页设 --window-size=390 再截图」来判断手机端。

### 坑 2：`overflow-x: clip` 让 scrollWidth 检测假阴性
站点 `body` 常有 `overflow-x: clip`（实测 `bodyOverflowX = "clip"`），此时 `documentElement.scrollWidth - clientWidth` 恒为 0，即使内部元素真的溢出也测不出来。

**正确做法**：遍历 iframe 内所有元素，逐个比较
- `el.scrollWidth > el.clientWidth + 2`，或
- `el.getBoundingClientRect().right > 视口宽 + 2`

并单独读 `h1.scrollWidth` vs `h1.clientWidth` 判断文字是否溢出。实测合格页面 `overflowCount` 只应为 1，且那一个是 `elementor-screen-only` 的 1px 无障碍 span（可忽略）。

### 其它
- 验证时给 URL 加随机参数或换 `--user-data-dir`，避免拿到缓存的旧 HTML。
- 站点根目录的临时测量页用完必须删掉，别留在生产目录。
- Elementor V4 的页面 CSS 文件（`wp-content/uploads/elementor/css/post-34.css`）可能几乎是空的（实测 33 字节），样式走内联输出 —— **不要靠 grep CSS 文件判断响应式是否生效**，要用 `elementor/get-page-structure` 读 `styles.css`，再用浏览器实测 computed style。

## E. 版权

本地测试站可作一比一还原底稿；正式对外上线前必须替换成自有或已获授权的文字与图片，并主动提醒用户。曾明确拒绝「逐字照搬第三方商业文字/图片上线」，仅允许本地测试用途。
