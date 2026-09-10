import { tridentApiUrl } from "@/lib/api";

export const dynamic = "force-dynamic";

interface OpsRun {
  run_id: string;
  project_id: string;
  project_name: string;
  step: string;
  task_id?: string | null;
  status: string;
  started_at: string;
  duration_ms: number;
  completed_at: string;
  model_calls: Array<{
    call_id: string;
    model: string;
    duration_ms: number;
    prompt_tokens: number;
    completion_tokens: number;
    reasoning_tokens: number;
    cached_tokens: number;
    total_tokens: number;
  }>;
  prompt_tokens: number;
  completion_tokens: number;
  reasoning_tokens: number;
  cached_tokens: number;
  total_tokens: number;
}

interface OpsPayload {
  generated_at: string;
  source: string;
  coverage_started_at?: string | null;
  summary: {
    project_count: number;
    completed_report_count: number;
    started_workflow_count: number;
    report_completion_rate?: number | null;
    step_run_count: number;
    failed_step_count: number;
    model_call_count: number;
    total_tokens: number;
    average_tokens_per_completed_report?: number | null;
    median_tokens_per_completed_report?: number | null;
    p75_tokens_per_completed_report?: number | null;
    p95_tokens_per_completed_report?: number | null;
    median_report_duration_ms?: number | null;
    sensing_run_count: number;
    sensing_failed_or_partial_count: number;
    pending_sensing_notification_count: number;
  };
  data_quality: {
    last_event_at?: string | null;
    usage_missing_call_count: number;
    aggregation_scope: string;
  };
  models: Array<{
    model: string;
    calls: number;
    tokens: number;
    duration_ms: number;
    average_tokens: number;
    average_duration_ms: number;
  }>;
  projects: Array<{
    project_id: string;
    project_name: string;
    scenario_pack: string;
    research_path: string;
    status: "completed" | "in_progress";
    started_at?: string | null;
    completed_at?: string | null;
    wall_duration_ms: number;
    active_duration_ms: number;
    review_input_duration_ms: number;
    excluded_idle_duration_ms: number;
    step_run_count: number;
    failed_step_count: number;
    model_call_count: number;
    models: string[];
    prompt_tokens: number;
    completion_tokens: number;
    reasoning_tokens: number;
    cached_tokens: number;
    total_tokens: number;
    aggregation_scope: "current_report" | "project_to_date";
  }>;
  runs: OpsRun[];
  sensing_runs: Array<{
    run_id: string; project_id: string; project_name: string; started_at: string;
    status: "succeeded" | "partial" | "failed"; duration_ms: number; new_signal_count: number;
    source_success_count: number; source_failure_count: number;
    connector_success_count: number; connector_failure_count: number; errors: string[];
  }>;
  sensing_notifications: Array<{
    notification_id: string; project_id: string; project_name: string; created_at: string;
    notification_type: "high_impact_signal" | "source_failure" | "connector_failure";
    severity: "critical" | "warning"; title: string; message: string; target_ref: string;
    status: "pending" | "acknowledged" | "closed"; delivery_channels: string[];
  }>;
}

const stepLabels: Record<string, string> = {
  research_brief: "Prompt Analysis / Gate 0",
  research_planning: "Research Planning",
  evidence_collection: "Web Research",
  industry_analysis: "Industry Analysis",
  future_intelligence: "Future Intelligence",
  decision_report: "General Report",
  company_assessment: "Company Scorecard",
  action_planning: "Action Plan",
  adaptive_plan: "Adaptive Plan",
  interview_analysis: "AI Diagnostic Interview",
};

function number(value: number | null | undefined) {
  return value == null ? "—" : new Intl.NumberFormat("zh-CN").format(value);
}

function duration(milliseconds: number | null | undefined) {
  if (milliseconds == null) return "—";
  if (milliseconds < 1000) return `${milliseconds} ms`;
  if (milliseconds < 60_000) return `${(milliseconds / 1000).toFixed(1)} s`;
  return `${(milliseconds / 60_000).toFixed(1)} min`;
}

function percentage(value: number | null | undefined) {
  return value == null ? "—" : `${(value * 100).toFixed(1)}%`;
}

function modelNames(run: OpsRun) {
  return [...new Set(run.model_calls.map((call) => call.model))].join("、") || "—";
}

