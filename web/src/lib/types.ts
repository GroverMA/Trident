export type ResearchPath = "research_build_first" | "report_review_first";

export interface MarketDefinition {
  core_market: string;
  product_scope: string;
  customer_scope: string;
  geography_scope: string;
  value_chain_scope: string;
  time_scope: string;
  inclusions: string[];
  exclusions: string[];
  market_sizing_basis: string;
  competitor_definition: string;
  adjacent_markets: string[];
  ambiguities: string[];
}

export interface ResearchBriefArtifact {
  artifact_id: string;
  decision_statement: string;
  original_prompt: string;
  market_definition: MarketDefinition;
  key_questions: string[];
  information_gaps: string[];
  hypotheses: string[];
  clarification_questions: string[];
  clarification_responses: Record<string, string>;
  confidence_note: string;
  human_confirmed: boolean;
  generated_at: string;
}

export interface ResearchTask {
  task_id: string;
  title: string;
  objective: string;
  questions: string[];
  hypotheses: string[];
  information_needs: string[];
  preferred_sources: string[];
  search_queries: string[];
  deliverables: string[];
  evidence_standard: string;
  counter_evidence_required: boolean;
  validation_gate: string;
  depends_on: string[];
}

export interface ResearchPlanArtifact {
  artifact_id: string;
  plan_summary: string;
  tasks: ResearchTask[];
  human_review_gates: string[];
  unresolved_gaps: string[];
  human_confirmed: boolean;
  generated_at: string;
}

export interface ProjectSummary {
  project_id: string;
  project_name: string;
  industry: string;
  region: string;
  research_objective: string;
  time_horizon: string;
  output_language: string;
  target_company?: string | null;
  company_strategy_enabled: boolean;
  company_strategy_objective?: string | null;
  research_path: ResearchPath;
  research_mode?: string;
  workspace_mode?: string;
  current_step: string;
  workflow_status: Record<string, string>;
  market_scope_confirmed_at?: string | null;
  research_brief_artifact?: ResearchBriefArtifact | null;
  research_plan_artifact?: ResearchPlanArtifact | null;
  created_at: string;
  updated_at: string;
}

export interface ResearchBriefReviewPayload {
  decision_statement: string;
  market_definition: MarketDefinition;
  key_questions: string[];
  information_gaps: string[];
  hypotheses: string[];
  clarification_questions: string[];
  clarification_responses: Record<string, string>;
  confidence_note: string;
  confirm: boolean;
}

export interface ProjectScopePayload {
  project_name: string;
  industry: string;
  region: string;
  research_objective: string;
  time_horizon: string;
  output_language: string;
  target_company?: string | null;
  company_strategy_objective?: string | null;
  confirm: boolean;
}

export interface ProjectCreatePayload {
  project_name: string;
  industry: string;
  region: string;
  research_objective: string;
  time_horizon: string;
  output_language: string;
  target_company?: string;
  company_strategy_enabled: boolean;
  company_strategy_objective?: string;
  research_path: ResearchPath;
  research_mode: "general_research";
  workspace_mode: "quick_report" | "analyst_workspace";
}
