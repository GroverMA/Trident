export type ResearchPath = "research_build_first" | "report_review_first";

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
  created_at: string;
  updated_at: string;
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
