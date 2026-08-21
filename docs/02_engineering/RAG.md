# RAG and Knowledge Retrieval

## 1. Overview

Trident 的 RAG 目标不是简单“把文件放进向量库”，而是把公开证据、企业一手信息、行业方法、历史判断和审阅记录放在清晰权限与证据边界下检索。当前代码以搜索、文件解析和 Evidence Matrix 为主，完整向量检索与企业知识图谱属于演进能力。

## 2. Knowledge Domains

- Research SOP 与 Skill 指令。
- Industry Pack：术语、分类、指标和常用来源。
- 公开网页、政策、公司披露与专业报告。
- 企业上传文件与自我诊断。
- 项目历史、报告版本、审阅意见和决策记录。
- Benchmark & Case Library。

## 3. Ingestion

1. 校验格式、大小、病毒和敏感级别。
2. 提取文本、表格、页码、工作表和幻灯片位置。
3. 保存原始文件哈希、来源、责任人、日期和战略关系。
4. 生成可检索片段，但保留回到原文件位置的映射。
5. 企业资料必须先经接受/拒绝/删除审核。

## 4. Chunking

- 以文档结构为优先：章节、段落、表格、页/幻灯片，而不是固定字符硬切。
- 表格保留标题、表头、单位和脚注。
- 政策文件保留条款与发布机关。
- 研究报告保留章节标题与时间范围。
- Chunk 需要适度重叠，但避免重复证据被误认为多个独立来源。

## 5. Metadata

每个片段至少记录：tenant、project、source type、title、URL/file、published_at、retrieved_at、page/sheet/slide、industry、region、time range、sensitivity、review status、source quality、hash。

## 6. Embedding Strategy

- Embedding provider 必须可替换。
- 中文、英文和专业缩写需要统一评估。
- 敏感企业资料仅使用授权区域内模型或本地模型。
- 更换 embedding 模型时保留版本并支持重新索引。

## 7. Retrieval

采用混合检索：关键词/BM25 + 向量召回 + metadata filters。研究问题先改写为多个检索意图，但最终按问题覆盖、来源多样性与用户目标聚合，不以“每个子问题都必须找到高分来源”作为无限补检条件。

## 8. Ranking and Re-ranking

排序因素：

- 与原始 Prompt 的相关性。
- 对当前研究模块的直接支持程度。
- 来源权威性与发布日期。
- 地区、时间和市场口径匹配。
- 是否为独立来源而非重复转载。
- 是否已经过人工接受。

系统推荐应优先少量最相关、质量较高的证据，而不是简单展示最高分的全部内容。

## 9. Context Construction

- 区分事实、数据、来源观点、分析推断和内部管理假设。
- 同一数字存在冲突时并列来源、统一口径并计算合理区间。
- 企业上下文按战略问题最小化提供，不把全部机密文件塞给模型。
- 报告正文不显示内部 ID，引用通过脚注、链接和附录呈现。

## 10. Cache

缓存搜索结果、网页正文、解析文件、embedding 和重排结果。缓存键包含来源哈希、解析/模型版本、租户和权限；敏感结果不可跨租户复用。

## 11. Evaluation

评估召回率、引用正确率、来源多样性、答案支持率、重复率、权限泄漏率和单位检索成本。建立固定行业案例与跨行业回归集。

## 12. Future

- PostgreSQL + pgvector 或独立向量服务。
- 企业时间化记忆和知识图谱。
- Query planner 自动选择网页、内部数据或专业数据库。
- 基于审阅反馈训练 reranker 与检索策略，而不是直接微调生成模型。
