/**
 * API client for Int Crucible backend.
 * 
 * Provides typed functions for all backend API endpoints.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface Project {
  id: string;
  title: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ChatSession {
  id: string;
  project_id: string;
  title?: string;
  mode: 'setup' | 'analysis';
  created_at?: string;
  updated_at?: string;
}

export interface Message {
  id: string;
  chat_session_id: string;
  role: 'user' | 'system' | 'agent';
  content: string;
  message_metadata?: Record<string, any>;
  created_at?: string;
}

export interface ProblemSpec {
  id: string;
  project_id: string;
  constraints: Array<{ name: string; description: string; weight: number }>;
  goals: string[];
  resolution: string;
  mode: 'full_search' | 'eval_only' | 'seeded';
  created_at?: string;
  updated_at?: string;
  provenance_log?: Array<Record<string, any>>;
}

export interface WorldModel {
  id: string;
  project_id: string;
  model_data: {
    actors?: any[];
    mechanisms?: any[];
    resources?: any[];
    constraints?: any[];
    assumptions?: any[];
    simplifications?: any[];
  };
  created_at?: string;
  updated_at?: string;
}

export interface Run {
  id: string;
  project_id: string;
  mode: string;
  config?: Record<string, any>;
  recommended_message_id?: string | null;
  recommended_config_snapshot?: Record<string, any> | null;
  ui_trigger_id?: string | null;
  ui_trigger_source?: string | null;
  ui_trigger_metadata?: Record<string, any> | null;
  ui_triggered_at?: string | null;
  run_summary_message_id?: string | null;
  status: string;
  created_at?: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  candidate_count?: number;
  scenario_count?: number;
  evaluation_count?: number;
  metrics?: Record<string, any> | null;
  llm_usage?: Record<string, any> | null;
  error_summary?: string | null;
}

export interface RunPreflightResponse {
  ready: boolean;
  blockers: string[];
  warnings: string[];
  normalized_config: Record<string, any>;
  prerequisites: Record<string, boolean>;
  notes: string[];
}

export interface RunSummaryPage {
  runs: Run[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
  next_offset?: number | null;
}

export interface Candidate {
  id: string;
  run_id: string;
  project_id: string;
  origin: string;
  status?: string;
  mechanism_description: string;
  predicted_effects?: Record<string, any>;
  scores?: {
    P?: number;
    R?: number;
    I?: number;
  };
  constraint_flags?: string[];
  parent_ids?: string[];
  provenance_summary?: {
    event_count: number;
    last_event?: {
      type?: string;
      timestamp?: string;
      actor?: string;
      source?: string;
      description?: string;
    };
  };
}

export interface CandidateDetail extends Candidate {
  parent_summaries: Array<{
    id: string;
    mechanism_description?: string;
    status?: string;
  }>;
  provenance_log: Array<Record<string, any>>;
  evaluations: Array<{
    id: string;
    scenario_id: string;
    P?: Record<string, any>;
    R?: Record<string, any>;
    constraint_satisfaction?: Record<string, any>;
    explanation?: string;
  }>;
}

export interface ProjectProvenance {
  project_id: string;
  problem_spec: Array<Record<string, any>>;
  world_model: Array<Record<string, any>>;
  candidates: Array<{
    candidate_id: string;
    run_id: string;
    parent_ids: string[];
    provenance_log: Array<Record<string, any>>;
  }>;
}

export interface GuidanceResponse {
  guidance_message: string;
  suggested_actions: string[];
  workflow_progress: {
    current_stage: string;
    completed_steps: string[];
    next_steps: string[];
  };
}

export interface WorkflowState {
  has_problem_spec: boolean;
  has_world_model: boolean;
  has_runs: boolean;
  run_count: number;
  project_title?: string;
  project_description?: string;
}

export interface Issue {
  id: string;
  project_id: string;
  run_id?: string | null;
  candidate_id?: string | null;
  type: 'model' | 'constraint' | 'evaluator' | 'scenario';
  severity: 'minor' | 'important' | 'catastrophic';
  description: string;
  resolution_status: 'open' | 'resolved' | 'invalidated';
  created_at?: string;
  resolved_at?: string | null;
}

export interface RemediationProposal {
  action_type: 'patch_and_rescore' | 'partial_rerun' | 'full_rerun' | 'invalidate_candidates';
  description: string;
  estimated_impact: string;
  rationale: string;
}

export interface FeedbackResponse {
  issue_id: string;
  feedback_message: string;
  clarifying_questions: string[];
  remediation_proposal?: RemediationProposal;
  needs_clarification: boolean;
  tool_call_audits?: Array<{
    tool_name: string;
    arguments: Record<string, any>;
    result_summary: string;
    duration_ms: number;
    success: boolean;
    error?: string;
  }>;
}

/**
 * Generic API fetch wrapper with error handling.
 */
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    // Handle 404 as a special case - return null for optional resources
    // Suppress console errors for expected 404s (e.g., world-model not existing yet)
    if (response.status === 404) {
      // Only log if it's not an expected 404 (world-model endpoint)
      if (!endpoint.includes('/world-model')) {
        console.warn(`Resource not found: ${endpoint}`);
      }
      throw new Error('NOT_FOUND');
    }
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `API error: ${response.statusText}`);
  }

  return response.json();
}

