# 布局忠实原版 · 铁律与还原方法

> 来源：2026-11-23 用户反馈与返工实证。用户明确要求：**内容可以差一点，但布局必须尽量和原版一致**。原因是用户后续会在 Elementor 里手工修改，而手工修改是**建立在原版式样之上**的；布局一旦被大幅改动，用户就没法在原版式样基础上改了。此文档是硬性约束，不是建议。

## 0. 铁律（最高优先级）

1. **布局忠实 > 内容完美**：当"精确还原文案"与"还原原版布局"冲突时，优先保证布局结构、区块顺序、分栏方式、图片尺寸/比例、字号层级与原版一致。文案逐字保留仍是目标，但绝不能为了塞文案而改动原版版式。
2. **不得自由发挥版式**：复刻不是"照着内容重新设计一个好看的页面"。禁止把左右分栏改成上下堆叠、把小图放大满宽、把列表改成网格、把 2 列改成 3 列、改变区块顺序——除非原版本来就是那样。
3. **先量后建**：任何布局决策必须来自对原版的**实际测量**，不靠看图猜测、不靠"常见网页大概这样"。见第 2 节方法。
4. **用户手改友好**：元素层级命名要清晰、结构要贴合原版区块，让用户能在编辑器结构面板里对应着原版一块块改。擅自重组结构 = 给用户添麻烦。

## 1. 为什么这条最重要（用户原话背景）

用户会在生成的页面上继续手工调整。手工修改的心智模型是"在原版式样上改"，所以：
- 布局一致 → 用户看着熟悉，能直接对照原版定位要改的地方；
- 布局变了 → 用户得先理解一套新结构，再重新找要改的元素，等于返工。

一次反馈实证（NatureTough WPC Decking 产品页）：第一版"东西都在"但布局大幅偏离——Hero 从左右分栏做成上下堆叠、主图从 520×520 方图做成满宽大图、规格区从左右分栏做成单列、配件图从 182×182 做成大图。用户反馈"基本东西有了，但布局差太多，图片太大很突兀"。**教训**：内容齐全 ≠ 复刻合格，布局 fidelity 才是用户能否接手的关键。

## 2. 还原布局的标准方法（实测有效）

### 第 1 步：把原版 HTML 变成可真实渲染的静态副本

用户保存的 Next.js / SPA 页面，`file://` 直接打开常报 `Application error: a client-side exception has occurred`，表现为空白——那是脚本加载失败，不是存档坏了。处理：

1. 复制一份 HTML，用正则**去掉所有 `<script>...</script>` 块**、`<script ... />`、`as="script"` 的 link、`rel="manifest"`。
2. 保留本地 CSS 的 `<link>` 和 `<img>`。
3. 把 `<img src>` 里指向 `_files` 的相对路径，替换为**已上传到媒体库的本站附件 URL**（借用上传阶段的 id→url 映射）；删除 `srcset` / `sizes`，避免浏览器去取 404 的 CDN 原图。
4. 把静态副本和它引用的 `_files` 目录一起放到目标站根目录（同源），用 `http://<站>/<副本>.html` 打开。

这样浏览器渲染出的就是**原版真实视觉**（真实 CSS、真实图片、真实栅格），截图可作金标准。

### 第 2 步：注入脚本量出真实像素尺寸

在静态副本 `</body>` 前注入测量脚本，对每个关键元素读 `getBoundingClientRect()` 与 `getComputedStyle()`：

```js
window.addEventListener('load', function(){
  setTimeout(function(){
    function info(el){var r=el.getBoundingClientRect(),c=getComputedStyle(el);
      return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),
              fs:c.fontSize,dir:c.flexDirection,cols:c.gridTemplateColumns,bg:c.backgroundColor};}
    var out={imgs:[],heads:[],sections:[]};
    document.querySelectorAll('img').forEach(function(im,i){var r=im.getBoundingClientRect();if(r.width<1)return;
      out.imgs.push({i:i,src:decodeURIComponent((im.src||'').split('/').pop()).slice(0,45),
        alt:(im.alt||'').slice(0,35),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});});
    ['h1','h2','h3'].forEach(function(t){document.querySelectorAll(t).forEach(function(el){
      var r=el.getBoundingClientRect();if(r.width<1)return;
      out.heads.push({tag:t,txt:(el.textContent||'').trim().slice(0,38),x:Math.round(r.x),y:Math.round(r.y),
        w:Math.round(r.width),fs:getComputedStyle(el).fontSize});});});
    document.querySelectorAll('main section').forEach(function(el,i){var o=info(el);o.i=i;out.sections.push(o);});
    var pre=document.createElement('pre');pre.id='MEASURE_OUT';
    pre.textContent='MEASURE_JSON='+JSON.stringify(out);document.body.appendChild(pre);
  },2000);
});
```

