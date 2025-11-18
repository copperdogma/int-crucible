'use client';

import { useQuery } from '@tanstack/react-query';
import { guidanceApi, WorkflowState } from '@/lib/api';

interface WorkflowProgressProps {
  projectId: string;
}

export default function WorkflowProgress({ projectId }: WorkflowProgressProps) {
  const { data: workflowState, isLoading } = useQuery<WorkflowState>({
    queryKey: ['workflowState', projectId],
    queryFn: () => guidanceApi.getWorkflowState(projectId),
    enabled: !!projectId,
  });

  if (isLoading || !workflowState) {
    return null;
  }

  const steps = [
    { name: 'ProblemSpec', completed: workflowState.has_problem_spec },
    { name: 'WorldModel', completed: workflowState.has_world_model },
    { name: 'Run', completed: workflowState.has_runs },
  ];

  const completedCount = steps.filter(s => s.completed).length;
  const totalSteps = steps.length;

  return (
    <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-semibold text-blue-900">Workflow Progress</h4>
        <span className="text-xs text-blue-700">
          {completedCount} / {totalSteps} steps completed
        </span>
      </div>
      <div className="flex gap-2">
        {steps.map((step, idx) => (
          <div
            key={step.name}
            className={`flex-1 h-2 rounded ${
              step.completed
                ? 'bg-blue-600'
                : idx <= completedCount
                ? 'bg-blue-300'
                : 'bg-gray-200'
            }`}
            title={`${step.name}: ${step.completed ? 'Completed' : 'Pending'}`}
          />
        ))}
      </div>
      <div className="mt-2 text-xs text-blue-700">
        {!workflowState.has_problem_spec && (
          <span>Start by chatting to create a ProblemSpec</span>
        )}
        {workflowState.has_problem_spec && !workflowState.has_world_model && (
          <span>Generate a WorldModel to continue</span>
        )}
        {workflowState.has_world_model && !workflowState.has_runs && (
          <span>Ready to run! Configure and start your first run</span>
        )}
        {workflowState.has_runs && (
          <span>Great! You've completed {workflowState.run_count} run(s)</span>
        )}
      </div>
    </div>
  );
}

