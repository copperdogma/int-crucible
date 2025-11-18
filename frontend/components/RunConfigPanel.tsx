'use client';

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { runsApi, problemSpecApi, worldModelApi } from '@/lib/api';

interface RunConfigPanelProps {
  projectId: string;
  onRunCreated: (runId: string) => void;
}

export default function RunConfigPanel({ projectId, onRunCreated }: RunConfigPanelProps) {
  const [mode, setMode] = useState<'full_search' | 'eval_only' | 'seeded'>('full_search');
  const [numCandidates, setNumCandidates] = useState(5);
  const [numScenarios, setNumScenarios] = useState(8);

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

  const createRunMutation = useMutation({
    mutationFn: async () => {
      const run = await runsApi.create(projectId, mode, {
        num_candidates: numCandidates,
        num_scenarios: numScenarios,
      });
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
    createRunMutation.mutate();
  };

  return (
    <form onSubmit={handleStartRun} className="space-y-6">
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
          disabled={createRunMutation.isPending || !canRun}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          title={!canRun ? 'Problem Specification and World Model are required' : undefined}
        >
          {createRunMutation.isPending ? 'Starting Run...' : 'Start Run'}
        </button>
      </div>

      {createRunMutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-800">
          Failed to start run: {createRunMutation.error instanceof Error ? createRunMutation.error.message : 'Unknown error'}
        </div>
      )}
    </form>
  );
}

