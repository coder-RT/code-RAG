/**
 * Shared API Types and Schemas
 * Used by both client and server for type consistency
 */

// Common response structure
export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data: T | null;
}

// Codebase types
export interface IndexRequest {
  path: string;
  include_patterns?: string[];
  exclude_patterns?: string[];
}

export interface QueryRequest {
  question: string;
  context_limit?: number;
}

export interface ExplainRequest {
  path: string;
  detail_level?: 'summary' | 'detailed' | 'verbose';
}

export interface CodeSource {
  file: string;
  snippet: string;
}

export interface QueryResponse {
  answer: string;
  sources: CodeSource[];
}

// Architecture types
export interface ModuleInfo {
  name: string;
  path: string;
  type: string;
  files: string[];
  description: string;
}

export interface LayerInfo {
  name: string;
  paths: string[];
  description: string;
}

export interface PatternInfo {
  analysis: string;
}

export interface ArchitectureAnalysis {
  modules: ModuleInfo[];
  layers: LayerInfo[];
  patterns: PatternInfo[];
  summary: string;
}

// Terraform types
export interface TerraformResource {
  type: string;
  name: string;
  file: string;
}

export interface TerraformModule {
  name: string;
  source: string;
  file: string;
}

export interface TerraformVariable {
  name: string;
  type: string;
  default: string | null;
  description: string | null;
  file: string;
}

export interface TerraformAnalysis {
  files: number;
  resources: TerraformResource[];
  modules: TerraformModule[];
  variables: TerraformVariable[];
  outputs: TerraformOutput[];
  providers: TerraformProvider[];
  summary: string;
}

export interface TerraformOutput {
  name: string;
  value: string | null;
  description: string | null;
  file: string;
}

export interface TerraformProvider {
  name: string;
  file: string;
}

// Graph types
export interface GraphNode {
  id: string;
  label: string;
  type: string;
  metadata?: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  metadata?: Record<string, unknown>;
}

export interface GraphStats {
  total_nodes: number;
  total_edges: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  graph_type: 'full' | 'dependency' | 'integration' | 'terraform';
  stats: GraphStats;
  layers?: Record<string, string[]>;
  mermaid?: string;
}

export interface GraphRequest {
  path: string;
  graph_type?: 'full' | 'dependencies' | 'integration' | 'terraform';
  output_format?: 'json' | 'svg' | 'mermaid';
}

