interface RunSummaryCardProps {
  summary: any;
  onViewResults?: () => void;
}

export default function RunSummaryCard({ summary, onViewResults }: RunSummaryCardProps) {
  const counts = summary?.counts || {};
  const topCandidates = summary?.top_candidates || [];

  return (
    <div className="mt-3 border border-purple-200 rounded-lg p-3 bg-purple-50 text-purple-900">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-semibold">Run Summary</div>
        {summary?.mode && (
          <span className="text-xs px-2 py-0.5 rounded bg-purple-100 text-purple-700">
            {summary.mode}
          </span>
        )}
      </div>
      <div className="text-xs mb-2">
        <div>
          Candidates: <span className="font-medium">{counts.candidates ?? 0}</span> · Scenarios:{' '}
          <span className="font-medium">{counts.scenarios ?? 0}</span> · Evaluations:{' '}
          <span className="font-medium">{counts.evaluations ?? 0}</span>
        </div>
        {summary?.duration_seconds && (
          <div>Duration: {Math.round(summary.duration_seconds)}s</div>
        )}
      </div>
      {topCandidates.length > 0 && (
        <div className="text-xs mb-2">
          <div className="font-semibold">Top candidates:</div>
          <ul className="list-disc list-inside">
            {topCandidates.map((candidate: any, idx: number) => (
              <li key={candidate.candidate_id ?? idx}>
                {candidate.label ?? candidate.candidate_id}{' '}
                {typeof candidate.I === 'number' && (
                  <span className="font-medium">I={candidate.I.toFixed(2)}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
      <button
        className="text-xs px-3 py-1 rounded bg-purple-600 text-white hover:bg-purple-700"
        onClick={onViewResults}
      >
        View Run Results
      </button>
    </div>
  );
}

