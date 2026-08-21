# MCP Integration

## 1. Overview

Model Context Protocol（MCP）用于将外部工具以可发现的方式暴露给 Agent。Trident 当前最相关的 MCP 是搜索与网页抓取；REST 仍保留为确定性和部署兼容性更高的调用方式。

## 2. Connected / Supported MCPs

| MCP | Tools | Status |
|---|---|---|
| Search Platform MCP | `search_web`, `crawl_page` | 已验证接入方式；生产环境可按部署配置选择 MCP 或 REST |
| Enterprise Connectors | CRM/ERP/Data Warehouse tools | 规划能力 |
| Internal Knowledge MCP | 企业知识检索、权限过滤 | 规划能力 |

## 3. Authentication

- 搜索 MCP 使用服务端请求头凭证。
- 凭证保存在 Secret Manager 或部署平台环境变量中。
- 不把 App Name、App Key 或其他凭证写进前端、文档示例和日志。
- 不同租户连接企业 MCP 时必须使用独立凭证和授权边界。

## 4. Inputs and Outputs

### `search_web`

- Input: `query`。
- Output: 结构化搜索结果、标题、URL、摘要和相关元数据。

### `crawl_page`

- Input: `url`。
- Output: 网页正文或抓取结果信封。

应用层必须解析 MCP 响应信封，并将外部结果映射为内部 `Source` 和 `Evidence`，不能让供应商原始结构渗透到报告层。

## 5. Tool Discovery

Agent 连接 MCP 后先调用 `tools/list` 获取工具目录。工具选择需受研究任务和预算约束，不能让模型无界限反复调用。

## 6. Failure Handling

- MCP 连接或工具发现失败时可切换 REST provider。
- 单个页面抓取失败不应终止整个任务。
- 记录失败原因、URL 和重试次数。
- 对慢调用设置超时；对 429/5xx 使用有限退避。
- 响应结构变化时通过 adapter 和 schema validation 隔离。

## 7. Security

- 防止模型提交内网地址、文件地址或敏感 URL 给外部抓取器。
- 对 URL 做协议、域名、重定向和大小限制。
- 企业内部检索结果不得发送到未经授权的外部模型。
- MCP 工具调用保留审计事件，但日志脱敏。

## 8. When to Use MCP vs REST

| Situation | Preferred |
|---|---|
| Agent 需要动态发现并选择搜索/抓取工具 | MCP |
| 固定流程、严格参数、易于重试与测试 | REST |
| 供应商 MCP 在目标地区连接不稳定 | REST fallback |
| 企业内部工具目录和权限动态变化 | MCP |

## 9. Future Expansion

- 政策数据库 MCP。
- 招股书、公告与专业行业数据库 MCP。
- 企业 CRM/ERP/BI MCP。
- 投资标的资料室 MCP。
- 工具信誉、成本、延迟和数据地域路由。
