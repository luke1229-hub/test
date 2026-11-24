# 博客文章复刻26年11月24日版本（blog-to-elementor）

把博客文章的网页变成 WordPress 后台里**真人可以用 Elementor 手工编辑**的一篇**文章（post，不是页面）**：还原标题、摘要、发布日期、分类、标签、特色图片；正文图片下载上传媒体库；从第一版起就同时适配电脑、平板、手机三种设备。

> 与「页匠 / 网页复刻」的区别：那位产出**页面（page）**，本专家产出**文章（post）**，并额外还原博客文章的日期/分类/标签/特色图。复刻流水线（布局忠实原版、图片本地化、三端响应式、真实证据验收）完全继承。

## 类型

Agent 型（单个 AI 专家）· 分类 `02-Engineering`

## 能做什么

- **产出是文章（post）**：`post_type:"post"` 新建，进 WordPress「文章」列表，不是「页面」。
- **文章元数据一起还原**：标题、摘要（`excerpt`，源有 description 就必写）、发布日期、分类、标签、特色图片；站点权限不允许写入原生字段时，降级为正文可见文本并如实说明，绝不伪造。
- **一次给几篇都行**：每篇博客文章生成一个独立新文章，不覆盖已有内容。
- **文件存哪都行**：网页下载/保存到你自己的任意目录（桌面、下载文件夹、D 盘……），直接把 `.html` 文件发给我或告诉我完整路径即可；zip/rar 整包（`.html` + `_files`）也行，我自己解压，不用你挪文件。
- **图片本地化**：外链直接下载、随附 `_files` 直接取用、`data:` URI 解码，上传目标站媒体库，页面用媒体库 ID 引用，不留外站链接。
- **真人可编辑**：Elementor V4 Atomic 原生元素（`e-flexbox` / `e-heading` / `e-paragraph` / `e-image` 等）搭建，编辑器里逐层可点选、可改字改图，不是纯代码页。
- **布局忠实原版**：内容可以差一点，但分栏、区块顺序、图片尺寸/比例、卡片列数、字号层级尽量贴合原版——你手工修改是建立在原版式样上的，布局改动太大就不好改。
- **响应式一次到位**：建文章时就把桌面/平板/手机三档断点写进样式，发布即三端可用。
- **真实证据验收**：前台 200、`post_type=post`、三端横向溢出 0、外站图片残留 0、结构树可编辑，逐项实测后才算完成。

## 怎么用（三步）

1. 打开 WorkBuddy 左侧栏 **专家** → **我的专家** → 找到「博客文章复刻26年11月24日版本」→ 开始对话。
2. **把文章交给我**：Chrome 打开博客文章 → `Ctrl+S` → 保存类型选「网页，全部」或「网页，仅 HTML」→ 把得到的 `.html` 文件直接发进对话（或告诉我完整路径）。多篇文章一次发也行；若同时生成同名 `_files` 文件夹，一起发来或告知路径更好（图片实体在里面），但不是开工前置条件。也可以把整页打包成 zip/rar 发我。
3. 说一句需求，例如：「我把 3 篇博客文章的 HTML 发给你，复刻成 testdecor 后台的可编辑 WordPress 文章，日期分类标签特色图都要，图片传媒体库，直接做好三端响应式」。我会先列清单跟你确认，再逐篇建、逐篇验，最后给汇总表（文章 ID / 标题 / 前台链接 / 后台编辑链接 / 元数据状态 / 三端实测结果）。

> 若目标站有反爬验证（如 Vercel Security Checkpoint），自动抓取会被拦，用第 2 步手动保存 HTML 再发我即可——这是已验证可用的通道。

## 试试这样问我

- 我把博客文章的网页 HTML 发给你，复刻成 testdecor 后台可编辑的 WordPress 文章，标题日期分类标签特色图都要，图片传媒体库，直接做好三端响应式
- 把这几篇博客文章做成新站点的 WordPress 文章，目标站点我给你地址，同样一次做成响应式
- 检查我后台这批新文章的响应式，确认手机、平板、桌面三端都不横向溢出

## 随附资料

| 文件 | 内容 |
|---|---|
| `skills/blog-to-elementor-pipeline/SKILL.md` | 完整流水线 SOP（含 post_type=post 建文章） |
| `references/post-fields.md` | **文章元数据解析与 REST 写入/降级方法（本专家新增）** |
| `references/layout-fidelity.md` | 布局忠实原版铁律 + 真实渲染测量还原方法 + 实测尺寸基线 |
| `references/responsive-recipe.md` | 三档响应式参数配方（实测数值，可直接复制） |
| `references/troubleshooting.md` | 踩坑手册（抓取通道、代理、headless 504px、overflow-x 假阴性等） |
| `references/target-site-config.md` | 目标站点配置与切换 |
| `templates/measure-iframe.html` | 三端同源 iframe 实测页 |
| `templates/batch-intake.md` | 批量任务清单模板 |
| `scripts/verify_front.py` | 前台图片本地化与可访问性核验 |

## 边界

- 只新建文章，不改动你已有的页面/文章。
- 文章元数据能否写入 WordPress 原生字段，取决于目标站是否提供有写权限的 REST 凭据；写不进时会降级为正文可见文本并明确告知。
- 本地测试站可作一比一还原底稿；**正式对外上线前**请替换成自有或已获授权的文字与图片。

## 头像

头像位于 `avatars/expert.png`（ImageGen 生成，512×512）。可手动替换：PNG/JPG，≤500KB。

## 安装位置

```
C:\Users\Administrator\.workbuddy\plugins\marketplaces\my-experts\plugins\blog-to-elementor\
```

注册后出现在「专家 → 我的专家」。分享打包：

```bash
python3 scripts/package_expert.py <expert-dir>
```
