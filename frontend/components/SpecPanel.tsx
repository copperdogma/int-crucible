'use client';

import { useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { problemSpecApi, worldModelApi } from '@/lib/api';

interface SpecPanelProps {
  projectId: string;
}

export default function SpecPanel({ projectId }: SpecPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  
  const { data: problemSpec, isLoading: specLoading, error: specError } = useQuery({
    queryKey: ['problemSpec', projectId],
    queryFn: () => problemSpecApi.get(projectId),
    enabled: !!projectId,
    retry: (failureCount, error) => {
      // Don't retry on 404 errors
      if (error instanceof Error && error.message === 'NOT_FOUND') {
        return false;
      }
      return failureCount < 3;
    },
  });

  const { data: worldModel, isLoading: modelLoading, error: modelError } = useQuery({
    queryKey: ['worldModel', projectId],
    queryFn: () => worldModelApi.get(projectId),
    enabled: !!projectId,
    retry: (failureCount, error) => {
      // Don't retry on 404 errors
      if (error instanceof Error && error.message === 'NOT_FOUND') {
        return false;
      }
      return failureCount < 3;
    },
  });

  // Function to find scroll container
  const findScrollContainer = (): HTMLElement | null => {
    if (!panelRef.current) return null;
    let scrollContainer = panelRef.current.parentElement;
    while (scrollContainer && !scrollContainer.classList.contains('overflow-y-auto')) {
      scrollContainer = scrollContainer.parentElement;
    }
    return scrollContainer as HTMLElement | null;
  };

  // Note: Scroll-to-top is handled by parent component (page.tsx)
  // to avoid conflicts and ensure it only happens when needed


  if (specLoading || modelLoading) {
    return (
      <div className="p-4">
        <div className="text-gray-900">Loading spec...</div>
      </div>
    );
  }

  // Check if errors are 404s (expected for new projects)
  const specNotFound = specError instanceof Error && specError.message === 'NOT_FOUND';
  const modelNotFound = modelError instanceof Error && modelError.message === 'NOT_FOUND';

  if ((!problemSpec || specNotFound) && (!worldModel || modelNotFound)) {
    return (
      <div className="p-4">
        <div className="text-gray-700 text-sm">
          No spec or world model yet. Start chatting to generate one.
        </div>
      </div>
    );
  }

  return (
    <div ref={panelRef} className="p-4 space-y-6" style={{ minHeight: 'min-content' }}>
      <h3 className="text-lg font-semibold text-gray-900">Problem Specification</h3>

      {/* Goals */}
      {problemSpec && problemSpec.goals.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Goals</h4>
          <ul className="list-disc list-inside space-y-1 text-sm">
            {problemSpec.goals.map((goal, idx) => (
              <li key={idx} className="text-gray-800">{goal}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Constraints */}
      {problemSpec && problemSpec.constraints.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Constraints</h4>
          <ul className="space-y-2 text-sm">
            {problemSpec.constraints.map((constraint, idx) => (
              <li key={idx} className="border-l-2 border-blue-500 pl-3">
                <div className="font-medium text-gray-800">{constraint.name}</div>
                <div className="text-gray-600">{constraint.description}</div>
                <div className="text-xs text-gray-500 mt-1">
                  Weight: {constraint.weight}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Resolution */}
      {problemSpec && problemSpec.resolution && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Resolution</h4>
          <p className="text-sm text-gray-800">{problemSpec.resolution}</p>
        </div>
      )}

      {/* World Model */}
      {worldModel && worldModel.model_data && (
        <div className="mt-6 pt-6 border-t">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">World Model</h3>

          {/* Actors */}
          {worldModel.model_data.actors && worldModel.model_data.actors.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Actors</h4>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-800">
                {worldModel.model_data.actors.map((actor: any, idx: number) => (
                  <li key={idx}>{actor.name || JSON.stringify(actor)}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Assumptions */}
          {worldModel.model_data.assumptions && worldModel.model_data.assumptions.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Assumptions</h4>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-800">
                {worldModel.model_data.assumptions.map((assumption: any, idx: number) => (
                  <li key={idx}>{typeof assumption === 'string' ? assumption : JSON.stringify(assumption)}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Simplifications */}
          {worldModel.model_data.simplifications && worldModel.model_data.simplifications.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Simplifications</h4>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-800">
                {worldModel.model_data.simplifications.map((simplification: any, idx: number) => (
                  <li key={idx}>{typeof simplification === 'string' ? simplification : JSON.stringify(simplification)}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

