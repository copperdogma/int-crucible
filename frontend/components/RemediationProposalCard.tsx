'use client';

import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { RemediationProposal } from '@/lib/api';
import { issuesApi } from '@/lib/api';
import { useToast } from '@/hooks/useToast';

interface RemediationProposalCardProps {
  proposal: RemediationProposal;
  issueId: string;
  projectId: string;
  chatSessionId: string;
}

export default function RemediationProposalCard({
  proposal,
  issueId,
  projectId,
  chatSessionId,
}: RemediationProposalCardProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const queryClient = useQueryClient();
  const { success, error: showError } = useToast();

  const getActionTypeLabel = (actionType: string) => {
    switch (actionType) {
      case 'patch_and_rescore':
        return 'Patch and Rescore';
      case 'partial_rerun':
        return 'Partial Rerun';
      case 'full_rerun':
        return 'Full Rerun';
      case 'invalidate_candidates':
        return 'Invalidate Candidates';
      default:
        return actionType;
    }
  };

  /**
   * Get explanation for remediation action.
   * 
   * Currently uses static estimates. Future enhancement: Use dynamic estimates
   * based on historical run data. Could query API for average times from similar
   * runs/projects and show "Based on similar runs: ~X minutes" instead of static values.
   * 
   * @param actionType - Type of remediation action
   * @returns Explanation with what, time, cost, and impact
   */
  const getActionExplanation = (actionType: string) => {
    // TODO: Consider dynamic estimates based on project history
    // Example: const historicalData = await api.getRunHistory(projectId)
    //          const avgTime = calculateAverageTime(historicalData, actionType)
    //          return { time: `~${avgTime} minutes (based on ${historicalData.length} similar runs)` }
    
    switch (actionType) {
      case 'patch_and_rescore':
        return {
          what: 'Update the ProblemSpec or WorldModel, then re-score existing candidates',
          time: 'Fast (seconds to minutes)',
          cost: 'Low cost - only re-evaluates existing candidates',
          impact: 'Updates scores for existing candidates in the current run',
        };
      case 'partial_rerun':
        return {
          what: 'Update the ProblemSpec or WorldModel, then re-run evaluation and ranking phases',
          time: 'Moderate (minutes)',
          cost: 'Moderate cost - re-evaluates and re-ranks existing candidates',
          impact: 'Re-evaluates all candidates against scenarios and re-ranks them',
        };
      case 'full_rerun':
        return {
          what: 'Update the ProblemSpec or WorldModel, then create a completely new run from scratch',
          time: 'Slow (several minutes to hours)',
          cost: 'High cost - generates new candidates, scenarios, and runs full evaluation',
          impact: 'Creates a new run with new candidates, scenarios, and evaluations',
        };
      case 'invalidate_candidates':
        return {
          what: 'Mark specific candidates as rejected due to the issue',
          time: 'Instant',
          cost: 'No cost - just updates candidate status',
          impact: 'Marks selected candidates as rejected',
        };
      default:
        return {
          what: 'Apply remediation action',
          time: 'Unknown',
          cost: 'Unknown',
          impact: 'Unknown',
        };
    }
  };

  const requiresConfirmation = (actionType: string) => {
    // Require confirmation for expensive/time-consuming actions
    return actionType === 'full_rerun';
  };

  const handleApproveClick = () => {
    if (requiresConfirmation(proposal.action_type)) {
      setShowConfirmDialog(true);
    } else {
      handleApprove();
    }
  };

  const handleApprove = async () => {
    setShowConfirmDialog(false);
    setIsProcessing(true);
    try {
      const result = await issuesApi.resolve(
        issueId,
        proposal.action_type,
        {
          problem_spec: proposal.description.includes('ProblemSpec') ? {} : undefined,
          world_model: proposal.description.includes('WorldModel') ? {} : undefined,
        }
      );
      await queryClient.invalidateQueries({ queryKey: ['messages', chatSessionId] });
      await queryClient.invalidateQueries({ queryKey: ['issues', projectId] });
      
      // Show success notification
      let successMessage = result.message || `Remediation applied successfully: ${getActionTypeLabel(proposal.action_type)}`;
      if (result.action_upgraded && result.original_remediation_action) {
        // Action was auto-upgraded - show informative message
        const originalLabel = getActionTypeLabel(result.original_remediation_action);
        const actualLabel = getActionTypeLabel(result.remediation_action);
        successMessage = `Remediation applied: ${actualLabel} (auto-upgraded from ${originalLabel} because issue has no associated run)`;
      }
      success(successMessage);
    } catch (err) {
      console.error('Failed to resolve issue:', err);
      showError('Failed to apply remediation. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = () => {
    // Acknowledge rejection
    console.log('Remediation proposal rejected');
    success('Remediation proposal rejected');
  };

  const getActionTypeColor = (actionType: string) => {
    switch (actionType) {
      case 'patch_and_rescore':
        return 'bg-yellow-50 border-yellow-200';
      case 'partial_rerun':
        return 'bg-orange-50 border-orange-200';
      case 'full_rerun':
        return 'bg-red-50 border-red-200';
      case 'invalidate_candidates':
        return 'bg-gray-50 border-gray-200';
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  const actionExplanation = getActionExplanation(proposal.action_type);
  const needsConfirmation = requiresConfirmation(proposal.action_type);

  return (
    <>
      <div className={`mt-4 p-4 border-2 rounded-lg ${getActionTypeColor(proposal.action_type)}`}>
        <div className="flex items-start justify-between mb-3">
          <div>
            <h4 className="font-semibold text-gray-900 mb-1">
              Remediation Proposal
            </h4>
            <span className="text-xs px-2 py-1 bg-white rounded border">
              {getActionTypeLabel(proposal.action_type)}
            </span>
          </div>
        </div>

        {/* What Will Happen Section - Prominent */}
        <div className="mb-4 p-3 bg-white rounded border border-gray-300">
          <h5 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
            {needsConfirmation && <span className="text-red-600">⚠️</span>}
            What will happen:
          </h5>
          <ul className="space-y-1 text-sm text-gray-700">
            <li className="flex items-start gap-2">
              <span className="text-gray-400">•</span>
              <span><strong>Action:</strong> {actionExplanation.what}</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-gray-400">•</span>
              <span><strong>Time:</strong> {actionExplanation.time}</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-gray-400">•</span>
              <span><strong>Cost:</strong> {actionExplanation.cost}</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-gray-400">•</span>
              <span><strong>Impact:</strong> {actionExplanation.impact}</span>
            </li>
          </ul>
        </div>

        <div className="space-y-2 text-sm text-gray-700 mb-4">
          {proposal.description && (
            <div>
              <span className="font-medium">Description:</span>
              <p className="mt-1">{proposal.description}</p>
            </div>
          )}
          {proposal.estimated_impact && (
            <div>
              <span className="font-medium">Estimated Impact:</span>
              <p className="mt-1">{proposal.estimated_impact}</p>
            </div>
          )}
          {proposal.rationale && (
            <div>
              <span className="font-medium">Rationale:</span>
              <p className="mt-1">{proposal.rationale}</p>
            </div>
          )}
        </div>

        <div className="flex gap-2 pt-2 border-t border-gray-300">
          <button
            onClick={handleApproveClick}
            disabled={isProcessing}
            className={`flex-1 px-4 py-2 text-sm rounded hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed ${
              needsConfirmation
                ? 'bg-red-600 text-white hover:bg-red-700'
                : 'bg-green-600 text-white hover:bg-green-700'
            }`}
          >
            {isProcessing ? 'Processing...' : needsConfirmation ? '⚠️ Approve & Start Full Run' : 'Approve & Apply'}
          </button>
          <button
            onClick={handleReject}
            disabled={isProcessing}
            className="flex-1 px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Reject
          </button>
        </div>
      </div>

      {/* Confirmation Dialog for Expensive Actions */}
      {showConfirmDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="text-red-600">⚠️</span>
              Confirm Full Run
            </h3>
            <div className="mb-4 space-y-2 text-sm text-gray-700">
              <p>
                <strong>This will create a completely new run from scratch.</strong>
              </p>
              <p>This action will:</p>
              <ul className="list-disc list-inside ml-2 space-y-1">
                <li>Update the ProblemSpec or WorldModel</li>
                <li>Generate new candidates</li>
                <li>Create new scenarios</li>
                <li>Run full evaluation and ranking</li>
              </ul>
              <p className="mt-2 text-orange-600">
                <strong>⏱️ This may take several minutes to hours and will consume LLM resources.</strong>
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleApprove}
                disabled={isProcessing}
                className="flex-1 px-4 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                {isProcessing ? 'Starting...' : 'Yes, Start Full Run'}
              </button>
              <button
                onClick={() => setShowConfirmDialog(false)}
                disabled={isProcessing}
                className="flex-1 px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

