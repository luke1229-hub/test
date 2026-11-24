# 三档响应式参数配方（实测可直接复制）

> 来源：2026-11-23 在 `testdecor` 页面 34 上真实 Chrome 测量。所有数值是 `getComputedStyle` / `getBoundingClientRect` 读出来的渲染结果，不是估计。
> 断点一律用 Elementor 原生 `@media(--tablet)` / `@media(--mobile)`，**禁止**像素 media query（会被降级成 custom CSS，编辑器里看不到设备切换）。

## 一、实测结果总表

| 项 | 桌面 1440 | 平板 1024 / 768 | 手机 390 |
|---|---|---|---|
| `main` padding | 16px | 12px | **0px** |
| `article` 宽度 | 900px 居中 | 985 / 729px | 375px（满宽） |
| `article` 左右内边距 | 32px | 28px | **0px** |
| 文字元素左右内边距 | 0（靠容器） | 0（靠容器） | **16px**（元素自带） |
| H1 | 38px / 行高 1.25 | 32px / 1.3 | **24px / 1.3** |
| 副标题 | 16px / 行高 2 | 15.5px / 1.85 | **15px / 1.7** |
| 正文 | 15px / 行高 2 | 15px / 1.85 | **14px / 1.75** |
| 面包屑 | 13px | 12.5px | **12px** |
| 图片比例 | 16/9 | 16/10 | **3/2（手机满宽）** |
| 图片实际尺寸 | 836×470 | 929×581 / 673×421 | **375×250** |
| 横向溢出 | 0 | 0 | **0** |

手机图片面积相对改造前（约 334×188）增大约 **49%**；H1 从 28px 再降到 24px，正文从 15px 降到 14px、行高从 30px 降到 24.5px —— 解决「图小字大」。

## 二、关键设计：手机图片满宽，文字仍有边距

直接把 `article` 左右 padding 归零会让文字贴屏幕边缘。正确做法是**让图片出血、文字各自补内边距**：

- `article` 在 `@media(--mobile)` 里 `padding-inline-start/end: 0`
- 每个文字元素（面包屑、H1、副标题、引言、正文、结论）在 `@media(--mobile)` 里加 `padding: 0 1rem`
- 图片元素不加 padding，保持 `width: 100% !important`，自然满宽

实测校验：`h1PaddingLeft = 16px`、`bodyPaddingLeft = 16px`，而 `articlePadInline = 0px`、`imageBoxes = 375x250`。

## 三、可直接复制的 style 字符串

用 `elementor/build-composition` 的 `style` map 或 `elementor/manage-elements` 的 `style`（配 `style_apply_mode: "replace"`）。

### 根容器 `main`（configuration-id: 页面主体）
```
padding: 1rem; background-color: #ffffff; display: block;
@media(--tablet) { padding: 0.75rem; }
@media(--mobile) { padding: 0; }
```

### 内容容器 `article`（configuration-id: 内容容器）
```
width: 100%; max-width: 900px; padding-block-start: 2.5rem; padding-block-end: 4rem; padding-inline-start: 2rem; padding-inline-end: 2rem; margin-inline: auto; box-sizing: border-box;
@media(--tablet) { max-width: 100%; padding-block-start: 2rem; padding-block-end: 3rem; padding-inline-start: 1.75rem; padding-inline-end: 1.75rem; }
@media(--mobile) { padding-block-start: 1.5rem; padding-block-end: 2.5rem; padding-inline-start: 0; padding-inline-end: 0; }
```

### H1（configuration-id: 主标题）
```
font-weight: 700; font-size: 38px; color: #1a1a1a; line-height: 1.25; margin-block-end: 1.5rem;
@media(--tablet) { font-size: 32px; line-height: 1.3; margin-block-end: 1.25rem; }
@media(--mobile) { font-size: 24px; line-height: 1.3; margin-block-end: 1rem; padding: 0 1rem; }
```

### 面包屑
```
font-size: 13px; color: #888888; line-height: 1.6; margin-block-end: 1.5rem;
@media(--tablet) { font-size: 12.5px; margin-block-end: 1.25rem; }
@media(--mobile) { font-size: 12px; line-height: 1.5; margin-block-end: 1rem; padding: 0 1rem; }
```

### 副标题
```
font-size: 16px; color: #4a4a4a; line-height: 2; margin-block-end: 2.5rem;
@media(--tablet) { font-size: 15.5px; line-height: 1.85; margin-block-end: 2rem; }
@media(--mobile) { font-size: 15px; line-height: 1.7; margin-block-end: 1.5rem; padding: 0 1rem; }
```

### 正文 / 引言 / 结论（每个段落同理）
```
font-size: 15px; color: #4a4a4a; line-height: 2; margin-block-end: 1.5rem;
@media(--tablet) { line-height: 1.85; }
@media(--mobile) { font-size: 14px; line-height: 1.75; margin-block-end: 1.25rem; padding: 0 1rem; }
```
> 结论段是最后一段，可省略 `margin-block-end`。

### 图片（三张同样）
```
aspect-ratio: 16/9; object-fit: cover; margin-block-end: 1.5rem; background-color: #f0ebe3; display: block; width: 100% !important;
@media(--tablet) { aspect-ratio: 16/10; margin-block-end: 1.75rem; }
@media(--mobile) { aspect-ratio: 3/2; margin-block-end: 1.5rem; }
```
> 3/2 贴近原图比例，不裁切变形；若用户还要更大，可改 `4/3`（会更裁左右，需先确认）。

## 四、写入与发布顺序

1. `elementor/build-composition`（或 `manage-elements` 批量 update，`style_apply_mode:"replace"`）
2. `elementor/get-page-structure`（`include_content:true`）确认三档 `@media` 都在 `styles.css` 里，没被丢弃
3. `elementor/publish-document` —— **必须调**，改动默认只是 staged 草稿
4. 前台重新抓取验证（注意缓存，URL 加随机参数或换 user-data-dir）

## 五、验收阈值

- 三档 `overflowPx` 全为 `0`
- 手机 `h1Font = 24px`、`bodyFont = 14px`、`imageBoxes` 宽度 = 视口宽度（375）
- 手机 `h1PaddingLeft = 16px`（证明文字没贴边）
- 遍历所有元素，`scrollWidth > clientWidth + 2` 的只有 `elementor-screen-only` 这类 1px 无障碍元素（可忽略）

## 六、为什么响应式要「一次写入」

用户在需求里明确：以后换站点/换网页时**直接做出来就是响应式的，不用单独留一步调整**。所以三档断点必须写在 Phase 3 建页的同一批 `style` 里，而不是先建桌面版、发布、再回头补响应式。若用户后续说「再调一下手机端」，那属于改需求，不是补流程缺陷。
