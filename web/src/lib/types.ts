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
  interpreted_intent?: {
    interpreted_objective: string;
    requested_topics: string[];
    must_answer_questions: string[];
    terminology_map: Record<string, string>;
    explicit_exclusions: string[];
    ambiguities: string[];
  };
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
  prompt_question_ids: string[];
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

export type EvidenceReviewStatus = "needs_review" | "accepted" | "rejected";

export interface EvidenceItem {
  evidence_id: string;
  task_id: string;
  source_id: string;
  kind: string;
  statement: string;
  supporting_excerpt: string;
  source_date?: string | null;
  geographic_scope: string;
  market_scope: string;
  prompt_relevance: number;
  question_ids: string[];
  prompt_question_ids: string[];
  qa_score: number;
  qa_flags: string[];
  review_status: EvidenceReviewStatus;
  reviewer_note?: string | null;
}

export interface EvidenceSource {
  source_id: string;
  title: string;
  url: string;
  domain: string;
  source_tier: string;
  tier_reason: string;
}

export interface TaskEvidenceRun {
  run_id: string;
  task_id: string;
  task_title: string;
  queries_used: string[];
  sources: EvidenceSource[];
  evidence: EvidenceItem[];
  information_gaps: string[];
  search_errors: string[];
}

export interface EvidenceCollectionArtifact {
  artifact_id: string;
  research_plan_id: string;
  task_runs: TaskEvidenceRun[];
  human_confirmed: boolean;
  coverage_gap_resolution?: string | null;
  coverage_gap_user_input?: string | null;
  coverage_gaps_acknowledged_at?: string | null;
  updated_at: string;
}

export type AnalysisReviewStatus = "needs_review" | "accepted" | "rejected";

export interface AnalysisFinding {
  finding_id: string;
  subject: string;
  finding_type: string;
  statement: string;
  mechanism: string;
  evidence_ids: string[];
  counter_evidence_ids: string[];
  comparison_dimensions: Record<string, string>;
  factor_role?: string | null;
  impact_direction?: string | null;
  confidence: number;
  scope: string;
  uncertainty: string;
  boundary_condition: string;
  review_status: AnalysisReviewStatus;
  reviewer_note?: string | null;
}

export interface IndustryAnalysisModule {
  module_id: string;
  title: string;
  executive_summary: string;
  findings: AnalysisFinding[];
  evidence_gaps: string[];
  rejected_questions: string[];
  market_sizing?: MarketSizingEstimate | null;
}

export interface MarketSizingEstimate {
  scope: string;
  currency: string;
  unit: string;
  price_basis: string;
  base_year: number;
  base_size: number;
  low_size: number;
  high_size: number;
  forecast_year: number;
  forecast_size: number;
  forecast_cagr: number;
  primary_method: string;
  validation_method: string;
  primary_equation: string;
  validation_equation: string;
  inputs: Array<{ name: string; value: number; unit: string; year: number; input_type: string; rationale: string }>;
  reconciliation: string;
  sensitivities: string[];
  limitations: string[];
}

export interface IndustryAnalysisArtifact {
  artifact_id: string;
  evidence_collection_id: string;
  input_evidence_ids: string[];
  modules: IndustryAnalysisModule[];
  company_implications: AnalysisFinding[];
  cross_module_conflicts: string[];
  overall_evidence_limitations: string[];
  human_confirmed: boolean;
  updated_at: string;
}

export type ForecastReviewStatus = "needs_review" | "accepted" | "rejected";

export interface FutureTrend {
  trend_id: string;
  title: string;
  category: string;
  forecast_horizon: string;
  forecast_statement: string;
  causal_mechanism: string[];
  assumptions: string[];
  leading_indicators: Array<{ name: string; definition: string; trigger_condition: string }>;
  falsification_conditions: string[];
  evidence_ids: string[];
  confidence: { overall: number };
  confidence_note: string;
  market_size_net_impact_score: number;
  profitability_net_impact_score: number;
  review_status: ForecastReviewStatus;
  reviewer_note?: string | null;
}

