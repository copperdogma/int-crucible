'use client';

import { useState } from 'react';
import { issuesApi, Issue } from '@/lib/api';

interface IssueDialogProps {
  projectId: string;
  runId?: string | null;
  candidateId?: string | null;
  onClose: () => void;
  onCreated: (issue: Issue) => void;
}

export default function IssueDialog({
  projectId,
  runId,
  candidateId,
  onClose,
  onCreated,
}: IssueDialogProps) {
  const [type, setType] = useState<'model' | 'constraint' | 'evaluator' | 'scenario'>('model');
  const [severity, setSeverity] = useState<'minor' | 'important' | 'catastrophic'>('minor');
  const [description, setDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    setIsCreating(true);
    try {
      const issue = await issuesApi.create(
        projectId,
        type,
        severity,
        description.trim(),
        runId || null,
        candidateId || null
      );
      onCreated(issue);
      onClose();
    } catch (error) {
      console.error('Failed to create issue:', error);
      alert('Failed to create issue. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-semibold text-gray-900">Flag Issue</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
          >
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Issue Type *
            </label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value as typeof type)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
              required
            >
              <option value="model">Model (World Model / Problem Spec)</option>
              <option value="constraint">Constraint</option>
              <option value="evaluator">Evaluator</option>
              <option value="scenario">Scenario</option>
            </select>
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Severity *
            </label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value as typeof severity)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
              required
            >
              <option value="minor">Minor (patch and rescore)</option>
              <option value="important">Important (partial rerun)</option>
              <option value="catastrophic">Catastrophic (full rerun or invalidate)</option>
            </select>
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description *
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
              placeholder="Describe the issue..."
              rows={6}
              required
              autoFocus
            />
          </div>
          {(runId || candidateId) && (
            <div className="mb-4 text-sm text-gray-600">
              <p>Context:</p>
              {runId && <p>• Run: {runId}</p>}
              {candidateId && <p>• Candidate: {candidateId}</p>}
            </div>
          )}
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
              disabled={isCreating}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isCreating || !description.trim()}
            >
              {isCreating ? 'Creating...' : 'Create Issue'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