用 Chrome headless `--dump-dom` 抓 `MEASURE_JSON`，存成 `orig_measure.json`。从 x 坐标能反推栅格列数，从 w/h 能反推图片比例与固定尺寸，从 fs 能反推字号层级。

### 第 3 步：按测量数据建页，而不是按想象建页

- 页面内容宽度 = 标题/区块的 `w`（如实测 1200px）。
- 分栏：由左右元素的 x 坐标是否重叠判断（左 x=104、右 x=756 → 左右分栏）。
- 图片尺寸：优先用测得的**固定像素值**（如色卡 89×89、配件图 182×182、主图 520×520），而不是 `width:100%` 任其撑满——这是"图片太大突兀"的根因。
- 字号：H1/H2/各级标题按 `fs` 实测值设（如 H1 56px、H2 40px），不要用通用的 38/32。
- 区块顺序、卡片列数（3+2、2 列、6 列等）严格按 x 坐标分组还原。
- 把测量值整理成一组样式常量（S_H1/S_H2/S_H3_*/S_P/S_IMG_*）在 build-composition 里统一复用。

### 第 4 步：改动大时重建，不要零敲碎打

当对照发现布局差异是**结构性**的（分栏方式、区块顺序、卡片列数变了），用 `manage-elements` 删除旧根容器，按测量数据重新 `build-composition`，比逐个元素 patch 更干净、更不易出错。改动后是草稿，必须 `publish-document`。

### 第 5 步：对照复核

把新页面与原版静态副本各截一张同宽截图，逐区块比对；再做三端实测（见 measure-iframe.html）。布局对齐 + 溢出为 0 才算完成。

## 3. 实测尺寸基线（NatureTough WPC Decking 产品页，1440px 视口）

以下数值是真实测得，可作为复杂产品落地页的参考基线（遇到相似页面可直接复用，但仍应自己量一遍）：

| 项目 | 实测值 |
|---|---|
| 内容区宽度 | 1200px（左边距 104px） |
| H1 / H2 | 56px / 40px |
| 规格小标题 / 配件标题 / 特性标题 | 20px / 16px / 14px |
| Hero | 左右分栏；左侧 H1 + 4 列 2 行特性图标（32×32），右侧主图 520×520 方图 |
| Profile 型材图 | 246×54 |
| Surface Treatment 图 | 268×268 |
| Color 色卡 | 89×89（5 列 2 行） |
| More Profiles 图 | 246×56（2 列 3 行） |
| 规格右栏展示图 | 486×486，下方 4 认证 2×2（认证图 130×80） |
| 配件卡片 | 首行 3 个 + 次行 2 个；每张配件图 182×182 方图 |
| Installation | 左侧 16px 竖排文字步骤列表 + 右侧 3 个视频封面（16/9） |
| More Products | 2 列，左图 272×204 + 右文字 |
| Be Inspired | 方图墙（6 列） |
| Guide | 文字叠在 588×331 图上 |

## 4. 反面清单（这次踩过的坑，务必避免）

- ❌ 左右分栏做成上下堆叠
- ❌ 520×520 方图做成满宽 16/9 大图（"图片太大突兀"的直接来源）
- ❌ 89×89 色卡做成 160px 大方块
- ❌ 182×182 配件图做成半卡片宽的 3:2 大图
- ❌ 认证从规格区右栏的 2×2 挪出来变成独立整行区块
- ❌ 竖排文字步骤做成网格方块
- ❌ 2 列左图右文做成 3 列图文卡片
- ❌ 用通用字号（38/32）覆盖原版实测字号（56/40）

> 一句话总结：**先真实渲染量尺寸，再按量到的布局一比一搭；宁可文案略有取舍，也不动原版骨架。**
