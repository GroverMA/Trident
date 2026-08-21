# Deployment Guide

## 1. Environments

| Environment | Purpose | Data |
|---|---|---|
| development | 本地开发与调试 | 本地模拟数据 |
| test | 自动化测试 | 临时数据库 |
| staging | 预发布和验收 | 脱敏/合成数据 |
| production | 对外服务 | 正式租户数据 |

## 2. Current Deployment Paths

### Dual-region invariant

- Vercel 与 CloudBase 是同一应用版本的不同区域承载方式。
- 两者必须共享研究流程、产品功能、FastAPI/Next.js 代码、领域与 API 契约、数据库迁移、
  Skill/Prompt 版本及回归测试。
- 允许不同的只有域名、构建清单、云资源、环境变量、Secret、Provider Endpoint、数据库/
  对象存储实例、扩缩容和合规设置。
- 不允许使用长期存在的 `china-feature` / `overseas-feature` 业务分支；区域兼容由配置和
  Adapter 解决，并在同一主干测试。

### Overseas

- Next.js 可继续使用 Vercel。
- 当前公开地址：`https://trident-research.vercel.app`。
- 2026-08-18 公网验收：首页与 `/api/projects` 均返回 HTTP 200。
- FastAPI、数据库和长任务使用独立后端服务。
- Vercel 版本与中国版本共用同一代码库，通过环境配置区分。
- 当前融资与产品验证阶段以 Vercel 为主 Demo；可将自有品牌子域名通过 Vercel 提供的
  CNAME 记录接入。自有域名只改变品牌入口，不把 Vercel 转换为中国大陆节点。

### China Demo

- 腾讯云 CloudBase 云托管容器。
- 2026-08-18 产品决策：当前阶段降级为中国大陆商业化部署预研和未来实现参考，不作为
  融资 Demo 的发布阻塞条件；仍禁止建立独立业务分支或删减共享研究能力。
- 当前默认域名：`https://trident-web-298210-7-1470031105.sh.run.tcloudbase.com`。
- 仓库根目录 `Dockerfile` 是 CloudBase 实际构建入口，并与
  `deploy/cloudbase/Dockerfile` 保持同步；容器同时启动 Next.js（公网 3000）和
  FastAPI（内部 8000）。
- CloudBase 公网访问端口映射至服务端口 3000。
- SQLite Demo 需要持久挂载 `/app/data`、单实例写入和 `WEB_CONCURRENCY=1`。
- 2026-08-18 状态：镜像已构建、容器运行正常，用户从中国大陆本地网络确认默认域名
  可访问。CloudBase 会隔离部分境外或自动化网络，因此外部 TLS 超时不等于服务故障；
  大陆版健康和端到端验收必须从目标区域网络执行。
- 2026-08-18 发布排查：GitHub 当前没有 `TCB_SECRET_ID`、`TCB_SECRET_KEY`、
  `TCB_ENV_ID`，也没有执行 `tcb cloudrun deploy` 的工作流。现有 CI 的 `container`
  job 只证明 CloudBase 镜像可以构建和启动，不会创建云托管新版本。因此 Vercel 自动更新而
  CloudBase 保持旧版本是发布触发缺失，不是业务代码分叉。
- 解决方式二选一，但必须固定一种并纳入发布清单：在 CloudBase 服务设置中把公开仓库
  `GroverMA/Trident` 的 `main` 绑定为自动部署分支；或在 GitHub Secrets 配置上述三个
  Secret，并由受保护的 GitHub Actions 执行
  `tcb cloudrun deploy -e "$TCB_ENV_ID" -s trident-agent-cn --port 3000 --force`。
  Secret 只允许进入平台密钥库，不写入仓库、日志或 Knowledge Base。
- **控制台识别规则**：若页面标题为“更新容器镜像部署”且要求填写“镜像地址”，当前服务
  就是镜像发布模式；这个页面不会显示 GitHub 分支，也不能通过把镜像名改成 `main` 来完成
  源码绑定。应返回服务创建/部署入口，选择“代码仓库/Git 仓库”方式并绑定
  `GroverMA/Trident` 的 `main`；若当前个人版控制台不提供该方式，则保留镜像模式，并由
  GitHub Actions 使用提交 SHA 构建镜像、推送镜像仓库、创建 CloudBase 新版本和切流。
  两种方式都必须在部署记录中保存 Git SHA，禁止长期使用含义不清的浮动镜像标签。

### Standard SaaS

- Web、API、Worker、Redis、PostgreSQL 和对象存储拆分。
- 报告生成由后台任务运行，前端通过轮询或事件获取进度。

## 3. Essential Environment Variables

只列变量名与含义，不在文档保存实际值。

