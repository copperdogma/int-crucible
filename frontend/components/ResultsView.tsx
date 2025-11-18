'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { runsApi, Candidate } from '@/lib/api';

interface ResultsViewProps {
  runId: string;
}

export default function ResultsView({ runId }: ResultsViewProps) {
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);

  const { data: run, isLoading: runLoading } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => runsApi.get(runId),
  });

  const { data: candidates = [], isLoading: candidatesLoading } = useQuery({
    queryKey: ['candidates', runId],
    queryFn: () => runsApi.getRankedCandidates(runId),
    enabled: !!runId,
  });

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
                onClick={() => setSelectedCandidate(candidate)}
                className={`p-3 border rounded cursor-pointer hover:bg-gray-50 ${
                  selectedCandidate?.id === candidate.id ? 'border-blue-500 bg-blue-50' : ''
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="font-medium text-sm">#{idx + 1}</div>
                  <div className="flex gap-2 text-xs">
                    {candidate.scores?.P !== undefined && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                        P: {candidate.scores.P.toFixed(2)}
                      </span>
                    )}
                    {candidate.scores?.R !== undefined && (
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded">
                        R: {candidate.scores.R.toFixed(2)}
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
              <button
                onClick={() => setSelectedCandidate(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ×
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Mechanism Description</h4>
                <p className="text-sm text-gray-800 whitespace-pre-wrap">
                  {selectedCandidate.mechanism_description}
                </p>
              </div>
              {selectedCandidate.scores && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Scores</h4>
                  <div className="grid grid-cols-3 gap-2">
                    {selectedCandidate.scores.P !== undefined && (
                      <div className="p-2 bg-blue-50 rounded">
                        <div className="text-xs text-blue-600">Prediction Quality (P)</div>
                        <div className="text-lg font-semibold">{selectedCandidate.scores.P.toFixed(2)}</div>
                      </div>
                    )}
                    {selectedCandidate.scores.R !== undefined && (
                      <div className="p-2 bg-green-50 rounded">
                        <div className="text-xs text-green-600">Resource Cost (R)</div>
                        <div className="text-lg font-semibold">{selectedCandidate.scores.R.toFixed(2)}</div>
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
              {selectedCandidate.constraint_flags && selectedCandidate.constraint_flags.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-red-700 mb-2">Constraint Violations</h4>
                  <ul className="list-disc list-inside text-sm text-red-800">
                    {selectedCandidate.constraint_flags.map((flag, idx) => (
                      <li key={idx}>{flag}</li>
                    ))}
                  </ul>
                </div>
              )}
              {selectedCandidate.predicted_effects && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Predicted Effects</h4>
                  <pre className="text-xs bg-gray-50 p-3 rounded overflow-x-auto">
                    {JSON.stringify(selectedCandidate.predicted_effects, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

