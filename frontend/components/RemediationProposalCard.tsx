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

  const handleApprove = async () => {
    setIsProcessing(true);
    try {
      await issuesApi.resolve(
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
      const actionLabel = getActionTypeLabel(proposal.action_type);
      success(`Remediation applied successfully: ${actionLabel}`);
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

  return (
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

      <div className="space-y-2 text-sm text-gray-700 mb-4">
        <div>
          <span className="font-medium">Description:</span>
          <p className="mt-1">{proposal.description}</p>
        </div>
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
          onClick={handleApprove}
          disabled={isProcessing}
          className="flex-1 px-4 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? 'Processing...' : 'Approve & Apply'}
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
  );
}

