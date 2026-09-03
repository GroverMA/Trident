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
  model_calls: unknown[];
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
    step_run_count: number;
    failed_step_count: number;
    model_call_count: number;
    total_tokens: number;
    average_tokens_per_completed_report?: number | null;
    sensing_run_count: number;
    sensing_failed_or_partial_count: number;
    pending_sensing_notification_count: number;
  };
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

function duration(milliseconds: number) {
  if (milliseconds < 1000) return `${milliseconds} ms`;
  if (milliseconds < 60_000) return `${(milliseconds / 1000).toFixed(1)} s`;
  return `${(milliseconds / 60_000).toFixed(1)} min`;
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
              ["项目总数", number(data.summary.project_count), "已进入系统的研究项目"],
              ["模型 Token", number(data.summary.total_tokens), "供应商返回的真实 usage"],
              ["步骤运行", number(data.summary.step_run_count), `${number(data.summary.model_call_count)} 次模型调用`],
              ["完成报告", number(data.summary.completed_report_count), `平均 ${number(data.summary.average_tokens_per_completed_report)} Token/份`],
              ["失败步骤", number(data.summary.failed_step_count), "可按下方明细定位重试"],
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
              <div className="opsPanelTitle"><div><span>Latency</span><h2>步骤平均耗时</h2></div></div>
              <div className="opsLatencyList">
                {byStep.map(([step, item]) => (
                  <div key={step}><span>{stepLabels[step] ?? step}</span><strong>{duration(item.duration / item.runs)}</strong></div>
                ))}
                {!byStep.length ? <p className="opsEmpty">暂无新埋点数据。</p> : null}
              </div>
            </article>
          </section>

          <section className="opsPanel opsTablePanel">
            <div className="opsPanelTitle"><div><span>Run Log</span><h2>最近步骤运行</h2></div><small>最多显示最近 100 条</small></div>
            <div className="opsTableWrap"><table className="opsTable">
              <thead><tr><th>开始时间</th><th>项目</th><th>步骤</th><th>状态</th><th>模型调用</th><th>Token</th><th>耗时</th></tr></thead>
              <tbody>{runs.slice(0, 100).map((run) => (
                <tr key={run.run_id}>
                  <td>{new Date(run.started_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" })}</td>
                  <td>{run.project_name}</td><td>{stepLabels[run.step] ?? run.step}{run.task_id ? ` · ${run.task_id}` : ""}</td>
                  <td><span className={`opsStatus ${run.status === "failed" ? "failed" : ""}`}>{run.status === "failed" ? "失败" : "完成"}</span></td>
                  <td>{run.model_calls.length}</td><td>{number(run.total_tokens)}</td><td>{duration(run.duration_ms)}</td>
                </tr>
              ))}</tbody>
            </table></div>
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

          <footer className="opsSource">数据源：{data.source}。覆盖从本次埋点上线后的新模型调用开始，历史调用不作推算回填。</footer>
        </>
      ) : null}
    </main>
  );
}
