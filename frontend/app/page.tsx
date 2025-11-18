'use client';

import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '@/lib/api';
import ProjectSelector from '@/components/ProjectSelector';
import ChatInterface from '@/components/ChatInterface';
import SpecPanel from '@/components/SpecPanel';
import RunConfigPanel from '@/components/RunConfigPanel';
import ResultsView from '@/components/ResultsView';
import WorkflowProgress from '@/components/WorkflowProgress';

export default function Home() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedChatSessionId, setSelectedChatSessionId] = useState<string | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [showSpecPanel, setShowSpecPanel] = useState(true);
  const [showRunConfig, setShowRunConfig] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const queryClient = useQueryClient();

  // Reset chat session and clear cache when project changes
  useEffect(() => {
    setSelectedChatSessionId(null);
    setActiveRunId(null);
    // Clear messages cache to prevent showing old messages
    queryClient.removeQueries({ queryKey: ['messages'] });
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

  // If no project selected, show project selector
  if (!selectedProjectId) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold mb-8 text-gray-900">Int Crucible</h1>
          <ProjectSelector
            projects={projects || []}
            onSelectProject={(projectId) => {
              setSelectedProjectId(projectId);
              // Create or get default chat session for this project
              // For now, we'll handle this in ChatInterface
            }}
            onCreateProject={async (title, description) => {
              const newProject = await projectsApi.create(title, description);
              setSelectedProjectId(newProject.id);
            }}
          />
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

        <div className="flex-1 flex overflow-hidden">
          {/* Chat interface */}
          <div className="flex-1 flex flex-col">
            {/* Workflow progress indicator */}
            <div className="px-4 pt-2">
              <WorkflowProgress projectId={selectedProjectId} />
            </div>
            <ChatInterface
              projectId={selectedProjectId}
              chatSessionId={selectedChatSessionId}
              onChatSessionChange={setSelectedChatSessionId}
            />
          </div>

          {/* Spec panel (right side) */}
          {showSpecPanel && (
            <div className="w-96 border-l bg-white overflow-y-auto">
              <SpecPanel projectId={selectedProjectId} />
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
              onRunCreated={(runId) => {
                setActiveRunId(runId);
                setShowRunConfig(false);
                setShowResults(true);
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
            <ResultsView runId={activeRunId} />
          </div>
        </div>
      )}
    </div>
  );
}
