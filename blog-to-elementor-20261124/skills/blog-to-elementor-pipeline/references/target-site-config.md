# 目标站点配置与切换

用户当前默认站点是 **`testdecor`**，但明确要求：「以后如果我做新的网页，我可以要求你更改这个复制的地址」。所以站点信息必须是**运行时参数**，不能写死在流程里。

## 一、当前默认值（仅作为默认，不是硬编码）

| 项 | 值 |
|---|---|
| 站点名 | `testdecor` |
| 前台地址 | `http://testdecor` |
| 站点目录 | `E:\phpstudy_pro\WWW\testdecor` |
| MCP 连接名 | `testdecor-elementor` |
| MCP 端点 | `http://testdecor/wp-json/mcp/mcp-adapter-default-server` |
| 编辑器 | Elementor Pro 4.4.1，V4 Atomic Editor 已开启 |
| 已验证页面 | 8（测试页）、12（Inspiration 列表）、16（MDF 案例）、34（SPC Wall Panels，流水线成品） |

> 上述 ID 仅用于举例和回归对照，建新页时**一律新建**，不覆盖。

## 二、用户说「换个地址」时的判定

先问清（或按上下文判断）用户指的是哪一种：

1. **换源网页地址 / 换源材料**：只是这批要复制的网页变了（新 URL 或用户新发来的 HTML 文件）→ 目标站点不变，Phase 0/1 换输入即可。用户把网页存到任意自己目录直接发来就行，不要求挪到指定目录。
2. **换目标站点地址**：新后台 / 新域名 → 走下面第三节。
3. **两者都换** → 分别处理，流程不变。

不要因为用户说「地址」就默认只改一个；含糊时一句话确认，别猜错后大改一通。

## 三、切换到新 WordPress 站点的步骤

1. **探活连接**：调用 `elementor/list-posts`（`post_type:"post"`）确认 MCP 能读到新站文章。工具列表里连接名按实际加载的为准（`mcp__<连接名>__*`）。
2. **若连接不存在**：
   - 在 `~/.workbuddy/mcp.json` 的 `mcpServers` 里新增一条（形状见 `troubleshooting.md` B 节），**保留**已有连接，不要覆盖。
   - 需要 Application Password；非 HTTPS 本地站加 `define('WP_ENVIRONMENT_TYPE','local')`。
   - 让用户在自定义连接器入口点 **Trust**，并**完全退出重开新会话**后工具才出现。
   - 用 `elementor/agent-ready-scan` / `elementor/get-system-info` 确认 Elementor 版本与 Atomic Editor 状态。
3. **确认版式基线**：新站的全局字体、主色、内容宽度可能不同。默认沿用 `responsive-recipe.md` 的三档配方，若用户要求贴合新站风格，先读 `elementor/get-default-styles` / 全局类再调整。
4. **确认元数据写入通道**：新站若要做日期/分类/标签/特色图，需该站有写权限的 REST 凭据（Application Password / nonce），探活方法见 `post-fields.md` 第 3.1 节。写不通就按该文件第 4 节降级。
5. **Phase 1–6 不变**：解析 → 图片上传（上传端点里的 `<站点>` 换成新地址）→ `post_type:"post"` 建文章 → 原生元素搭正文（响应式一次写入）→ 补元数据 → 发布 → 三端实测。
6. **验收里的地址全部动态取**：前台 URL、后台编辑 URL、图片 URL 都从工具返回值和页面实测中取，不拼死 `testdecor`。

## 四、每篇文章的输出必须给全

- 前台：`http://<站点>/?p=<ID>`（文章用 `p`，不是页面的 `page_id`；或固定链接）
- 后台编辑：`http://<站点>/wp-admin/post.php?post=<ID>&action=elementor`
- 预览：`elementor/publish-document` 返回的 `preview_url`（需登录编辑器账号）
- 图片：`http://<站点>/wp-content/uploads/YYYY/MM/<文件名>`

## 五、批量任务的配置记录

批量任务开始时，把本次配置写进 `templates/batch-intake.md` 的清单头部：目标站点、MCP 连接名、页数、是否要页眉页脚、文案语言。这样中途不会被默认 `testdecor` 带偏。
