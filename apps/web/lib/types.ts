export type Scope = { country: string; period: string };
export type Row = {
  [key: string]: string | number | null | undefined;
  revenue: number;
  target: number;
  gap: number;
  attainment: number;
  prior_year_revenue: number;
  product?: string;
  country?: string;
  territory?: string;
  month?: string;
  share?: number;
};
export type Dataset = {
  data_version: string;
  rows: number;
  months: number;
  as_of: string;
  currency: string;
  quality_checks: Record<string, boolean>;
};
export type Overview = {
  summary: Row & { growth: number };
  products: Row[];
  markets: Row[];
  territories: Row[];
  trend: Row[];
  scope: Scope;
  metadata: Dataset;
};
export type Answer = {
  run_id: string;
  status: string;
  title: string;
  text: string;
  next_check?: string;
  limitation?: string;
  chart: string;
  rows: Row[];
  scope: Scope;
  sql?: string;
  steps: string[];
  latency_ms: number;
  mode: string;
  usage: { input_tokens: number; output_tokens: number };
  data_version: string;
  intent: string;
};
export type Brief = {
  brief_id: string;
  title: string;
  created_at?: string;
  content: {
    summary: string;
    findings: string[];
    next_step: string;
    disclosure: string;
    data_version: string;
    scope: Scope;
  };
};
export type Analysis = {
  selected_model: string;
  history: { month: string; revenue: number }[];
  forecast: { month: string; forecast: number; lower: number; upper: number }[];
  test: Record<string, { mape: number; wape: number; mae: number }>;
  test_period: string;
  method: string;
  interval_note: string;
  anomaly: { flagged: boolean; robust_score: number | null; method: string };
  promotion: {
    effect_pp: number;
    p_value: number;
    ci_low_pp: number;
    ci_high_pp: number;
    method: string;
    limitation: string;
  };
};
