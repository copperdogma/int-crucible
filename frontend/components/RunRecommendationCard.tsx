import { useMemo } from 'react';

interface RunRecommendationCardProps {
  recommendation: any;
  onUseSettings?: () => void;
}

export default function RunRecommendationCard({ recommendation, onUseSettings }: RunRecommendationCardProps) {
  const blockers = recommendation?.blockers || [];
  const status = recommendation?.status || 'ready';
  const parameters = recommendation?.parameters || {};

  const formattedStatus = useMemo(() => {
    if (status === 'blocked') return 'Blocked';
    if (status === 'info') return 'Info';
    return 'Ready';
  }, [status]);

  return (
    <div className="mt-3 border border-blue-200 rounded-lg p-3 bg-blue-50 text-blue-900">
      <div className="flex items-center justify-between mb-2">
        <div>
          <div className="text-sm font-semibold">Architect Run Recommendation</div>
          <div className="text-xs text-blue-700 mt-0.5">Recommended run configuration settings</div>
        </div>
        <span
          className={`text-xs px-2 py-0.5 rounded ${
            status === 'blocked'
              ? 'bg-red-100 text-red-700'
              : status === 'info'
              ? 'bg-yellow-100 text-yellow-700'
              : 'bg-green-100 text-green-700'
          }`}
        >
          {formattedStatus}
        </span>
      </div>
      {recommendation?.rationale && (
        <p className="text-sm mb-2">{recommendation.rationale}</p>
      )}
      <div className="text-xs mb-2">
        <div>Mode: <span className="font-medium">{recommendation?.mode || 'full_search'}</span></div>
        <div>
          Candidates: <span className="font-medium">{parameters.num_candidates ?? 5}</span> · Scenarios:{' '}
          <span className="font-medium">{parameters.num_scenarios ?? 8}</span>
        </div>
      </div>
      {blockers.length > 0 && (
        <div className="text-xs text-red-700 mb-2">
          Blockers: {blockers.join(', ')}
        </div>
      )}
      {recommendation?.notes?.length > 0 && (
        <ul className="text-xs text-blue-800 list-disc list-inside mb-2">
          {recommendation.notes.map((note: string, idx: number) => (
            <li key={idx}>{note}</li>
          ))}
        </ul>
      )}
      <button
        className="text-xs px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        onClick={onUseSettings}
        disabled={status === 'blocked'}
        title={status === 'blocked' ? 'Complete prerequisites first' : 'Opens Run Config panel with these settings pre-filled'}
      >
        {status === 'blocked' ? 'Use These Settings' : 'Apply to Run Config'}
      </button>
      {status !== 'blocked' && (
        <p className="text-xs text-blue-700 mt-1.5">
          This will open the Run Config panel where you can review and start the run.
        </p>
      )}
    </div>
  );
}

