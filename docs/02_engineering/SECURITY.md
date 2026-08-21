# Security and Privacy

## 1. Principles

1. 最小权限与默认拒绝。
2. 租户数据严格隔离。
3. 企业资料只用于明确授权的项目。
4. 证据、判断和行动保留责任链。
5. 密钥不进入仓库、前端、截图、报告或日志。
6. Demo 限制必须显式，不把演示配置包装成企业安全能力。

## 2. Authentication

- Demo 可使用平台访问控制。
- SaaS 使用安全 Session/OIDC，支持 MFA。
- 企业版支持 SSO/SAML/OIDC 与生命周期管理。

## 3. Authorization

角色示例：Owner、Research Lead、Analyst、Reviewer、Management Viewer、System Admin。权限在 tenant、workspace、project、artifact、document 层分别控制。研究方式不是身份或权限。

## 4. Data Classification

| Level | Example | Handling |
|---|---|---|
| Public | 公开政策和网页 | 可用于公开 Demo |
| Desensitized / Simulated | 脱敏案例与模拟数据 | 经确认后可用于演示 |
| Internal | 内部经营资料 | 限项目和授权人员 |
| Confidential / Restricted | 订单、客户、价格、个人数据 | 强加密、限制模型和导出 |

## 5. Secrets Management

- 使用部署平台 Secret 或 KMS。
- 环境变量只保存引用或运行时密钥。
- `.env` 不提交；`.env.example` 只列变量名。
- 任何曾出现在公开截图或聊天中的密钥应立即轮换。
- 定期扫描 Git 历史和构建日志中的秘密。

## 6. Enterprise File Security

- 支持接受、拒绝和删除。
- 拒绝资料不得进入企业证据或模型上下文。
- 上传后进行格式、大小、恶意文件和敏感性检查。
- 原文件存对象存储，使用短时签名 URL。
- 删除需覆盖索引、缓存、解析文本与派生产物的处置规则。

## 7. Model and Tool Privacy

- 记录不同模型供应商的数据使用与保留政策。
- 高敏资料可限制为企业私有模型/区域。
- Prompt 注入内容不能改变系统权限和数据边界。
- 搜索/抓取工具禁止访问内网与 metadata endpoints。

## 8. Logging and Audit

日志包含 request ID、用户、租户、项目、操作、状态和耗时；不得含明文密钥和大段企业原文。审计日志应防篡改，保留下载、删除、审批、模型调用和报告版本事件。

## 9. Compliance Roadmap

根据客户地域与行业逐步建立：数据处理协议、个人信息清单、跨境评估、保留与删除机制、供应商清单、安全测试和事件响应。不得在尚未完成审计时宣称通过特定认证。

## 10. Incident Response

1. 识别并隔离受影响服务。
2. 轮换相关凭证。
3. 保存日志与证据。
4. 评估租户和数据范围。
5. 按合同与法规通知。
6. 完成根因、修复和回归测试。

## 11. Security Release Gate

上线前至少检查：依赖漏洞、secret scan、鉴权、越权、文件上传、SSRF、Prompt injection、租户隔离、导出权限、备份恢复与日志脱敏。