// Project endpoints
export const projectsApi = {
  list: async (): Promise<Project[]> => {
    return apiFetch<Project[]>('/projects');
  },
  get: async (projectId: string): Promise<Project> => {
    return apiFetch<Project>(`/projects/${projectId}`);
  },
  create: async (title: string, description?: string): Promise<Project> => {
    return apiFetch<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify({ title, description }),
    });
  },
  createFromDescription: async (description: string, suggestedTitle?: string): Promise<Project> => {
    return apiFetch<Project>('/projects/from-description', {
      method: 'POST',
      body: JSON.stringify({ description, suggested_title: suggestedTitle }),
    });
  },
  update: async (projectId: string, title?: string, description?: string): Promise<Project> => {
    return apiFetch<Project>(`/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify({ title, description }),
    });
  },
  getProvenance: async (projectId: string): Promise<ProjectProvenance> => {
    return apiFetch<ProjectProvenance>(`/projects/${projectId}/provenance`);
  },
};

// Chat session endpoints
export const chatSessionsApi = {
  list: async (projectId?: string): Promise<ChatSession[]> => {
    const endpoint = projectId ? `/projects/${projectId}/chat-sessions` : '/chat-sessions';
    return apiFetch<ChatSession[]>(endpoint);
  },
  get: async (chatSessionId: string): Promise<ChatSession> => {
    return apiFetch<ChatSession>(`/chat-sessions/${chatSessionId}`);
  },
  create: async (
    projectId: string,
    title?: string,
    mode: 'setup' | 'analysis' = 'setup',
    runId?: string,
    candidateId?: string
  ): Promise<ChatSession> => {
    return apiFetch<ChatSession>('/chat-sessions', {
      method: 'POST',
      body: JSON.stringify({ 
        project_id: projectId, 
        title, 
        mode,
        run_id: runId,
        candidate_id: candidateId,
      }),
    });
  },
  update: async (
    chatSessionId: string,
    title?: string,
    mode?: 'setup' | 'analysis'
  ): Promise<ChatSession> => {
    return apiFetch<ChatSession>(`/chat-sessions/${chatSessionId}`, {
      method: 'PUT',
      body: JSON.stringify({ title, mode }),
    });
  },
};

// Message endpoints
export const messagesApi = {
  list: async (chatSessionId: string): Promise<Message[]> => {
    return apiFetch<Message[]>(`/chat-sessions/${chatSessionId}/messages`);
  },
  create: async (
    chatSessionId: string,
    content: string,
    role: 'user' | 'system' | 'agent' = 'user',
    messageMetadata?: Record<string, any>
  ): Promise<Message> => {
    return apiFetch<Message>(`/chat-sessions/${chatSessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content, role, message_metadata: messageMetadata }),
    });
  },
};

// ProblemSpec endpoints
export const problemSpecApi = {
  get: async (projectId: string): Promise<ProblemSpec> => {
    return apiFetch<ProblemSpec>(`/projects/${projectId}/problem-spec`);
  },
  refine: async (
    projectId: string,
    chatSessionId?: string,
    messageLimit: number = 20
  ): Promise<any> => {
    return apiFetch(`/projects/${projectId}/problem-spec/refine`, {
      method: 'POST',
      body: JSON.stringify({ chat_session_id: chatSessionId, message_limit: messageLimit }),
    });
  },
};