async function loadTelemetry(): Promise<{ data?: OpsPayload; error?: string }> {
  const key = process.env.TRIDENT_OPS_KEY;
  const username = process.env.TRIDENT_OPS_USERNAME;
  const password = process.env.TRIDENT_OPS_PASSWORD;
  if (!key || !username || !password) return { error: "运营监测尚未连接：请在 Web 部署同时配置 TRIDENT_OPS_KEY、TRIDENT_OPS_USERNAME 与 TRIDENT_OPS_PASSWORD。配置后重新部署即可读取真实数据。" };
  try {
    const response = await fetch(tridentApiUrl("/v1/ops/telemetry"), {
      cache: "no-store",
      headers: { "X-Trident-Ops-Key": key },
    });
    if (!response.ok) return { error: `监测数据服务返回 HTTP ${response.status}` };
    return { data: (await response.json()) as OpsPayload };
  } catch {
    return { error: "暂时无法连接研究监测服务。" };
  }
}

export default async function OperationsPage() {
  const { data, error } = await loadTelemetry();
  const runs = data?.runs ?? [];
  const recentRuns = runs.slice(0, 100);
  const runsByProject = Array.from(
    recentRuns.reduce<Map<string, OpsRun[]>>((groups, run) => {
      const group = groups.get(run.project_id) ?? [];
      group.push(run);
      groups.set(run.project_id, group);
      return groups;
    }, new Map()),
  );
  const byStep = Object.entries(
    runs.reduce<Record<string, { tokens: number; duration: number; runs: number; failures: number }>>(
      (summary, run) => {
        const current = summary[run.step] ?? { tokens: 0, duration: 0, runs: 0, failures: 0 };
        current.tokens += run.total_tokens;
        current.duration += run.duration_ms;
        current.runs += 1;
        current.failures += run.status === "failed" ? 1 : 0;
        summary[run.step] = current;
        return summary;
      },
      {},
    ),
  ).sort((a, b) => b[1].tokens - a[1].tokens);
  const maxTokens = Math.max(...byStep.map(([, item]) => item.tokens), 1);

  return (
    <main className="opsPage">
      <header className="opsHeader">
        <div>
          <div className="eyebrow">TRIDENT · PRODUCT OPERATIONS</div>
          <h1>研究运行监测</h1>
          <p>真实模型用量、步骤耗时与流程可靠性。该页面不展示 Prompt、模型正文或密钥。</p>
        </div>
        <div className="opsFreshness">
          <span>数据刷新</span>
          <strong>{data ? new Date(data.generated_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" }) : "不可用"}</strong>
        </div>
      </header>

      {error ? <div className="opsAlert"><strong>运营监测暂不可用</strong><span>{error}</span><small>页面已正常加载，研究主流程不受影响；这里不会用演示数字替代真实用量。</small></div> : null}
      {data ? (
        <>
          <section className="opsMetricGrid">
            {[
              ["完成流程", number(data.summary.completed_report_count), `完成率 ${percentage(data.summary.report_completion_rate)}`],
              ["模型 Token", number(data.summary.total_tokens), `${number(data.summary.model_call_count)} 次真实模型调用`],
              ["单报告 Token", number(data.summary.median_tokens_per_completed_report), `P75 ${number(data.summary.p75_tokens_per_completed_report)} · P95 ${number(data.summary.p95_tokens_per_completed_report)}`],
              ["单报告耗时", duration(data.summary.median_report_duration_ms), "有效执行与人工响应耗时中位数"],
              ["失败步骤", number(data.summary.failed_step_count), `${number(data.summary.step_run_count)} 次步骤运行`],
              ["待处理通知", number(data.summary.pending_sensing_notification_count), "高影响信号与自动感知异常"],
            ].map(([label, value, note]) => (
              <article className="opsMetric" key={label}>
                <span>{label}</span><strong>{value}</strong><small>{note}</small>
              </article>
            ))}
          </section>

          <section className="opsGrid">
            <article className="opsPanel">
              <div className="opsPanelTitle"><div><span>Token Mix</span><h2>步骤用量分布</h2></div><small>按累计 Token 排序</small></div>
              {byStep.length ? byStep.map(([step, item]) => (
                <div className="opsBarRow" key={step}>
                  <div><strong>{stepLabels[step] ?? step}</strong><span>{item.runs} 次 · {item.failures} 失败</span></div>
                  <div className="opsBarTrack"><i style={{ width: `${Math.max(3, item.tokens / maxTokens * 100)}%` }} /></div>
                  <b>{number(item.tokens)}</b>
                </div>
              )) : <p className="opsEmpty">新的 AI 研究步骤执行后，这里将出现真实用量。</p>}
            </article>

            <article className="opsPanel">
              <div className="opsPanelTitle"><div><span>Model Mix</span><h2>模型调用分布</h2></div><small>实际返回模型</small></div>
              <div className="opsLatencyList">
                {data.models.map((item) => (
                  <div key={item.model} className="opsModelRow">
                    <span><b>{item.model}</b><small>{item.calls} 次调用 · 平均 {duration(item.average_duration_ms)}</small></span>
                    <strong>{number(item.tokens)} Token</strong>
                  </div>
                ))}
                {!data.models.length ? <p className="opsEmpty">暂无模型调用数据。</p> : null}
              </div>
            </article>
          </section>

          <section className="opsPanel opsTablePanel">
            <div className="opsPanelTitle"><div><span>Workflow Cost</span><h2>报告与场景流程总消耗</h2></div><small>实际步骤耗时 + 每段人工响应最多 10 分钟</small></div>
            <div className="opsTableWrap"><table className="opsTable">
              <thead><tr><th>项目 / 场景</th><th>状态</th><th>模型</th><th>步骤 / 调用</th><th>Prompt</th><th>Completion</th><th>Reasoning</th><th>Cached</th><th>总 Token</th><th>有效耗时</th></tr></thead>
              <tbody>{data.projects.map((project) => (
                <tr key={project.project_id}>
                  <td><strong>{project.project_name}</strong><small className="opsCellMeta">{project.scenario_pack} · {project.research_path}</small></td>
                  <td><span className={`opsStatus ${project.status === "completed" ? "" : "pending"}`}>{project.status === "completed" ? "已完成" : "进行中"}</span></td>
                  <td>{project.models.join("、") || "—"}</td><td>{project.step_run_count} / {project.model_call_count}</td>
                  <td>{number(project.prompt_tokens)}</td><td>{number(project.completion_tokens)}</td><td>{number(project.reasoning_tokens)}</td><td>{number(project.cached_tokens)}</td>
                  <td><strong>{number(project.total_tokens)}</strong></td><td>{duration(project.wall_duration_ms)}<small className="opsCellMeta">执行 {duration(project.active_duration_ms)} · 人工 {duration(project.review_input_duration_ms)}</small></td>
                </tr>
              ))}</tbody>
            </table>{!data.projects.length ? <p className="opsEmpty">创建并执行研究项目后，这里会显示完整流程总消耗。</p> : null}</div>
          </section>

          <section className="opsPanel opsTablePanel">
            <div className="opsPanelTitle"><div><span>Run Log</span><h2>最近步骤运行</h2></div><small>按项目折叠 · 最近 100 条</small></div>
            <div className="opsRunGroups">
              {runsByProject.map(([projectId, projectRuns], index) => {
                const totalProjectTokens = projectRuns.reduce((sum, run) => sum + run.total_tokens, 0);
                const failedRuns = projectRuns.filter((run) => run.status === "failed").length;
                return (
                  <details className="opsRunGroup" key={projectId} open={index === 0}>
                    <summary>
                      <span><strong>{projectRuns[0].project_name}</strong><small>{projectRuns.length} 个步骤 · {failedRuns} 个失败</small></span>
                      <span><b>{number(totalProjectTokens)} Token</b><small>最近运行 {new Date(projectRuns[0].started_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" })}</small></span>
                    </summary>
                    <div className="opsTableWrap"><table className="opsTable opsNestedTable">
                      <thead><tr><th>开始 / 完成</th><th>步骤</th><th>状态</th><th>实际模型</th><th>Prompt</th><th>Completion</th><th>Reasoning</th><th>Cached</th><th>总 Token</th><th>耗时</th></tr></thead>
                      <tbody>{projectRuns.map((run) => (
                        <tr key={run.run_id}>
                          <td>{new Date(run.started_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" })}<small className="opsCellMeta">{new Date(run.completed_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" })}</small></td>
                          <td>{stepLabels[run.step] ?? run.step}{run.task_id ? ` · ${run.task_id}` : ""}</td>
                          <td><span className={`opsStatus ${run.status === "failed" ? "failed" : ""}`}>{run.status === "failed" ? "失败" : "完成"}</span></td>
                          <td>{modelNames(run)}<small className="opsCellMeta">{run.model_calls.length} 次调用</small></td>
                          <td>{number(run.prompt_tokens)}</td><td>{number(run.completion_tokens)}</td><td>{number(run.reasoning_tokens)}</td><td>{number(run.cached_tokens)}</td><td><strong>{number(run.total_tokens)}</strong></td><td>{duration(run.duration_ms)}</td>
                        </tr>
                      ))}</tbody>
                    </table></div>
                  </details>
                );
              })}
              {!runsByProject.length ? <p className="opsEmpty">暂无步骤运行记录。</p> : null}
            </div>
          </section>

          <section className="opsPanel opsTablePanel">
            <div className="opsPanelTitle"><div><span>Management Notifications</span><h2>管理层通知队列</h2></div><small>{number(data.summary.pending_sensing_notification_count)} 项待确认</small></div>
            <div className="opsTableWrap"><table className="opsTable">
              <thead><tr><th>创建时间</th><th>项目</th><th>级别</th><th>类型</th><th>事项</th><th>状态</th><th>通知通道</th></tr></thead>
              <tbody>{data.sensing_notifications.slice(0, 100).map((item) => <tr key={`${item.project_id}-${item.notification_id}`}>
                <td>{new Date(item.created_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" })}</td><td>{item.project_name}</td>
                <td><span className={`opsStatus ${item.severity === "critical" ? "failed" : ""}`}>{item.severity === "critical" ? "重要" : "异常"}</span></td>
                <td>{item.notification_type === "high_impact_signal" ? "高影响信号" : item.notification_type === "source_failure" ? "公开来源失败" : "内部连接失败"}</td>
                <td>{item.title}</td><td>{item.status === "pending" ? "待确认" : item.status === "acknowledged" ? "已知悉" : "已关闭"}</td><td>{item.delivery_channels.join("、")}</td>
              </tr>)}</tbody>
            </table>{!data.sensing_notifications.length ? <p className="opsEmpty">当前没有高影响信号或自动感知异常通知。</p> : null}</div>
          </section>

          <section className="opsPanel opsTablePanel">
            <div className="opsPanelTitle"><div><span>Continuous Sensing</span><h2>自动感知运行记录</h2></div><small>{number(data.summary.sensing_run_count)} 次运行 · {number(data.summary.sensing_failed_or_partial_count)} 次需关注</small></div>
            <div className="opsTableWrap"><table className="opsTable">
              <thead><tr><th>开始时间</th><th>项目</th><th>状态</th><th>新增信号</th><th>公开来源</th><th>内部连接器</th><th>耗时</th><th>错误</th></tr></thead>
              <tbody>{data.sensing_runs.slice(0, 100).map((run) => <tr key={run.run_id}>
                <td>{new Date(run.started_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" })}</td><td>{run.project_name}</td>
                <td><span className={`opsStatus ${run.status === "succeeded" ? "" : "failed"}`}>{run.status === "succeeded" ? "完成" : run.status === "partial" ? "部分成功" : "失败"}</span></td>
                <td>{run.new_signal_count}</td><td>{run.source_success_count} 成功 / {run.source_failure_count} 失败</td><td>{run.connector_success_count} 成功 / {run.connector_failure_count} 失败</td><td>{duration(run.duration_ms)}</td><td>{run.errors.join("；") || "—"}</td>
              </tr>)}</tbody>
            </table>{!data.sensing_runs.length ? <p className="opsEmpty">自动感知调度运行后，这里会显示真实来源与连接器健康记录。</p> : null}</div>
          </section>

          <footer className="opsSource">数据源：{data.source}。耗时口径：实际步骤执行时间，加相邻步骤之间的人工审核/输入等待；每段等待最多计入 10 分钟，最后一步结束后的停滞不计入。最后事件：{data.data_quality.last_event_at ? new Date(data.data_quality.last_event_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" }) : "暂无"}；Usage 缺失调用：{number(data.data_quality.usage_missing_call_count)}。Reasoning Token 是 Completion 的明细项时不重复计入总数；总 Token 始终采用供应商返回值。覆盖从埋点上线后的新模型调用开始，历史调用不作推算回填。</footer>
        </>
      ) : null}
    </main>
  );
}
