'use client';

import { useState, useEffect, useRef } from 'react';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { projectsApi, Project, chatSessionsApi, messagesApi } from '@/lib/api';
import ChatInterface, { ChatInterfaceRef } from '@/components/ChatInterface';
import ChatSessionSwitcher from '@/components/ChatSessionSwitcher';
import SpecPanel from '@/components/SpecPanel';
import RunConfigPanel from '@/components/RunConfigPanel';
import ResultsView from '@/components/ResultsView';
import WorkflowProgress from '@/components/WorkflowProgress';
import ProjectEditModal from '@/components/ProjectEditModal';
import RunHistoryPanel from '@/components/RunHistoryPanel';
import IssuesPanel from '@/components/IssuesPanel';
import { ToastContainer } from '@/components/Toast';
import { useToast } from '@/hooks/useToast';

export default function Home() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedChatSessionId, setSelectedChatSessionId] = useState<string | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [runConfigDraft, setRunConfigDraft] = useState<any | null>(null);
  const [showSpecPanel, setShowSpecPanel] = useState(true);
  const [showRunConfig, setShowRunConfig] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [showRunHistory, setShowRunHistory] = useState(false);
  const [showProjectEdit, setShowProjectEdit] = useState(false);
  const [showIssues, setShowIssues] = useState(false);
  const queryClient = useQueryClient();
  const specPanelScrollRef = useRef<HTMLDivElement>(null);
  const hasScrolledToTopRef = useRef(false);
  const chatInterfaceRef = useRef<ChatInterfaceRef>(null);
  const { toasts, removeToast } = useToast();

  // Handler to create analysis chat for a run
  const createAnalysisChatMutation = useMutation({
    mutationFn: async (runId: string) => {
      if (!selectedProjectId) throw new Error('No project selected');
      const chatTitle = `Analysis: Run ${runId.slice(0, 8)}`;
      const chatSession = await chatSessionsApi.create(
        selectedProjectId,
        chatTitle,
        'analysis',
        runId
      );
      return chatSession;
    },
    onSuccess: (chatSession) => {
      setSelectedChatSessionId(chatSession.id);
      queryClient.invalidateQueries({ queryKey: ['chatSessions', selectedProjectId] });
    },
  });

  const handleCreateAnalysisChat = (runId: string) => {
    createAnalysisChatMutation.mutate(runId);
  };

  // Prevent browser from restoring scroll position
  useEffect(() => {
    if (typeof window !== 'undefined' && 'scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }
  }, []);

  // Reset chat session and clear cache when project changes
  useEffect(() => {
    setSelectedChatSessionId(null);
    setActiveRunId(null);
    // Clear messages cache to prevent showing old messages
    queryClient.removeQueries({ queryKey: ['messages'] });
    // Scroll spec panel to top when project changes
    if (specPanelScrollRef.current) {
      // Find the inner scroll container
      const scrollContainer = specPanelScrollRef.current.querySelector('.overflow-y-auto');
      if (scrollContainer) {
        // Small delay to ensure content is loaded
        setTimeout(() => {
          scrollContainer.scrollTop = 0;
        }, 100);
      }
    }
  }, [selectedProjectId, queryClient]);

  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
  });

  if (projectsLoading) {
    return (
        <div className="flex min-h-screen items-center justify-center">
        <div className="text-lg text-gray-900">Loading...</div>
      </div>
    );
  }

  // If no project selected, show chat-first interface
  if (!selectedProjectId) {
    return (
      <div className="flex h-screen bg-gray-50">
        {/* Main chat area */}
        <div className="flex-1 flex flex-col">
          <div className="bg-white border-b px-4 py-2 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h2 className="text-lg font-semibold text-gray-900">Int Crucible</h2>
            </div>
            <div className="flex gap-2">
              {projects && projects.length > 0 && (
                <button
                  onClick={() => {
                    // Show project selector in a modal or side panel
                    // For now, we'll add a simple dropdown or keep it minimal
                  }}
                  className="px-3 py-1 text-sm rounded bg-gray-100 text-gray-700 hover:bg-gray-200"
                >
                  Select Project
                </button>
              )}
            </div>
          </div>

          <div className="flex-1 flex overflow-hidden min-h-0">
            {/* Chat interface for project creation */}
            <div className="flex-1 flex flex-col min-h-0">
              <ChatInterface
                ref={chatInterfaceRef}
                projectId={null}
                chatSessionId={null}
                onChatSessionChange={(chatSessionId) => {
                  // When a project is created, the ChatInterface will call onProjectCreated
                }}
                onProjectCreated={(projectId) => {
                  setSelectedProjectId(projectId);
                  // Refresh projects list
                  queryClient.invalidateQueries({ queryKey: ['projects'] });
                }}
              />
            </div>

            {/* Project selector sidebar (if projects exist) */}
            {projects && projects.length > 0 && (
              <div className="w-64 border-l bg-white flex-shrink-0 flex flex-col">
                <div className="p-4 border-b">
                  <h3 className="text-sm font-semibold text-gray-900 mb-2">Your Projects</h3>
                </div>
                <div className="flex-1 overflow-y-auto p-2">
                  {projects.map((project) => (
                    <button
                      key={project.id}
                      onClick={() => setSelectedProjectId(project.id)}
                      className={`w-full text-left px-3 py-2 rounded mb-1 text-sm ${
                        selectedProjectId === project.id
                          ? 'bg-blue-100 text-blue-900 font-medium'
                          : 'hover:bg-gray-100 text-gray-900'
                      }`}
                    >
                      {project.title}
                    </button>
                  ))}
                </div>
                <div className="p-2 border-t">
                  <button
                    onClick={() => {
                      // Start new project creation flow
                      // This will be handled by ChatInterface showing the greeting
                      setSelectedProjectId(null);
                    }}
                    className="w-full px-3 py-2 text-sm rounded bg-blue-600 text-white hover:bg-blue-700"
                  >
                    + New Project
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        <div className="bg-white border-b px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSelectedProjectId(null)}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              ← Back to Projects
            </button>
            <h2 className="text-lg font-semibold text-gray-900">
              {projects?.find(p => p.id === selectedProjectId)?.title || 'Project'}
            </h2>
            <button
              onClick={() => setShowProjectEdit(true)}
              className="text-sm text-gray-500 hover:text-gray-700"
              title="Edit project"
            >
              ✏️
            </button>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowSpecPanel(!showSpecPanel)}
              className={`px-3 py-1 text-sm rounded ${
                showSpecPanel
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {showSpecPanel ? 'Hide' : 'Show'} Spec
            </button>
            <button
              onClick={() => setShowRunConfig(!showRunConfig)}
              className={`px-3 py-1 text-sm rounded ${
                showRunConfig
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Run Config
            </button>
            <button
              onClick={() => setShowRunHistory(true)}
              className="px-3 py-1 text-sm rounded bg-gray-100 text-gray-700 hover:bg-gray-200"
            >
              Run History
            </button>
            <button
              onClick={() => setShowIssues(!showIssues)}
              className={`px-3 py-1 text-sm rounded ${
                showIssues
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Issues
            </button>
            {activeRunId && (
              <button
                onClick={() => setShowResults(!showResults)}
                className={`px-3 py-1 text-sm rounded ${
                  showResults
                    ? 'bg-purple-100 text-purple-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Results
              </button>
            )}
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden min-h-0">
          {/* Chat interface */}
          <div className="flex-1 flex flex-col min-h-0">
            {/* Chat session switcher */}
            {selectedProjectId && (
              <div className="flex-shrink-0">
                <ChatSessionSwitcher
                  projectId={selectedProjectId}
                  currentChatSessionId={selectedChatSessionId}
                  onChatSessionChange={setSelectedChatSessionId}
                />
              </div>
            )}
            {/* Workflow progress indicator */}
            <div className="px-4 pt-2 flex-shrink-0">
              <WorkflowProgress projectId={selectedProjectId} />
            </div>
            <div className="flex-1 min-h-0 overflow-hidden">
              <ChatInterface
                ref={chatInterfaceRef}
                projectId={selectedProjectId}
                chatSessionId={selectedChatSessionId}
                onChatSessionChange={setSelectedChatSessionId}
                onRecommendation={(config) => {
                  setRunConfigDraft(config);
                  setShowRunConfig(true);
                }}
                onRunSummary={(summary) => {
                  if (summary?.run_id) {
                    setActiveRunId(summary.run_id);
                    setShowResults(true);
                  }
                }}
              />
            </div>
          </div>

          {/* Spec panel (right side) */}
          {showSpecPanel && (
            <div 
              ref={specPanelScrollRef}
              className="w-96 border-l bg-white flex-shrink-0 flex flex-col overflow-hidden" 
            >
              <div className="flex-1 overflow-y-auto overflow-x-hidden">
                <SpecPanel 
                  projectId={selectedProjectId} 
                  chatSessionId={selectedChatSessionId}
                  onIssueCreated={(issue) => {
                    // Trigger feedback in chat
                    if (chatInterfaceRef.current) {
                      chatInterfaceRef.current.triggerIssueFeedback(issue.id);
                    }
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Run config panel (modal/overlay) */}
      {showRunConfig && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Run Configuration</h3>
              <button
                onClick={() => setShowRunConfig(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ×
              </button>
            </div>
            <RunConfigPanel
              projectId={selectedProjectId!}
              chatSessionId={selectedChatSessionId}
              architectConfig={runConfigDraft}
              onConfigApplied={() => setRunConfigDraft(null)}
              onRunCreated={(runId) => {
                setActiveRunId(runId);
                setShowRunConfig(false);
                setShowResults(true);
              }}
            />
          </div>
        </div>
      )}

      {showRunHistory && selectedProjectId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-5xl w-full mx-4 max-h-[85vh] overflow-y-auto">
            <RunHistoryPanel
              projectId={selectedProjectId}
              onClose={() => setShowRunHistory(false)}
              onSelectRun={(runId) => {
                setActiveRunId(runId);
                setShowRunHistory(false);
                setShowResults(true);
              }}
              onCreateAnalysisChat={handleCreateAnalysisChat}
            />
          </div>
        </div>
      )}

      {showIssues && selectedProjectId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-5xl w-full mx-4 max-h-[85vh] overflow-y-auto flex flex-col">
            <IssuesPanel
              projectId={selectedProjectId}
              runId={activeRunId}
              onClose={() => setShowIssues(false)}
              onIssueSelected={(issueId) => {
                // Trigger feedback in chat for selected issue
                if (chatInterfaceRef.current) {
                  chatInterfaceRef.current.triggerIssueFeedback(issueId);
                  setShowIssues(false);
                }
              }}
            />
          </div>
        </div>
      )}

      {/* Results view (modal/overlay) */}
      {showResults && activeRunId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-900">Run Results</h3>
              <button
                onClick={() => setShowResults(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ×
              </button>
            </div>
            <ResultsView 
              runId={activeRunId}
              onIssueCreated={(issue) => {
                // Trigger feedback in chat
                if (chatInterfaceRef.current) {
                  chatInterfaceRef.current.triggerIssueFeedback(issue.id);
                }
              }}
            />
          </div>
        </div>
      )}

      {/* Project edit modal */}
      {showProjectEdit && selectedProjectId && (
        <ProjectEditModal
          project={projects?.find(p => p.id === selectedProjectId)!}
          onClose={() => setShowProjectEdit(false)}
          onUpdated={(updatedProject) => {
            queryClient.invalidateQueries({ queryKey: ['projects'] });
            setShowProjectEdit(false);
          }}
        />
      )}

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
}
