# General Report 独立阅读页设计 QA

- source visual truth path: `/var/folders/dp/dwbdn3jx1j36lscl0cpz0g5w0000gn/T/codex-clipboard-7fb53689-faa8-4a52-9efc-a2a555d742eb.png`
- implementation desktop screenshot: `/Users/calin/Documents/PhD Application 2/Trident/qa-report-desktop-viewport.jpg`
- implementation mobile screenshot: `/Users/calin/Documents/PhD Application 2/Trident/qa-report-mobile-viewport.jpg`
- source pixels: 1998 × 1239
- desktop viewport / pixels: CSS 1440 × 1000; capture 1425 × 990; density 1
- mobile viewport / pixels: CSS 390 × 844; capture 375 × 812; density 1
- state: completed General Report; display settings persisted as 报告宋体 + 宽屏

## Full-view comparison evidence

源截图的核心问题是报告继续嵌在研究工作台中、Markdown 标记按原始文本显示、长行溢出。实现将 General Report 移至无侧栏、无前序节点的独立路由，限制正文阅读宽度，按语义渲染标题、正文、列表、表格和链接。桌面首屏保留报告身份、摘要和正文起点；移动端在 390px 视窗下无横向溢出。

## Focused region comparison evidence

- 标题与正文：标题层级、正文行距、中文换行和长链接均由报告排版样式控制，不再使用 `pre`。
- 市场规模表：表头、数字行与边界在桌面和移动端保持结构，窄屏时仅表格容器可横向滚动，不影响整页。
- 显示设置：已实际操作字体和页面宽度选择器；设置保存在当前浏览器，刷新后继续生效。
- 交互：返回工作台、显示设置、打印 / 保存 PDF 均可见；浏览器控制台无 warning/error。

## Comparison history

1. P1：初次测试底稿写入了字面量 `\\n`，导致 Markdown 被识别为一个超长标题。修正测试数据为真实换行后，标题、列表和表格均被正确解析。
2. P2：报告 Markdown 自带的 H1 与页面 masthead 标题重复。实现增加同名首个 H1 去重；复测正文不再产生重复 H1，masthead 保留唯一报告标题。
3. P2：首次 full-page 移动截图在浏览器拼接时出现视觉压缩，但 DOM 实测文档宽 351px、正文宽 309px且无横向溢出。改用稳定的视窗截图复核，移动布局正常。

## Required fidelity surfaces

- Fonts and typography: 通过；专业无衬线、报告宋体、系统字体可切换，标题 28–48px、正文 14–21px、行距 1.4–2.2 可调。
- Spacing and layout rhythm: 通过；桌面为居中纸张式阅读面，移动端缩减内边距并维持章节节奏。
- Colors and visual tokens: 通过；沿用 Trident 深蓝、青绿色和柔和警示色；标题与正文颜色均可调。
- Image quality and asset fidelity: 不适用；源页面和实现均无必须复刻的图像资产。
- Copy and content: 通过；独立报告页不显示研究流程，只保留报告元数据、未完全回答问题与正式正文。

## Primary interactions tested

- 打开独立报告路由
- 展开显示设置
- 切换报告宋体
- 切换宽屏阅读宽度
- 刷新后确认设置持久化
- 390px 移动端响应式检查
- 控制台错误检查（0）

## Findings

无剩余 P0/P1/P2 问题。

## Follow-up polish

- P3：未来接入 Word/PDF 服务后，可让网页显示设置同步写入导出请求，完全复刻 Streamlit 的多格式一致性。

final result: passed
