# 专业研究 Skill 治理与执行规则

## 强制原则

Trident 的行业定义、赛道与产业链、市场规模、竞争格局、驱动因素及其下游未来趋势研究，必须执行仓库中的版本化专业研究 Skill。Skill 不是提示词参考资料，而是研究运行时的强制方法合同。

仓库目录 `knowledge_packs/research_skills/` 是唯一可执行事实源；Knowledge Base 中的说明是面向产品和研究人员的可读镜像。仅修改 Word、Markdown 或 Knowledge Base，不会改变线上 Agent 的研究行为。

## 当前 Skill

| Skill ID | 研究职责 | 当前版本 |
|---|---|---|
| `defining-industry-markets` | 行业定义、边界与统计口径 | 1.0.0 |
| `mapping-tracks-value-chain` | 赛道分类、产业链、价值流与瓶颈 | 1.0.0 |
| `sizing-industry-markets` | 市场规模模型、交叉验证与敏感性 | 1.0.0 |
| `analyzing-industry-competition` | 公司全集、业务映射、可比口径与竞争格局 | 1.0.0 |
| `analyzing-industry-drivers` | 六向扫描、因果链、双重影响与反证 | 1.0.0 |

## 运行规则

1. Prompt Analysis 和 Gate 0 先锁定市场范围，后续节点不得静默改变范围。
2. 每个行业分析模块只加载与其职责匹配的 Skill；Future Intelligence 继承全部已批准的专业方法输出。
3. 每个研究产物必须保存 SOP ID、SOP 版本、Skill ID、Skill 版本和内容 SHA-256。
4. Skill 的硬失败条件优先于模型的顺畅输出；不满足条件时必须要求人工确认、降级结论或退回上一节点。
5. Vercel 与腾讯云必须从同一 `main` 分支和同一 Skill 目录构建，允许模型供应商不同，不允许研究方法不同。

## 更新流程

1. 在 GitHub 仓库中修改对应 `SKILL.md` 与 `manifest.json`。
2. 语义或判定规则变化时提升版本号；只修正文案也至少提升补丁版本。
3. 补充或更新单元测试与代表性研究评测，确认模块选择、硬失败和输出合同。
4. 通过代码审查后合并 `main`，再由两种部署方式同步构建。
5. 更新 Knowledge Base 的人类可读说明和变更记录。
6. 已生成产物保留原 Skill 版本与哈希；若范围或关键方法变化，相关下游节点必须失效并重新生成。

## 禁止事项

- 不得把尚未进入仓库的附件内容当作线上已生效方法。
- 不得在应用代码中复制一份无法追踪版本的临时 Prompt。
- 不得让 Vercel 与腾讯云分别维护不同研究规则。
- 不得覆盖旧产物的历史方法版本；重新运行应产生新的审计记录。
