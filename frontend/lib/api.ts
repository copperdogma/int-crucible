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
  status: string;
  created_at?: string;
  completed_at?: string;
}

export interface Candidate {
  id: string;
  run_id: string;
  project_id: string;
  origin: string;
  mechanism_description: string;
  predicted_effects?: Record<string, any>;
  scores?: {
    P?: number;
    R?: number;
    I?: number;
  };
  constraint_flags?: string[];
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
    mode: 'setup' | 'analysis' = 'setup'
  ): Promise<ChatSession> => {
    return apiFetch<ChatSession>('/chat-sessions', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, title, mode }),
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
    role: 'user' | 'system' | 'agent' = 'user'
  ): Promise<Message> => {
    return apiFetch<Message>(`/chat-sessions/${chatSessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content, role }),
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
  get: async (runId: string): Promise<Run> => {
    return apiFetch<Run>(`/runs/${runId}`);
  },
  create: async (
    projectId: string,
    mode: string = 'full_search',
    config?: Record<string, any>
  ): Promise<Run> => {
    return apiFetch<Run>('/runs', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, mode, config }),
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

