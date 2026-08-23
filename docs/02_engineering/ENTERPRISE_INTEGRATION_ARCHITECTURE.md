# Enterprise Integration Architecture

## Decision

Trident Web remains the system of record and the complete decision workspace. Feishu, Microsoft 365 Copilot and future enterprise channels are companion surfaces around the same Research Core; they do not own scenario logic, prompts, evidence rules, project state or report generation.

This preserves one product baseline while allowing a customer to work from the tools it already uses.

## Product boundary

| Surface | Best use | Handoff to Trident Web |
|---|---|---|
| Trident Web | Full research, evidence matrix, complex Gates, report editing, Scorecard and Action Plan | Not required |
| Feishu companion | Create/continue work, adaptive interview, upload reminders, status cards, notifications, bounded review, action feedback | Evidence review, complex editing and full report |
| Microsoft 365 Copilot agent | Natural-language actions over Trident APIs, enterprise-document context, status and feedback | Evidence review, complex editing and full report |
| Focused industry-research plugin | Define a question, start an asynchronous study, receive progress and an executive summary | Gate review and complete report |

The complete product can be exposed through a plugin, but it should not be reproduced as a long chat conversation. Long-running work returns a job handle; the channel sends progress and review notifications; a signed deep link opens the exact project and node in the Web workspace.

## Shared architecture

```text
Feishu bot/cards       Microsoft agent       Other enterprise channel
        \                    |                       /
             Channel adapters and card schemas
                            |
              Integration gateway / OpenAPI
                            |
       Identity mapping, tenant isolation and RBAC
                            |
       Project API + interview API + durable job API
                            |
       Scenario Packs -> shared Industry Research Core
                            |
 Projects / evidence / artifacts / enterprise memory
                            |
       audit log / token, latency and outcome telemetry
```

PE, VC and Enterprise Growth therefore do not receive copies of the industry-research code. Each Scenario Pack configures the interview, research tasks, evidence emphasis, Gates, Scorecard and output contract while calling the same versioned Research Core.

## Stable operation contract

All delivery surfaces use the same operation identifiers:

- `create_project`
- `continue_diagnostic_interview`
- `get_project_status`
- `run_research`
- `submit_review_decision`
- `get_decision_output`
- `submit_action_feedback`
- `open_full_workspace`

The first four lightweight operations can be exposed early. Research remains asynchronous. Any state-changing review or feedback operation requires an authenticated user and explicit confirmation.

## Required production changes

1. **Identity and tenancy**: map Feishu tenant/user identities and Microsoft Entra identities to a Trident organization, workspace and role.
2. **Durable execution**: use asynchronous jobs, checkpoints, idempotency keys, retry rules and event/webhook delivery for research that outlives a browser request.
3. **Secure handoff**: issue short-lived, signed deep links to an exact project and workflow node; never place secrets or unrestricted project IDs in cards.
4. **Channel presentation**: maintain compact, versioned message/card schemas. Cards summarize; they do not duplicate evidence tables or the report editor.
5. **Enterprise files**: add permission-aware file ingestion and source provenance for Feishu and Microsoft 365 documents.
6. **Governance**: add RBAC, consent, audit logs, retention policy, data-region policy and tool-level allowlists.
7. **Observability**: trace channel, operation, project, job, model/token use, latency, failure and human decision without logging confidential content by default.

## Delivery sequence

- **Current architecture phase**: publish the integration-surface contract and keep all plugin-only operations explicitly marked as planned.
- **Focused pilot**: industry-research companion with intake, adaptive interview, start/status, notifications and deep links.
- **Scenario expansion**: expose PE, VC and Enterprise Growth through the same contract after their Scenario Packs and tenant data boundaries are accepted.
- **Enterprise rollout**: add SSO/RBAC, durable jobs, document connectors, audit and customer-specific policies before production distribution.

No Feishu or Copilot package is deployed in the current phase.