| Variable | Purpose |
|---|---|
| `TRIDENT_ENV` | development/test/staging/production |
| `TRIDENT_DATABASE_MODE` | `sqlite` 或 `database_url` |
| `TRIDENT_DATABASE_PATH` | SQLite 文件路径 |
| `DATABASE_URL` | PostgreSQL/MySQL 可写连接串 |
| `TRIDENT_API_URL` | Next.js BFF 访问 FastAPI 的内部地址 |
| `WEB_CONCURRENCY` | API worker 数；SQLite Demo 使用 1 |
| `HKGAI_MODEL_BASE_URL` | 模型服务 Base URL |
| `HKGAI_MODEL_NAME` | 模型名称 |
| `HKGAI_MODEL_API_KEY` | 模型 API 凭证 |
| `HKGAI_MODEL_TIMEOUT_SECONDS` | 模型超时 |
| `HKGAI_SEARCH_TRANSPORT` | REST 或 MCP |
| `HKGAI_APP_NAME` | 搜索应用名称 |
| `HKGAI_APP_KEY` | 搜索应用凭证 |
| `HKGAI_AGENTHUB_ENDPOINT` | 搜索 Agent 端点 |
| `HKGAI_SEARCH_BASE_URL` | 搜索 REST Base URL |
| `HKGAI_SEARCH_MCP_URL` | 搜索 MCP URL |
| `HKGAI_SEARCH_TIMEOUT_SECONDS` | 搜索超时 |
| `TZ` | 运行时区 |

## 4. Build

- Python 依赖由 `pyproject.toml` 管理。
- Web 依赖由 `web/package.json` 和 pnpm lockfile 管理。
- 容器构建必须包含运行时依赖，不依赖构建机器全局缓存。
- 构建阶段不得把 `.env` 或密钥复制进镜像层。

## 5. Health Checks

- 容器入口：首页或明确 health endpoint。
- FastAPI `/health` 检查进程。
- FastAPI `/ready` 检查数据库和关键依赖。
- 单容器 CloudBase 对外提供 Next.js `/healthz` 与 `/readyz`，分别代理上述 FastAPI
  探针，使公网和平台无需暴露内部 8000 端口即可检查完整服务链路。
- 就绪检查失败的实例不接收流量。

## 6. CI/CD

推荐流水线：

1. 格式与静态检查。
2. Python、Web、provider、reviewer 两条流程测试。
3. Secret scan 和依赖安全检查。
4. 构建镜像并运行 smoke test。
5. 部署 staging。
6. 运行端到端报告生成和回滚检查。
7. 人工批准 production。

双区域发布矩阵要求每个功能提交记录以下结果：共享单元/合同测试、海外构建、CloudBase
镜像构建、两个区域健康/就绪检查，以及受影响研究路径的端到端测试。任一格未通过，发布
状态为“部分部署”而非“完成”。

同提交门禁：Vercel 和 CloudBase 必须记录同一个 Git SHA；CloudBase 不能再以“容器 CI
通过”代替“新版本已创建且流量已切换”。如果 CloudBase 控制台使用 Git 自动部署，服务
必须绑定 `main`，避免主干已更新但试验分支/旧构建仍被发布。

## 7. Database Modes

- 本地开发默认 SQLite。
- staging/production 默认要求 `DATABASE_URL`。
- 中国融资 Demo 可显式设置 SQLite，但不可静默 fallback。
- 切换 PostgreSQL 前运行迁移并校验项目、版本和文件引用。

## 8. Rollback

- 镜像采用不可变版本标签。
- 数据库 migration 必须有兼容窗口。
- 应用回滚不应覆盖新版本产生的数据。
- 报告和 Artifact 版本不可因部署回滚而丢失。

## 9. Monitoring

监控 CPU、内存、磁盘、实例重启、API p95、任务队列、错误率、模型/搜索依赖、数据库连接、报告成功率与成本。生产环境接入 Sentry 或等价错误监控与集中日志。

## 10. Maintenance

- 每月更新依赖并运行回归测试。
- 定期轮换密钥与检查过期凭证。
- 验证备份恢复。
- 清理临时抓取内容、缓存与过期文件。
- 复核模型和搜索供应商可用性与价格。

## 11. Deployment Acceptance

一次部署只有在以下条件满足后才算完成：两种研究路径能创建项目、确认范围、生成完整报告；企业路径能处理资料、生成 Scorecard 与 Action Plan；Word/PDF 可下载；历史项目可恢复；日志无明文密钥；线上 URL 可从目标地区访问。

容器状态为“运行正常”只代表实例存活，不等于部署验收完成。公网域名必须能够完成
TLS 握手、首页返回 200，且 `/api/projects` 可用，之后才能执行会写入测试数据的端到端验收。
