"""Built-in delivery surfaces for the first integration architecture phase."""

from __future__ import annotations

from src.integrations.contracts import IntegrationOperation, IntegrationSurface


COMMON_OPERATIONS = (
    IntegrationOperation(
        "create_project",
        "Create a scenario-bound project from a compact intake.",
        "available",
        "synchronous",
        mutates_state=True,
    ),
    IntegrationOperation(
        "continue_diagnostic_interview",
        "Answer the next adaptive interview question and receive the follow-up.",
        "available",
        "synchronous",
        mutates_state=True,
    ),
    IntegrationOperation(
        "get_project_status",
        "Read the current workflow node, progress and next required action.",
        "available",
        "synchronous",
    ),
    IntegrationOperation(
        "open_full_workspace",
        "Continue evidence review or complex editing in the Trident workspace.",
        "available",
        "deep_link",
    ),
    IntegrationOperation(
        "run_research",
        "Start or resume the durable multi-stage research workflow.",
        "planned_job_api",
        "asynchronous_job",
        mutates_state=True,
        requires_human_confirmation=True,
    ),
    IntegrationOperation(
        "submit_review_decision",
        "Accept, reject or annotate a bounded review batch.",
        "planned_auth",
        "synchronous",
        mutates_state=True,
        requires_human_confirmation=True,
    ),
    IntegrationOperation(
        "get_decision_output",
        "Retrieve a report summary, Scorecard, IC Memo or Action Plan.",
        "planned_auth",
        "synchronous",
    ),
    IntegrationOperation(
        "submit_action_feedback",
        "Write execution progress, outcome evidence and blockers back to the project.",
        "planned_auth",
        "synchronous",
        mutates_state=True,
        requires_human_confirmation=True,
    ),
)


def builtin_integration_surfaces() -> tuple[IntegrationSurface, ...]:
    return (
        IntegrationSurface(
            surface_id="trident_web",
            display_name="Trident Web Workspace",
            interaction_mode="full_workspace",
            recommended_scope="完整研究、证据矩阵、复杂Gate、报告编辑、Scorecard与Action Plan",
            supports_full_workspace=True,
            identity_strategy="Trident session now; organization OIDC and RBAC for production",
            response_strategy="responsive pages with polling or event progress",
            operations=COMMON_OPERATIONS,
        ),
        IntegrationSurface(
            surface_id="feishu_companion",
            display_name="Feishu Decision Companion",
            interaction_mode="conversational_companion",
            recommended_scope="场景入口、主动访谈、资料提醒、进度、批量审核、行动反馈与预警",
            supports_full_workspace=False,
            identity_strategy="Feishu tenant/user identity mapped to Trident organization/workspace roles",
            response_strategy="bot messages and interactive cards; complex work uses signed deep links",
            operations=COMMON_OPERATIONS,
        ),
        IntegrationSurface(
            surface_id="m365_copilot_agent",
            display_name="Microsoft 365 Copilot Agent",
            interaction_mode="api_action",
            recommended_scope="用自然语言调用Trident工具、引用企业资料、查询状态、提交反馈并打开完整工作台",
            supports_full_workspace=False,
            identity_strategy="Microsoft Entra identity and OAuth scopes mapped to Trident tenant/RBAC",
            response_strategy="declarative/custom-engine agent actions over OpenAPI; long work returns job handles",
            operations=COMMON_OPERATIONS,
        ),
    )
