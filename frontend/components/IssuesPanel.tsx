'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { issuesApi, Issue } from '@/lib/api';

interface IssuesPanelProps {
  projectId: string;
  runId?: string | null;
  candidateId?: string | null;
  onClose: () => void;
  onIssueSelected?: (issueId: string) => void;
}

const TYPE_OPTIONS = [
  { label: 'All types', value: 'all' },
  { label: 'Model', value: 'model' },
  { label: 'Constraint', value: 'constraint' },
  { label: 'Evaluator', value: 'evaluator' },
  { label: 'Scenario', value: 'scenario' },
];

const SEVERITY_OPTIONS = [
  { label: 'All severities', value: 'all' },
  { label: 'Minor', value: 'minor' },
  { label: 'Important', value: 'important' },
  { label: 'Catastrophic', value: 'catastrophic' },
];

const STATUS_OPTIONS = [
  { label: 'All statuses', value: 'all' },
  { label: 'Open', value: 'open' },
  { label: 'Resolved', value: 'resolved' },
  { label: 'Invalidated', value: 'invalidated' },
];

export default function IssuesPanel({
  projectId,
  runId,
  candidateId,
  onClose,
  onIssueSelected,
}: IssuesPanelProps) {
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedIssueId, setSelectedIssueId] = useState<string | null>(null);

  const { data: issues, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['issues', projectId, runId, candidateId, typeFilter, severityFilter, statusFilter],
    queryFn: () =>
      issuesApi.list(projectId, {
        run_id: runId || undefined,
        candidate_id: candidateId || undefined,
        type: typeFilter === 'all' ? undefined : (typeFilter as Issue['type']),
        severity: severityFilter === 'all' ? undefined : (severityFilter as Issue['severity']),
        resolution_status: statusFilter === 'all' ? undefined : (statusFilter as Issue['resolution_status']),
      }),
    enabled: !!projectId,
  });

  const selectedIssue: Issue | null = useMemo(() => {
    if (!issues || !selectedIssueId) return null;
    return issues.find((issue) => issue.id === selectedIssueId) ?? null;
  }, [issues, selectedIssueId]);

  const getSeverityColor = (severity: Issue['severity']) => {
    switch (severity) {
      case 'minor':
        return 'bg-yellow-100 text-yellow-800';
      case 'important':
        return 'bg-orange-100 text-orange-800';
      case 'catastrophic':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: Issue['resolution_status']) => {
    switch (status) {
      case 'open':
        return 'bg-blue-100 text-blue-800';
      case 'resolved':
        return 'bg-green-100 text-green-800';
      case 'invalidated':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeLabel = (type: Issue['type']) => {
    switch (type) {
      case 'model':
        return 'Model';
      case 'constraint':
        return 'Constraint';
      case 'evaluator':
        return 'Evaluator';
      case 'scenario':
        return 'Scenario';
      default:
        return type;
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Issues</h3>
          <p className="text-sm text-gray-500">
            View and manage issues for this project{runId ? ` / run` : ''}{candidateId ? ` / candidate` : ''}.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="text-sm px-3 py-1 rounded border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            disabled={isFetching}
          >
            {isFetching ? 'Refreshing…' : 'Refresh'}
          </button>
          <button
            onClick={onClose}
            className="text-sm px-3 py-1 rounded bg-gray-200 text-gray-700 hover:bg-gray-300"
          >
            Close
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 mb-4">
        <label className="text-sm text-gray-700 flex flex-col">
          Type
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="mt-1 border rounded px-2 py-1 text-sm text-gray-900"
          >
            {TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm text-gray-700 flex flex-col">
          Severity
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="mt-1 border rounded px-2 py-1 text-sm text-gray-900"
          >
            {SEVERITY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm text-gray-700 flex flex-col">
          Status
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="mt-1 border rounded px-2 py-1 text-sm text-gray-900"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">Loading issues...</div>
        ) : !issues || issues.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No issues found{runId || candidateId ? ' for this context' : ''}.
          </div>
        ) : (
          <div className="space-y-2">
            {issues.map((issue) => (
              <div
                key={issue.id}
                onClick={() => setSelectedIssueId(issue.id)}
                className={`p-3 border rounded cursor-pointer hover:bg-gray-50 ${
                  selectedIssueId === issue.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs px-2 py-1 rounded ${getSeverityColor(issue.severity)}`}>
                        {issue.severity}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded ${getStatusColor(issue.resolution_status)}`}>
                        {issue.resolution_status}
                      </span>
                      <span className="text-xs text-gray-500">{getTypeLabel(issue.type)}</span>
                    </div>
                    <p className="text-sm text-gray-900 line-clamp-2">{issue.description}</p>
                  </div>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {issue.created_at && (
                    <span>Created: {new Date(issue.created_at).toLocaleString()}</span>
                  )}
                  {issue.run_id && (
                    <span className="ml-2">Run: {issue.run_id.substring(0, 8)}...</span>
                  )}
                  {issue.candidate_id && (
                    <span className="ml-2">Candidate: {issue.candidate_id.substring(0, 8)}...</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedIssue && (
        <div className="mt-4 p-4 border-t border-gray-200 bg-gray-50 rounded">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold text-gray-900">Issue Details</h4>
            <button
              onClick={() => setSelectedIssueId(null)}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              ×
            </button>
          </div>
          <div className="space-y-2 text-sm">
            <div>
              <span className="font-medium">Type:</span> {getTypeLabel(selectedIssue.type)}
            </div>
            <div>
              <span className="font-medium">Severity:</span>{' '}
              <span className={`px-2 py-1 rounded ${getSeverityColor(selectedIssue.severity)}`}>
                {selectedIssue.severity}
              </span>
            </div>
            <div>
              <span className="font-medium">Status:</span>{' '}
              <span className={`px-2 py-1 rounded ${getStatusColor(selectedIssue.resolution_status)}`}>
                {selectedIssue.resolution_status}
              </span>
            </div>
            <div>
              <span className="font-medium">Description:</span>
              <p className="mt-1 text-gray-700">{selectedIssue.description}</p>
            </div>
            {selectedIssue.run_id && (
              <div>
                <span className="font-medium">Run ID:</span> {selectedIssue.run_id}
              </div>
            )}
            {selectedIssue.candidate_id && (
              <div>
                <span className="font-medium">Candidate ID:</span> {selectedIssue.candidate_id}
              </div>
            )}
            {selectedIssue.created_at && (
              <div>
                <span className="font-medium">Created:</span>{' '}
                {new Date(selectedIssue.created_at).toLocaleString()}
              </div>
            )}
            {selectedIssue.resolved_at && (
              <div>
                <span className="font-medium">Resolved:</span>{' '}
                {new Date(selectedIssue.resolved_at).toLocaleString()}
              </div>
            )}
          </div>
          {onIssueSelected && (
            <button
              onClick={() => {
                onIssueSelected(selectedIssue.id);
                onClose();
              }}
              className="mt-3 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              View in Chat
            </button>
          )}
        </div>
      )}
    </div>
  );
}