export interface FutureScenario {
  scenario_id: string;
  scenario_type: string;
  title: string;
  narrative: string;
  trigger_conditions: string[];
  expected_outcomes: string[];
  leading_indicators: string[];
  falsification_conditions: string[];
  review_status: ForecastReviewStatus;
  reviewer_note?: string | null;
}

export interface FutureIntelligenceArtifact {
  artifact_id: string;
  industry_analysis_id: string;
  evidence_collection_id: string;
  trends: FutureTrend[];
  scenarios: FutureScenario[];
  monitoring_priorities: string[];
  forecast_gaps: string[];
  forecast_methodology: {
    data_sufficiency: string;
    selected_method: string;
    validation_design: string;
    quantitative_forecast_used: boolean;
    selection_rationale: string;
    model_limitations: string[];
  };
  human_confirmed: boolean;
  updated_at: string;
}

export interface GeneralReportArtifact {
  report_id: string;
  title: string;
  report_status: string;
  markdown: string;
  accepted_evidence_ids: string[];
  accepted_finding_ids: string[];
  accepted_trend_ids: string[];
  accepted_scenario_ids: string[];
  unresolved_prompt_questions: string[];
  source_count: number;
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
  scenario_pack?: string;
  scenario_pack_version?: string;
  workspace_mode?: string;
  current_step: string;
  last_pipeline_error?: string | null;
  workflow_status: Record<string, string>;
  market_scope_confirmed_at?: string | null;
  research_brief_artifact?: ResearchBriefArtifact | null;
  research_plan_artifact?: ResearchPlanArtifact | null;
  evidence_collection_artifact?: EvidenceCollectionArtifact | null;
  industry_analysis_artifact?: IndustryAnalysisArtifact | null;
  future_intelligence_artifact?: FutureIntelligenceArtifact | null;
  general_report_artifact?: GeneralReportArtifact | null;
  interview_session_artifact?: {
    artifact_id: string;
    status: "in_progress" | "ready_for_profile" | "completed";
    turns: Array<{ turn_id: string; topic_id: string; question: string; answer?: string | null; answer_quality: string; analysis?: { summary: string; extracted_facts: string[]; ambiguities: string[]; missing_information: string[]; answer_quality: string; topic_complete: boolean; follow_up_question?: string | null; confidence: number } | null }>;
    covered_topics: string[];
    remaining_topics: string[];
    suggested_uploads: string[];
    provider_warning?: string | null;
  } | null;
  entity_profile_artifact?: {
    artifact_id: string;
    entity_name: string;
    operating_portrait: string;
    decision_style: string;
    research_next_step: string;
    known_facts: string[];
    management_judgments: string[];
    data_gaps: string[];
    human_confirmed: boolean;
    confirmed_at?: string | null;
  } | null;
  research_route_artifact?: {
    artifact_id: string;
    scenario_id: string;
    primary_path: ResearchPath;
    supplemental_gap_research: boolean;
    mode_label: string;
    rationale: string[];
    available_materials: string[];
    data_scope: Record<string, unknown>;
  } | null;
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
  scenario_pack: string;
  scenario_pack_version: string;
}

export interface ScenarioWorkflowNodeContract {
  node_id: string;
  capability: string;
  depends_on: string[];
  review_gate?: string | null;
  checkpoint: boolean;
}

export interface ScenarioPackContract {
  descriptor: {
    display_name: string;
    description: string;
    capabilities: string[];
  };
  manifest: {
    scenario_id: string;
    version: string;
    research_core_version: string;
    deprecated: boolean;
    replaces: string[];
  };
  required_inputs: { required: string[] };
  workflow: ScenarioWorkflowNodeContract[];
  interview_policy: Record<string, unknown>;
  evidence_policy: Record<string, unknown>;
  review_gates: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  evaluation_rubric: Record<string, unknown>;
  report_template: Record<string, unknown>;
  ui_schema: Record<string, unknown>;
  feedback_policy: Record<string, unknown>;
  research_route_policy: Record<string, unknown>;
  data_scope_policy: Record<string, unknown>;
}
