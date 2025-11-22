'use client';

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { problemSpecApi, worldModelApi, messagesApi, Issue } from '@/lib/api';
import IssueDialog from './IssueDialog';

interface SpecPanelProps {
  projectId: string;
  chatSessionId?: string | null;
}

interface SectionHighlight {
  section: string;
  timestamp: number;
}

export default function SpecPanel({ projectId, chatSessionId, onIssueCreated }: SpecPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  // Track individual item highlights with delta-based ordering (newest = highest index)
  // Key format: "constraints:Budget", "goals:0", "resolution", etc.
  const [highlightedItems, setHighlightedItems] = useState<Map<string, number>>(new Map());
  const [showIssueDialog, setShowIssueDialog] = useState(false);
  
  // Fetch messages to get delta information
  const { data: messages = [] } = useQuery({
    queryKey: ['messages', chatSessionId],
    queryFn: () => (chatSessionId ? messagesApi.list(chatSessionId) : []),
    enabled: !!chatSessionId,
  });
  
  // Extract individual item changes from Architect messages with delta-based ordering
  useEffect(() => {
    if (!messages || messages.length === 0) return;
    
    const newHighlights = new Map<string, number>();
    
    // Get all Architect messages with deltas, ordered by creation time (oldest to newest)
    // We need to preserve the original message order to assign correct delta indices
    const architectMessagesWithDeltas = messages
      .map((msg: any, originalIndex: number) => ({
        ...msg,
        originalIndex
      }))
      .filter((msg: any) => msg.role === 'agent' && msg.message_metadata?.spec_delta)
      .sort((a: any, b: any) => {
        // Sort by created_at to ensure chronological order
        const aTime = a.created_at ? new Date(a.created_at).getTime() : 0;
        const bTime = b.created_at ? new Date(b.created_at).getTime() : 0;
        return aTime - bTime;
      });
    
    // Process messages in chronological order (oldest to newest)
    // Newest message (last in array) gets highest index (most vibrant)
    architectMessagesWithDeltas.forEach((msg, msgIndex) => {
      const metadata = msg.message_metadata;
      const specDelta = metadata.spec_delta;
      
      if (!specDelta) return;
      
      // Calculate delta index: newest message (last in array) gets highest index
      // Use msgIndex which represents position in the filtered array (0 = oldest, N-1 = newest)
      const deltaIndex = msgIndex;
      
      // Track individual constraints
      if (specDelta.constraints) {
        const constraints = specDelta.constraints;
        // Track added constraints
        if (constraints.added && Array.isArray(constraints.added)) {
          constraints.added.forEach((c: any) => {
            const key = `constraints:${c.name || c}`;
            const existing = newHighlights.get(key);
            if (existing === undefined || deltaIndex > existing) {
              newHighlights.set(key, deltaIndex);
            }
          });
        }
        // Track updated constraints
        if (constraints.updated && Array.isArray(constraints.updated)) {
          constraints.updated.forEach((c: any) => {
            const key = `constraints:${c.name || c}`;
            const existing = newHighlights.get(key);
            if (existing === undefined || deltaIndex > existing) {
              newHighlights.set(key, deltaIndex);
            }
          });
        }
        // Track removed constraints (for completeness, though they won't be visible)
        if (constraints.removed && Array.isArray(constraints.removed)) {
          constraints.removed.forEach((c: any) => {
            const key = `constraints:${c.name || c}`;
            const existing = newHighlights.get(key);
            if (existing === undefined || deltaIndex > existing) {
              newHighlights.set(key, deltaIndex);
            }
          });
        }
      }
      
      // Track individual goals (by index since they don't have names)
      if (specDelta.goals) {
        const goals = specDelta.goals;
        if (goals.added && Array.isArray(goals.added)) {
          goals.added.forEach((g: string, idx: number) => {
            const key = `goals:${g}`;
            const existing = newHighlights.get(key);
            if (existing === undefined || deltaIndex > existing) {
              newHighlights.set(key, deltaIndex);
            }
          });
        }
        if (goals.removed && Array.isArray(goals.removed)) {
          goals.removed.forEach((g: string) => {
            const key = `goals:${g}`;
            const existing = newHighlights.get(key);
            if (existing === undefined || deltaIndex > existing) {
              newHighlights.set(key, deltaIndex);
            }
          });
        }
      }
      
      // Track resolution changes
      if (specDelta.resolution_changed) {
        const key = 'resolution';
        const existing = newHighlights.get(key);
        if (existing === undefined || deltaIndex > existing) {
          newHighlights.set(key, deltaIndex);
        }
      }
      
      // Track mode changes
      if (specDelta.mode_changed) {
        const key = 'mode';
        const existing = newHighlights.get(key);
        if (existing === undefined || deltaIndex > existing) {
          newHighlights.set(key, deltaIndex);
        }
      }
    });
    
    setHighlightedItems(newHighlights);
  }, [messages]);
  
  // Helper function to get highlight class based on delta index (not time)
  const getHighlightClass = (itemKey: string): string => {
    const deltaIndex = highlightedItems.get(itemKey);
    if (deltaIndex === undefined) return '';
    
    // Get all delta indices to find the maximum (newest)
    const allIndices = Array.from(highlightedItems.values());
    if (allIndices.length === 0) return '';
    
    const maxIndex = Math.max(...allIndices);
    if (maxIndex === 0) {
      // Only one delta, make it most vibrant
      return 'highlight-newest';
    }
    
    // Only the absolute newest item (deltaIndex === maxIndex) gets "newest"
    // Everything else fades based on how far behind it is
    if (deltaIndex === maxIndex) {
      return 'highlight-newest'; // Most vibrant - only the newest change
    }
    
    // Calculate how many steps behind the newest this item is
    const stepsBehind = maxIndex - deltaIndex;
    
    // If only 1 step behind, it's "recent"
    // If 2+ steps behind, it's "fading"
    if (stepsBehind === 1) {
      return 'highlight-recent'; // Medium - one step behind
    } else {
      return 'highlight-fading'; // Least vibrant - multiple steps behind
    }
  };
  
  
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

  const handleIssueCreated = (issue: Issue) => {
    // Issue created - notify parent to trigger feedback agent
    console.log('Issue created:', issue);
    if (onIssueCreated) {
      onIssueCreated(issue);
    }
  };

  return (
    <div ref={panelRef} className="p-4 space-y-6" style={{ minHeight: 'min-content' }}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Problem Specification</h3>
        <button
          onClick={() => setShowIssueDialog(true)}
          className="text-sm px-3 py-1 bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200"
          title="Flag an issue with this spec"
        >
          ⚠ Flag Issue
        </button>
      </div>

      {/* Goals */}
      {problemSpec && problemSpec.goals.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Goals</h4>
          <ul className="list-disc list-inside space-y-1 text-sm">
            {problemSpec.goals.map((goal, idx) => {
              const highlightClass = getHighlightClass(`goals:${goal}`);
              return (
                <li key={idx} className={`${highlightClass} pl-3 text-gray-800`}>{goal}</li>
              );
            })}
          </ul>
        </div>
      )}

      {/* Constraints */}
      {problemSpec && problemSpec.constraints.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Constraints</h4>
          <ul className="space-y-2 text-sm">
            {problemSpec.constraints.map((constraint, idx) => {
              // Check if this specific constraint was recently changed
              // Match constraint name exactly (case-sensitive)
              const highlightClass = getHighlightClass(`constraints:${constraint.name}`);
              const baseClasses = highlightClass ? '' : 'border-l-2 border-blue-500';
              return (
              <li 
                key={idx} 
                className={`${highlightClass || baseClasses} pl-3`}
              >
                <div className="font-medium text-gray-800">{constraint.name}</div>
                <div className="text-gray-600">{constraint.description}</div>
                <div className="text-xs text-gray-500 mt-1">
                  Weight: {constraint.weight}
                </div>
              </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* Resolution */}
      {problemSpec && problemSpec.resolution && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Resolution</h4>
          {(() => {
            const resolutionHighlight = getHighlightClass('resolution');
            const resolutionBorder = resolutionHighlight || 'border-l-2 border-blue-500';
            return (
              <p className={`text-sm text-gray-800 pl-3 py-1 ${resolutionBorder}`}>
                {problemSpec.resolution}
              </p>
            );
          })()}
        </div>
      )}

      {/* World Model */}
      {worldModel && worldModel.model_data && (
        <div className="mt-6 pt-6 border-t">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">World Model</h3>

          {/* Actors */}
          {worldModel.model_data.actors && worldModel.model_data.actors.length > 0 && (
            <div className={`mb-4 ${getHighlightClass('actors')}`}>
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
            <div className={`mb-4 ${getHighlightClass('assumptions')}`}>
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
            <div className={getHighlightClass('simplifications')}>
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

      {showIssueDialog && (
        <IssueDialog
          projectId={projectId}
          onClose={() => setShowIssueDialog(false)}
          onCreated={handleIssueCreated}
        />
      )}
    </div>
  );
}

