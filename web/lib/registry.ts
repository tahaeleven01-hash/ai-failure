import registryData from "@/data/registry.json";

export interface AgentMetadata {
  name: string;
  version?: string | null;
  model?: string | null;
  provider?: string | null;
}

export interface TaskDefinition {
  prompt: string;
  context?: string | null;
  target_repository?: string | null;
  target_files?: string[];
}

export interface BehaviorComparison {
  expected: string;
  observed: string;
}

export interface EnvironmentSpecification {
  os?: string | null;
  runtime?: string | null;
  dependencies?: Record<string, string>;
  docker_image?: string | null;
}

export interface AssertionRule {
  type: string;
  target?: string | null;
  value: string | number;
  description?: string | null;
}

export interface ReproductionProcedure {
  type: string;
  entrypoint?: string | null;
  command?: string | null;
  timeout_seconds: number;
  assertions?: AssertionRule[];
  requires_network?: boolean;
  requires_docker?: boolean;
}

export interface VerificationMethod {
  method_type: string;
  test_runner?: string | null;
  expected_exit_code?: number | null;
  failure_criteria: string;
}

export interface EvidenceReference {
  type: "log" | "diff" | "screenshot" | "recording" | "link";
  path_or_url: string;
  description?: string | null;
  content?: string;
}

export interface SubmissionMetadata {
  submitted_by: string;
  date: string;
  updated_date?: string | null;
  original_pr_or_issue?: string | null;
}

export interface FailureCase {
  id: string;
  title: string;
  description: string;
  categories: string[];
  status: "submitted" | "validated" | "reproducible" | "non-reproducible" | "archived";
  is_synthetic: boolean;
  agent: AgentMetadata;
  task: TaskDefinition;
  behavior: BehaviorComparison;
  environment: EnvironmentSpecification;
  reproduction: ReproductionProcedure;
  verification: VerificationMethod;
  evidence: EvidenceReference[];
  submission: SubmissionMetadata;
  tags: string[];
  reproduction_code?: string;
}

export interface RegistryStats {
  total_cases: number;
  real_cases: number;
  synthetic_cases: number;
  reproducible_cases: number;
  status_counts: Record<string, number>;
  category_counts: Record<string, number>;
  agent_counts: Record<string, number>;
}

export interface RegistryData {
  version: string;
  statistics: RegistryStats;
  cases: FailureCase[];
}

export function getRegistryData(): RegistryData {
  return registryData as RegistryData;
}

export function getAllCases(): FailureCase[] {
  return (registryData as RegistryData).cases;
}

export function getCaseById(id: string): FailureCase | undefined {
  const cleanId = id.trim().toUpperCase();
  return getAllCases().find((c) => c.id.toUpperCase() === cleanId);
}

export function getRegistryStats(): RegistryStats {
  return (registryData as RegistryData).statistics;
}

export function getAllCategories(): string[] {
  const set = new Set<string>();
  getAllCases().forEach((c) => {
    c.categories.forEach((cat) => set.add(cat));
  });
  return Array.from(set).sort();
}

export function getAllAgents(): string[] {
  const set = new Set<string>();
  getAllCases().forEach((c) => {
    set.add(c.agent.name);
  });
  return Array.from(set).sort();
}