// WorldModel endpoints
export const worldModelApi = {
  get: async (projectId: string): Promise<WorldModel> => {
    return apiFetch<WorldModel>(`/projects/${projectId}/world-model`);
  },
  refine: async (
    projectId: string,
    chatSessionId?: string,
    messageLimit: number = 20
  ): Promise<any> => {
    return apiFetch(`/projects/${projectId}/world-model/refine`, {
      method: 'POST',
      body: JSON.stringify({ chat_session_id: chatSessionId, message_limit: messageLimit }),
    });
  },
  update: async (projectId: string, modelData: any, source: string = 'manual_edit'): Promise<WorldModel> => {
    return apiFetch<WorldModel>(`/projects/${projectId}/world-model`, {
      method: 'PUT',
      body: JSON.stringify({ model_data: modelData, source }),
    });
  },
};

// Run endpoints
export const runsApi = {
  list: async (projectId?: string): Promise<Run[]> => {
    const endpoint = projectId ? `/projects/${projectId}/runs` : '/runs';
    return apiFetch<Run[]>(endpoint);
  },
  listSummary: async (
    projectId: string,
    options?: {
      limit?: number;
      offset?: number;
      status?: string[];
    }
  ): Promise<RunSummaryPage> => {
    const searchParams = new URLSearchParams();
    if (options?.limit !== undefined) {
      searchParams.set('limit', String(options.limit));
    }
    if (options?.offset !== undefined) {
      searchParams.set('offset', String(options.offset));
    }
    if (options?.status) {
      for (const status of options.status) {
        searchParams.append('status', status);
      }
    }
    const query = searchParams.toString();
    const endpoint = `/projects/${projectId}/runs/summary${query ? `?${query}` : ''}`;
    return apiFetch<RunSummaryPage>(endpoint);
  },
  get: async (runId: string): Promise<Run> => {
    return apiFetch<Run>(`/runs/${runId}`);
  },
  create: async (
    projectId: string,
    mode: string = 'full_search',
    config?: Record<string, any>,
    extras?: {
      chat_session_id?: string | null;
      recommended_message_id?: string | null;
      recommended_config_snapshot?: Record<string, any> | null;
      ui_trigger_id: string;
      ui_trigger_source?: string;
      ui_trigger_metadata?: Record<string, any> | null;
    }
  ): Promise<Run> => {
    const payload: Record<string, any> = {
      project_id: projectId,
      mode,
      config,
      ui_trigger_id: extras?.ui_trigger_id,
      ui_trigger_source: extras?.ui_trigger_source ?? 'run_config_panel',
      ui_trigger_metadata: extras?.ui_trigger_metadata,
      chat_session_id: extras?.chat_session_id,
      recommended_message_id: extras?.recommended_message_id,
      recommended_config_snapshot: extras?.recommended_config_snapshot,
    };

    return apiFetch<Run>('/runs', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  preflight: async (
    projectId: string,
    mode: string,
    parameters: Record<string, any> | undefined,
    chatSessionId?: string | null,
    recommendedMessageId?: string | null
  ): Promise<RunPreflightResponse> => {
    return apiFetch<RunPreflightResponse>(`/projects/${projectId}/runs/preflight`, {
      method: 'POST',
      body: JSON.stringify({
        mode,
        parameters,
        chat_session_id: chatSessionId,
        recommended_message_id: recommendedMessageId,
      }),
    });
  },
  executeFullPipeline: async (
    runId: string,
    numCandidates: number = 5,
    numScenarios: number = 8
  ): Promise<any> => {
    return apiFetch(`/runs/${runId}/full-pipeline`, {
      method: 'POST',
      body: JSON.stringify({ num_candidates: numCandidates, num_scenarios: numScenarios }),
    });
  },
  getRankedCandidates: async (runId: string): Promise<Candidate[]> => {
    // After ranking, candidates should be available via the run
    return apiFetch<Candidate[]>(`/runs/${runId}/candidates`);
  },
  getCandidateDetail: async (runId: string, candidateId: string): Promise<CandidateDetail> => {
    return apiFetch<CandidateDetail>(`/runs/${runId}/candidates/${candidateId}`);
  },
};

// Guidance endpoints
export const guidanceApi = {
  requestGuidance: async (
    chatSessionId: string,
    userQuery?: string,
    messageLimit: number = 5
  ): Promise<GuidanceResponse> => {
    return apiFetch<GuidanceResponse>(`/chat-sessions/${chatSessionId}/guidance`, {
      method: 'POST',
      body: JSON.stringify({ user_query: userQuery, message_limit: messageLimit }),
    });
  },
  getWorkflowState: async (projectId: string): Promise<WorkflowState> => {
    return apiFetch<WorkflowState>(`/projects/${projectId}/workflow-state`);
  },
  generateArchitectReply: async (chatSessionId: string): Promise<Message> => {
    return apiFetch<Message>(`/chat-sessions/${chatSessionId}/architect-reply`, {
      method: 'POST',
    });
  },
  generateArchitectReplyStream: async (
    chatSessionId: string,
    onChunk: (chunk: string) => void,
    onDone: (messageId: string) => void,
    onError: (error: string) => void,
    onUpdating?: (what: string) => void,
    onUpdated?: (delta: any, what: string) => void
  ): Promise<void> => {
    const url = `${API_BASE_URL}/chat-sessions/${chatSessionId}/architect-reply-stream`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      onError(error.detail || `API error: ${response.statusText}`);
      return;
    }

    if (!response.body) {
      onError('No response body');
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'chunk') {
                onChunk(data.content);
              } else if (data.type === 'done') {
                onDone(data.message_id);
                return;
              } else if (data.type === 'error') {
                onError(data.error);
                return;
              } else if (data.type === 'updating' && onUpdating) {
                onUpdating(data.what);
              } else if (data.type === 'updated' && onUpdated) {
                onUpdated(data.delta, data.what);
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e, line);
            }
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Streaming error');
    } finally {
      reader.releaseLock();
    }
  },
};

