import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface CodebaseResponse {
  success: boolean
  message: string
  data: Record<string, unknown> | null
}

export interface TaskStatusResponse {
  task_id: string
  status: string
  progress?: number
  stage?: string
  message?: string
  result?: Record<string, unknown>
}

export interface IndexOptions {
  path: string
  projectName?: string
  excludePatterns?: string[]
  asyncMode?: boolean
  embeddingProvider?: 'openai' | 'huggingface'
}

export interface Project {
  name: string
  count: number
}

export interface LLMModel {
  id: string
  name: string
  description: string
  provider: string
}

export interface GraphData {
  nodes: Array<{
    id: string
    label: string
    type: string
    metadata?: Record<string, unknown>
  }>
  edges: Array<{
    source: string
    target: string
    relationship: string
    metadata?: Record<string, unknown>
  }>
  graph_type: string
  stats: {
    total_nodes: number
    total_edges: number
  }
  mermaid?: string
}

export const api = {
  // Health check
  health: () => client.get('/health'),

  // Codebase endpoints
  indexCodebase: (options: IndexOptions) =>
    client.post<CodebaseResponse>('/codebase/index', {
      path: options.path,
      project_name: options.projectName,
      exclude_patterns: options.excludePatterns,
      async_mode: options.asyncMode ?? false,
      embedding_provider: options.embeddingProvider ?? 'openai',
    }),
  
  // Get indexed projects
  getProjects: () =>
    client.get<CodebaseResponse>('/codebase/projects'),
  
  // Delete a project
  deleteProject: (projectName: string) =>
    client.delete<CodebaseResponse>(`/codebase/projects/${projectName}`),
  
  // Rename a project
  renameProject: (projectName: string, newName: string) =>
    client.put<CodebaseResponse>(`/codebase/projects/${projectName}/rename`, {
      new_name: newName,
    }),

  // Get available LLM models
  getModels: () =>
    client.get<CodebaseResponse>('/codebase/models'),

  // Task status (for async indexing)
  getTaskStatus: (taskId: string) =>
    client.get<TaskStatusResponse>(`/codebase/task/${taskId}`),

  queryCodebase: (
    question: string, 
    projectName: string, 
    llmModel = 'gpt-4o',
    contextLimit = 5, 
    embeddingProvider = 'openai',
    userContext?: string
  ) =>
    client.post<CodebaseResponse>('/codebase/query', {
      question,
      project_name: projectName,
      llm_model: llmModel,
      context_limit: contextLimit,
      embedding_provider: embeddingProvider,
      user_context: userContext || null,
    }),

  explainCode: (path: string, detailLevel = 'summary') =>
    client.post<CodebaseResponse>('/codebase/explain', {
      path,
      detail_level: detailLevel,
    }),

  getStructure: (path: string) =>
    client.get<CodebaseResponse>(`/codebase/structure/${encodeURIComponent(path)}`),

  // Architecture endpoints
  analyzeArchitecture: (path: string, analysisType = 'full') =>
    client.post<CodebaseResponse>('/architecture/analyze', {
      path,
      analysis_type: analysisType,
    }),

  getModules: (path: string) =>
    client.get<CodebaseResponse>(`/architecture/modules/${encodeURIComponent(path)}`),

  getLayers: (path: string) =>
    client.get<CodebaseResponse>(`/architecture/layers/${encodeURIComponent(path)}`),

  detectPatterns: (path: string) =>
    client.get<CodebaseResponse>(`/architecture/patterns/${encodeURIComponent(path)}`),

  // Terraform endpoints
  analyzeTerraform: (path: string, includeModules = true) =>
    client.post<CodebaseResponse>('/terraform/analyze', {
      path,
      include_modules: includeModules,
    }),

  getTerraformResources: (path: string) =>
    client.get<CodebaseResponse>(`/terraform/resources/${encodeURIComponent(path)}`),

  getAppLinks: (path: string) =>
    client.post<CodebaseResponse>('/terraform/app-links', { path }),

  explainInfrastructure: (path: string) =>
    client.post<CodebaseResponse>('/terraform/explain', { path }),

  // Graph endpoints
  generateGraph: (path: string, graphType = 'full', outputFormat = 'json') =>
    client.post<{ success: boolean; message: string; data: GraphData }>('/graph/generate', {
      path,
      graph_type: graphType,
      output_format: outputFormat,
    }),

  getDependencyGraph: (path: string) =>
    client.post<{ success: boolean; message: string; data: GraphData }>('/graph/dependencies', { path }),

  getIntegrationGraph: (path: string) =>
    client.post<{ success: boolean; message: string; data: GraphData }>('/graph/integration', { path }),

  getGraphSummary: (path: string, graphType = 'full') =>
    client.post<CodebaseResponse>('/graph/summary', {
      path,
      graph_type: graphType,
    }),

  exportMermaid: (path: string, graphType = 'full') =>
    client.post<CodebaseResponse>('/graph/export/mermaid', {
      path,
      graph_type: graphType,
    }),
}

