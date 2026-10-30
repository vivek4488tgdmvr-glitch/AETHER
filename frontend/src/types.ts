export type Health = {
  status: string;
  api_key_configured: boolean;
  model_configured: boolean;
  model_id: string | null;
  docker_cli_available: boolean;
  tavily_configured?: boolean;
  warning?: string;
};

export type RepoFile = {
  path: string;
  size: number;
  lines: number;
  language: string;
};

export type Finding = {
  id: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  confidence: "high" | "medium" | "low";
  file: string;
  line: number | null;
  evidence: string;
  problem: string;
  recommendation: string;
};

export type Analysis = {
  run_id: string;
  summary: string;
  findings: Finding[];
  checks: string[];
  included_files: string[];
  model: string;
  research_sources?: ResearchSource[];
};

export type PatchResult = {
  run_id: string;
  patch: string;
  message: string;
  included_files: string[];
  model: string;
  research_sources?: ResearchSource[];
};

export type TestResult = {
  status: string;
  message: string;
  stdout: string;
  stderr: string;
  exit_code: number | null;
};

export type ResearchSource = {
  title: string;
  url: string;
  content: string;
  score?: number | null;
};