// Issue endpoints
export const issuesApi = {
  create: async (
    projectId: string,
    type: 'model' | 'constraint' | 'evaluator' | 'scenario',
    severity: 'minor' | 'important' | 'catastrophic',
    description: string,
    runId?: string | null,
    candidateId?: string | null
  ): Promise<Issue> => {
    return apiFetch<Issue>(`/projects/${projectId}/issues`, {
      method: 'POST',
      body: JSON.stringify({
        type,
        severity,
        description,
        run_id: runId,
        candidate_id: candidateId,
      }),
    });
  },
  list: async (
    projectId: string,
    filters?: {
      run_id?: string;
      candidate_id?: string;
      type?: 'model' | 'constraint' | 'evaluator' | 'scenario';
      severity?: 'minor' | 'important' | 'catastrophic';
      resolution_status?: 'open' | 'resolved' | 'invalidated';
    }
  ): Promise<Issue[]> => {
    const searchParams = new URLSearchParams();
    if (filters?.run_id) searchParams.set('run_id', filters.run_id);
    if (filters?.candidate_id) searchParams.set('candidate_id', filters.candidate_id);
    if (filters?.type) searchParams.set('type', filters.type);
    if (filters?.severity) searchParams.set('severity', filters.severity);
    if (filters?.resolution_status) searchParams.set('resolution_status', filters.resolution_status);
    const query = searchParams.toString();
    const endpoint = `/projects/${projectId}/issues${query ? `?${query}` : ''}`;
    return apiFetch<Issue[]>(endpoint);
  },
  get: async (issueId: string): Promise<Issue> => {
    return apiFetch<Issue>(`/issues/${issueId}`);
  },
  update: async (
    issueId: string,
    description?: string,
    resolution_status?: 'open' | 'resolved' | 'invalidated'
  ): Promise<Issue> => {
    return apiFetch<Issue>(`/issues/${issueId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        description,
        resolution_status,
      }),
    });
  },
  resolve: async (
    issueId: string,
    remediationAction: 'patch_and_rescore' | 'partial_rerun' | 'full_rerun' | 'invalidate_candidates',
    remediationMetadata?: {
      problem_spec?: Record<string, any>;
      world_model?: Record<string, any>;
      run_config?: Record<string, any>;
      candidate_ids?: string[];
      reason?: string;
    }
  ): Promise<{
    status: string;
    message: string;
    issue_id: string;
    remediation_action: string;
    result: Record<string, any>;
  }> => {
    return apiFetch(`/issues/${issueId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({
        remediation_action: remediationAction,
        remediation_metadata: remediationMetadata,
      }),
    });
  },
};

// Feedback endpoints
export const feedbackApi = {
  proposeRemediation: async (
    issueId: string,
    userClarification?: string
  ): Promise<FeedbackResponse> => {
    const searchParams = new URLSearchParams();
    if (userClarification) {
      searchParams.set('user_clarification', userClarification);
    }
    const query = searchParams.toString();
    const endpoint = `/issues/${issueId}/feedback${query ? `?${query}` : ''}`;
    return apiFetch<FeedbackResponse>(endpoint, {
      method: 'POST',
    });
  },
};

