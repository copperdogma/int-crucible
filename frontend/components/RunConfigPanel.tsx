'use client';

import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { runsApi, problemSpecApi, worldModelApi, RunPreflightResponse } from '@/lib/api';

interface RunConfigPanelProps {
  projectId: string;
  chatSessionId: string | null;
  architectConfig?: any | null;
  onConfigApplied?: () => void;
  onRunCreated: (runId: string) => void;
}

const generateTriggerId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `ui-${Math.random().toString(36).slice(2)}`;
};

export default function RunConfigPanel({
  projectId,
  chatSessionId,
  architectConfig,
  onConfigApplied,
  onRunCreated,
}: RunConfigPanelProps) {
  const [mode, setMode] = useState<'full_search' | 'eval_only' | 'seeded'>('full_search');
  const [numCandidates, setNumCandidates] = useState(5);
  const [numScenarios, setNumScenarios] = useState(8);
  const [activeRecommendationId, setActiveRecommendationId] = useState<string | null>(null);
  const [preflight, setPreflight] = useState<RunPreflightResponse | null>(null);
  const [preflightLoading, setPreflightLoading] = useState(false);
  const [preflightError, setPreflightError] = useState<string | null>(null);

  // Check if ProblemSpec and WorldModel exist
  const { data: problemSpec } = useQuery({
    queryKey: ['problemSpec', projectId],
    queryFn: () => problemSpecApi.get(projectId),
    enabled: !!projectId,
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message === 'NOT_FOUND') {
        return false;
      }
      return failureCount < 3;
    },
  });

  const { data: worldModel } = useQuery({
    queryKey: ['worldModel', projectId],
    queryFn: () => worldModelApi.get(projectId),
    enabled: !!projectId,
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message === 'NOT_FOUND') {
        return false;
      }
      return failureCount < 3;
    },
  });

  const hasProblemSpec = !!problemSpec;
  const hasWorldModel = !!worldModel;
  const canRun = hasProblemSpec && hasWorldModel;

  useEffect(() => {
    if (!architectConfig) return;
    if (architectConfig.recommendation_id === activeRecommendationId) return;

    if (architectConfig.mode) {
      setMode(architectConfig.mode);
    }
    const params = architectConfig.parameters || {};
    if (typeof params.num_candidates === 'number') {
      setNumCandidates(params.num_candidates);
    }
    if (typeof params.num_scenarios === 'number') {
      setNumScenarios(params.num_scenarios);
    }
    setActiveRecommendationId(architectConfig.recommendation_id || null);
    onConfigApplied?.();
  }, [architectConfig, activeRecommendationId, onConfigApplied]);

  useEffect(() => {
    let cancelled = false;
    async function runPreflight() {
      if (!projectId) return;
      setPreflightLoading(true);
      setPreflightError(null);
      try {
        const response = await runsApi.preflight(
          projectId,
          mode,
          {
            num_candidates: numCandidates,
            num_scenarios: numScenarios,
          },
          chatSessionId ?? undefined,
          architectConfig?.source_message_id ?? architectConfig?.recommended_message_id ?? architectConfig?.message_id
        );
        if (!cancelled) {
          setPreflight(response);
        }
      } catch (error) {
        console.error('Run preflight failed:', error);
        if (!cancelled) {
          setPreflight(null);
          setPreflightError(error instanceof Error ? error.message : 'Unknown error');
        }
      } finally {
        if (!cancelled) {
          setPreflightLoading(false);
        }
      }
    }
    runPreflight();
    return () => {
      cancelled = true;
    };
  }, [projectId, chatSessionId, mode, numCandidates, numScenarios, architectConfig?.recommendation_id]);

  const isPreflightReady = preflight?.ready ?? false;
  const blockers = preflight?.blockers ?? [];
  const warnings = preflight?.warnings ?? [];

  const createRunMutation = useMutation({
    mutationFn: async () => {
      const run = await runsApi.create(
        projectId,
        mode,
        {
          num_candidates: numCandidates,
          num_scenarios: numScenarios,
        },
        {
          chat_session_id: chatSessionId ?? undefined,
          recommended_message_id: architectConfig?.source_message_id ?? architectConfig?.recommended_message_id,
          recommended_config_snapshot: architectConfig ?? undefined,
          ui_trigger_id: generateTriggerId(),
          ui_trigger_source: 'run_config_panel',
          ui_trigger_metadata: {
            matched_recommendation: activeRecommendationId,
          },
        }
      );
      return run;
    },
    onSuccess: async (run) => {
      // Execute full pipeline
      try {
        await runsApi.executeFullPipeline(run.id, numCandidates, numScenarios);
        onRunCreated(run.id);
      } catch (error) {
        console.error('Failed to execute pipeline:', error);
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        if (errorMessage === 'NOT_FOUND') {
          alert('Run created but pipeline execution failed: ProblemSpec or WorldModel not found. Please ensure you have a problem specification and world model before running.');
        } else {
          alert(`Run created but pipeline execution failed: ${errorMessage}. Please check the run status.`);
        }
        onRunCreated(run.id);
      }
    },
    onError: (error) => {
      console.error('Failed to create run:', error);
    },
  });

  const handleStartRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isPreflightReady) {
      return;
    }
    createRunMutation.mutate();
  };

  const recommendationBanner = useMemo(() => {
    if (!activeRecommendationId) return null;
    return (
      <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-800">
        Using Architect recommendation ({activeRecommendationId.slice(0, 8)}…). Adjust fields if you need tweaks.
      </div>
    );
  }, [activeRecommendationId]);

  return (
    <form onSubmit={handleStartRun} className="space-y-6">
      {recommendationBanner}
      {/* Prerequisites check */}
      {!canRun && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-4 mb-4">
          <h4 className="text-sm font-semibold text-yellow-800 mb-2">Prerequisites Required</h4>
          <p className="text-sm text-yellow-700 mb-2">
            Before running, you need both a Problem Specification and a World Model.
          </p>
          <ul className="text-sm text-yellow-700 space-y-1 list-disc list-inside">
            {!hasProblemSpec && <li>Problem Specification is missing</li>}
            {!hasWorldModel && <li>World Model is missing</li>}
          </ul>
          <p className="text-sm text-yellow-700 mt-2">
            Start chatting with the system to generate these automatically.
          </p>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Run Mode
        </label>
        <select
          value={mode}
          onChange={(e) => setMode(e.target.value as any)}
          className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
        >
          <option value="full_search">Full Search</option>
          <option value="eval_only">Evaluation Only</option>
          <option value="seeded">Seeded Search</option>
        </select>
        <p className="text-xs text-gray-500 mt-1">
          {mode === 'full_search' && 'Generate candidates and evaluate them'}
          {mode === 'eval_only' && 'Evaluate existing candidates only'}
          {mode === 'seeded' && 'Use seed candidates and evaluate'}
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Number of Candidates
        </label>
        <input
          type="number"
          min="1"
          max="20"
          value={numCandidates}
          onChange={(e) => setNumCandidates(parseInt(e.target.value) || 5)}
          className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Number of Scenarios
        </label>
        <input
          type="number"
          min="1"
          max="20"
          value={numScenarios}
          onChange={(e) => setNumScenarios(parseInt(e.target.value) || 8)}
          className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
        />
      </div>

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={
            createRunMutation.isPending ||
            !canRun ||
            preflightLoading ||
            !isPreflightReady
          }
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          title={!canRun ? 'Problem Specification and World Model are required' : undefined}
        >
          {createRunMutation.isPending ? 'Starting Run...' : preflightLoading ? 'Validating...' : 'Start Run'}
        </button>
      </div>

      {preflightError && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-800">
          Preflight failed: {preflightError}
        </div>
      )}

      {blockers.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-800">
          <div className="font-semibold mb-1">Blockers</div>
          <ul className="list-disc list-inside">
            {blockers.map((blocker) => (
              <li key={blocker}>{blocker}</li>
            ))}
          </ul>
        </div>
      )}

      {warnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
          <div className="font-semibold mb-1">Warnings</div>
          <ul className="list-disc list-inside">
            {warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      {createRunMutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-800">
          Failed to start run: {createRunMutation.error instanceof Error ? createRunMutation.error.message : 'Unknown error'}
        </div>
      )}
    </form>
  );
}

