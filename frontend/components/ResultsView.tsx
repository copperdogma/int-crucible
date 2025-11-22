'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { runsApi, Candidate, CandidateDetail, Issue } from '@/lib/api';
import IssueDialog from './IssueDialog';

interface ResultsViewProps {
  runId: string;
  onIssueCreated?: (issue: Issue) => void;
}

export default function ResultsView({ runId, onIssueCreated }: ResultsViewProps) {
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [showIssueDialog, setShowIssueDialog] = useState(false);

  const { data: run, isLoading: runLoading } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => runsApi.get(runId),
  });

  const { data: candidates = [], isLoading: candidatesLoading } = useQuery({
    queryKey: ['candidates', runId],
    queryFn: () => runsApi.getRankedCandidates(runId),
    enabled: !!runId,
  });

  const { data: candidateDetail, isLoading: candidateDetailLoading } = useQuery({
    queryKey: ['candidate-detail', runId, selectedCandidateId],
    queryFn: () => runsApi.getCandidateDetail(runId, selectedCandidateId!),
    enabled: !!selectedCandidateId,
  });

  const selectedCandidate = selectedCandidateId
    ? candidates.find((c) => c.id === selectedCandidateId) || null
    : null;

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return isNaN(date.getTime()) ? timestamp : date.toLocaleString();
  };

  if (runLoading || candidatesLoading) {
    return (
      <div className="p-4">
        <div className="text-gray-900">Loading results...</div>
      </div>
    );
  }

  // Sort candidates by I score (intelligence metric) descending
  const sortedCandidates = [...candidates].sort((a, b) => {
    const aI = a.scores?.I || 0;
    const bI = b.scores?.I || 0;
    return bI - aI;
  });

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Run Status</h4>
        <div className="text-sm">
          <span className={`px-2 py-1 rounded ${
            run?.status === 'completed' ? 'bg-green-100 text-green-800' :
            run?.status === 'running' ? 'bg-yellow-100 text-yellow-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {run?.status || 'unknown'}
          </span>
        </div>
      </div>

      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-2">
          Ranked Candidates ({sortedCandidates.length})
        </h4>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {sortedCandidates.length === 0 ? (
            <div className="text-sm text-gray-700">No candidates yet.</div>
          ) : (
            sortedCandidates.map((candidate, idx) => (
              <div
                key={candidate.id}
                onClick={() => setSelectedCandidateId(candidate.id)}
                className={`p-3 border rounded cursor-pointer hover:bg-gray-50 ${
                  selectedCandidate?.id === candidate.id ? 'border-blue-500 bg-blue-50' : ''
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="font-medium text-sm">#{idx + 1}</div>
                  <div className="flex gap-2 text-xs">
                    {candidate.scores?.P !== undefined && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                        P: {typeof candidate.scores.P === 'number' ? candidate.scores.P.toFixed(2) : candidate.scores.P.overall?.toFixed(2) ?? 'N/A'}
                      </span>
                    )}
                    {candidate.scores?.R !== undefined && (
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded">
                        R: {typeof candidate.scores.R === 'number' ? candidate.scores.R.toFixed(2) : candidate.scores.R.overall?.toFixed(2) ?? 'N/A'}
                      </span>
                    )}
                    {candidate.scores?.I !== undefined && (
                      <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded font-semibold">
                        I: {candidate.scores.I.toFixed(2)}
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-sm text-gray-800 line-clamp-2">
                  {candidate.mechanism_description}
                </div>
                {candidate.scores?.ranking_explanation && (
                  <div className={`text-xs mt-1 ${
                    idx === 0 ? 'font-semibold text-gray-800' : 'text-gray-600'
                  }`}>
                    {(() => {
                      const firstSentence = candidate.scores.ranking_explanation.split('.')[0];
                      const truncated = firstSentence.slice(0, 80);
                      return truncated + (firstSentence.length > 80 ? '...' : '');
                    })()}
                  </div>
                )}
                {candidate.provenance_summary?.last_event && (
                  <div className="mt-2 text-xs text-gray-500">
                    Last event: {candidate.provenance_summary.last_event.type ?? 'update'} ·{' '}
                    {formatTimestamp(candidate.provenance_summary.last_event.timestamp)}
                  </div>
                )}
                {candidate.constraint_flags && candidate.constraint_flags.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {candidate.constraint_flags.map((flag, flagIdx) => (
                      <span
                        key={flagIdx}
                        className="text-xs px-2 py-1 bg-red-100 text-red-800 rounded"
                      >
                        ⚠ {flag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Candidate detail modal */}
      {selectedCandidate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Candidate Details</h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowIssueDialog(true)}
                  className="text-sm px-3 py-1 bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200"
                  title="Flag an issue with this candidate"
                >
                  ⚠ Flag Issue
                </button>
                <button
                  onClick={() => setSelectedCandidateId(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ×
                </button>
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Mechanism Description</h4>
                <p className="text-sm text-gray-800 whitespace-pre-wrap">
                  {candidateDetail?.mechanism_description ?? selectedCandidate.mechanism_description}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="text-gray-600">
                  <span className="font-semibold text-gray-800">Origin:</span>{' '}
                  {(candidateDetail?.origin ?? selectedCandidate.origin) || 'unknown'}
                </div>
                <div className="text-gray-600">
                  <span className="font-semibold text-gray-800">Status:</span>{' '}
                  {(candidateDetail?.status ?? selectedCandidate.status) || 'unknown'}
                </div>
              </div>
              {candidateDetail?.parent_summaries && candidateDetail.parent_summaries.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Parents</h4>
                  <div className="flex flex-wrap gap-2">
                    {candidateDetail.parent_summaries.map((parent) => (
                      <div
                        key={parent.id}
                        className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-800"
                      >
                        {parent.id.slice(0, 8)} — {parent.status ?? 'unknown'}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {selectedCandidate.scores && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Scores</h4>
                  <div className="grid grid-cols-3 gap-2">
                    {selectedCandidate.scores.P !== undefined && (
                      <div className="p-2 bg-blue-50 rounded">
                        <div className="text-xs text-blue-600">Prediction Quality (P)</div>
                        <div className="text-lg font-semibold">
                          {typeof selectedCandidate.scores.P === 'number' 
                            ? selectedCandidate.scores.P.toFixed(2)
                            : selectedCandidate.scores.P.overall?.toFixed(2) ?? 'N/A'}
                        </div>
                      </div>
                    )}
                    {selectedCandidate.scores.R !== undefined && (
                      <div className="p-2 bg-green-50 rounded">
                        <div className="text-xs text-green-600">Resource Cost (R)</div>
                        <div className="text-lg font-semibold">
                          {typeof selectedCandidate.scores.R === 'number'
                            ? selectedCandidate.scores.R.toFixed(2)
                            : selectedCandidate.scores.R.overall?.toFixed(2) ?? 'N/A'}
                        </div>
                      </div>
                    )}
                    {selectedCandidate.scores.I !== undefined && (
                      <div className="p-2 bg-purple-50 rounded">
                        <div className="text-xs text-purple-600">Intelligence (I = P/R)</div>
                        <div className="text-lg font-semibold">{selectedCandidate.scores.I.toFixed(2)}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}
              {(candidateDetail?.scores?.ranking_explanation || selectedCandidate.scores?.ranking_explanation) && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Why this rank?</h4>
                  <p className="text-sm text-gray-800 mb-3">
                    {(candidateDetail?.scores ?? selectedCandidate.scores)?.ranking_explanation}
                  </p>
                  {(candidateDetail?.scores ?? selectedCandidate.scores)?.ranking_factors?.top_positive_factors?.length > 0 && (
                    <div className="mb-2">
                      <div className="text-xs font-semibold text-green-700 mb-1">Strengths:</div>
                      <ul className="list-disc list-inside text-xs text-green-800 space-y-0.5">
                        {(candidateDetail?.scores ?? selectedCandidate.scores)?.ranking_factors.top_positive_factors.map((factor, idx) => (
                          <li key={idx}>{factor}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {(candidateDetail?.scores ?? selectedCandidate.scores)?.ranking_factors?.top_negative_factors?.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-yellow-700 mb-1">Weaknesses:</div>
                      <ul className="list-disc list-inside text-xs text-yellow-800 space-y-0.5">
                        {(candidateDetail?.scores ?? selectedCandidate.scores)?.ranking_factors.top_negative_factors.map((factor, idx) => (
                          <li key={idx}>{factor}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
              {(candidateDetail?.constraint_flags ?? selectedCandidate.constraint_flags)?.length ? (
                <div>
                  <h4 className="text-sm font-semibold text-red-700 mb-2">Constraint Violations</h4>
                  <ul className="list-disc list-inside text-sm text-red-800">
                    {(candidateDetail?.constraint_flags ?? selectedCandidate.constraint_flags)!.map((flag, idx) => (
                      <li key={idx}>{flag}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {(candidateDetail?.predicted_effects ?? selectedCandidate.predicted_effects) && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Predicted Effects</h4>
                  <pre className="text-xs bg-gray-50 p-3 rounded overflow-x-auto">
                    {JSON.stringify(candidateDetail?.predicted_effects ?? selectedCandidate.predicted_effects, null, 2)}
                  </pre>
                </div>
              )}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Lineage</h4>
                {candidateDetailLoading ? (
                  <div className="text-sm text-gray-600">Loading provenance...</div>
                ) : candidateDetail?.provenance_log?.length ? (
                  <ul className="space-y-2">
                    {candidateDetail.provenance_log
                      .slice()
                      .reverse()
                      .map((entry, idx) => (
                        <li key={`${entry.timestamp}-${idx}`} className="text-sm border-l-2 border-gray-200 pl-3">
                          <div className="text-gray-900">
                            <span className="font-semibold">{entry.type}</span> · {formatTimestamp(entry.timestamp)}
                          </div>
                          {entry.description && (
                            <div className="text-gray-700">{entry.description}</div>
                          )}
                          <div className="text-xs text-gray-500">
                            Actor: {entry.actor}
                            {entry.source ? ` · Source: ${entry.source}` : ''}
                          </div>
                        </li>
                      ))}
                  </ul>
                ) : (
                  <div className="text-sm text-gray-600">No provenance entries yet.</div>
                )}
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Evaluations</h4>
                {candidateDetailLoading ? (
                  <div className="text-sm text-gray-600">Loading evaluations...</div>
                ) : candidateDetail?.evaluations?.length ? (
                  <div className="space-y-2">
                    {candidateDetail.evaluations.map((evaluation) => (
                      <div key={evaluation.id} className="border rounded p-2">
                        <div className="text-xs text-gray-500 mb-1">
                          Scenario: {evaluation.scenario_id}
                        </div>
                        <div className="text-sm text-gray-800">
                          P: {evaluation.P?.overall ?? 'n/a'} · R: {evaluation.R?.overall ?? 'n/a'}
                        </div>
                        {evaluation.explanation && (
                          <div className="text-xs text-gray-600 mt-1">{evaluation.explanation}</div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-gray-600">No evaluations recorded yet.</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {showIssueDialog && run && (
        <IssueDialog
          projectId={run.project_id}
          runId={runId}
          candidateId={selectedCandidateId}
          onClose={() => setShowIssueDialog(false)}
          onCreated={(issue: Issue) => {
            console.log('Issue created:', issue);
            setShowIssueDialog(false);
            if (onIssueCreated) {
              onIssueCreated(issue);
            }
          }}
        />
      )}
    </div>
  );
}

