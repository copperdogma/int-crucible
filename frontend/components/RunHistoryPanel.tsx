'use client';

import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { runsApi, Run } from '@/lib/api';

interface RunHistoryPanelProps {
  projectId: string;
  onClose: () => void;
  onSelectRun?: (runId: string) => void;
  onCreateAnalysisChat?: (runId: string) => void;
}

const STATUS_OPTIONS = [
  { label: 'All statuses', value: 'all' },
  { label: 'Completed', value: 'completed' },
  { label: 'Running', value: 'running' },
  { label: 'Failed', value: 'failed' },
  { label: 'Created', value: 'created' },
];

export default function RunHistoryPanel({ projectId, onClose, onSelectRun, onCreateAnalysisChat }: RunHistoryPanelProps) {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [limit, setLimit] = useState<number>(20);
  const [offset, setOffset] = useState<number>(0);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['run-history', projectId, statusFilter, limit, offset],
    queryFn: () =>
      runsApi.listSummary(projectId, {
        limit,
        offset,
        status: statusFilter === 'all' ? undefined : [statusFilter],
      }),
    enabled: !!projectId,
    keepPreviousData: true,
  });

  const selectedRun: Run | null = useMemo(() => {
    if (!data || !selectedRunId) return null;
    return data.runs.find((run) => run.id === selectedRunId) ?? null;
  }, [data, selectedRunId]);

  const handleSelectRun = (run: Run) => {
    setSelectedRunId(run.id);
  };

  const handleOpenResults = () => {
    if (selectedRun && onSelectRun) {
      onSelectRun(selectedRun.id);
      onClose();
    }
  };

  const handlePaginate = (direction: 'next' | 'prev') => {
    if (!data) return;
    if (direction === 'next' && data.has_more) {
      setOffset(offset + limit);
    } else if (direction === 'prev') {
      setOffset(Math.max(0, offset - limit));
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Run History</h3>
          <p className="text-sm text-gray-500">
            Recent pipeline runs with status, counts, and resource usage.
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
          Status
          <select
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value);
              setOffset(0);
            }}
            className="mt-1 border rounded px-2 py-1 text-sm"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm text-gray-700 flex flex-col">
          Rows
          <select
            value={limit}
            onChange={(event) => {
              setLimit(Number(event.target.value));
              setOffset(0);
            }}
            className="mt-1 border rounded px-2 py-1 text-sm"
          >
            {[10, 20, 50].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="flex-1 overflow-y-auto border rounded-lg bg-white shadow-sm">
        {isLoading ? (
          <div className="p-6 text-center text-gray-600">Loading history…</div>
        ) : !data || data.runs.length === 0 ? (
          <div className="p-6 text-center text-gray-600">
            No runs recorded yet. Launch a run to populate history.
          </div>
        ) : (
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-3 py-2 text-left">Run</th>
                <th className="px-3 py-2 text-left">Status</th>
                <th className="px-3 py-2 text-left">Created</th>
                <th className="px-3 py-2 text-right">Duration</th>
                <th className="px-3 py-2 text-center">Counts (C/S/E)</th>
                <th className="px-3 py-2 text-center">LLM Calls</th>
                <th className="px-3 py-2 text-right">Cost ($)</th>
              </tr>
            </thead>
            <tbody>
              {data.runs.map((run) => {
                const status = run.status ?? 'unknown';
                const tokens =
                  run.llm_usage?.total?.call_count ??
                  run.llm_usage?.phases?.evaluation?.call_count ??
                  0;
                const cost =
                  run.llm_usage?.total?.cost_usd ??
                  run.llm_usage?.phases?.evaluation?.cost_usd ??
                  null;
                const duration = run.duration_seconds
                  ? `${run.duration_seconds.toFixed(1)}s`
                  : '—';
                const rowSelected = selectedRunId === run.id;

                return (
                  <tr
                    key={run.id}
                    onClick={() => handleSelectRun(run)}
                    className={`cursor-pointer ${
                      rowSelected ? 'bg-purple-50' : 'hover:bg-gray-50'
                    }`}
                  >
                    <td className="px-3 py-2 font-mono text-xs text-gray-800">{run.id}</td>
                    <td className="px-3 py-2">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-semibold ${
                          status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {status}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-gray-700">
                      {run.created_at ? new Date(run.created_at).toLocaleString() : '—'}
                    </td>
                    <td className="px-3 py-2 text-right text-gray-700">{duration}</td>
                    <td className="px-3 py-2 text-center text-gray-700">
                      {(run.candidate_count ?? 0)}/{(run.scenario_count ?? 0)}/
                      {(run.evaluation_count ?? 0)}
                    </td>
                    <td className="px-3 py-2 text-center text-gray-700">{tokens ?? 0}</td>
                    <td className="px-3 py-2 text-right text-gray-700">
                      {cost !== null && cost !== undefined ? cost.toFixed(4) : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <div className="flex items-center justify-between mt-3 text-sm text-gray-600">
        <div>
          Showing {data?.runs.length ?? 0} of {data?.total ?? 0} runs
          {isFetching && ' · refreshing…'}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handlePaginate('prev')}
            className="px-3 py-1 rounded border border-gray-300 disabled:opacity-50"
            disabled={offset === 0}
          >
            Previous
          </button>
          <button
            onClick={() => handlePaginate('next')}
            className="px-3 py-1 rounded border border-gray-300 disabled:opacity-50"
            disabled={!data?.has_more}
          >
            Next
          </button>
        </div>
      </div>

      <div className="mt-4 border rounded-lg p-4 bg-white shadow-sm">
        {selectedRun ? (
          <div>
            <div className="flex items-center justify-between mb-2">
              <div>
                <h4 className="text-md font-semibold text-gray-900">
                  Run {selectedRun.id} details
                </h4>
                <p className="text-xs text-gray-500">
                  Started:{' '}
                  {selectedRun.started_at
                    ? new Date(selectedRun.started_at).toLocaleString()
                    : 'n/a'}
                  {' · '}Completed:{' '}
                  {selectedRun.completed_at
                    ? new Date(selectedRun.completed_at).toLocaleString()
                    : 'n/a'}
                </p>
              </div>
              <div className="flex gap-2">
                {onSelectRun && (
                  <button
                    onClick={handleOpenResults}
                    className="text-xs px-3 py-1 rounded bg-purple-600 text-white hover:bg-purple-700"
                  >
                    Open in Results
                  </button>
                )}
                {onCreateAnalysisChat && selectedRun && (
                  <button
                    onClick={() => {
                      onCreateAnalysisChat(selectedRun.id);
                      onClose();
                    }}
                    className="text-xs px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700"
                  >
                    Discuss in Chat
                  </button>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm text-gray-700">
              <div>
                <div className="font-semibold text-gray-900 mb-1">Counts</div>
                <div>Candidates: {selectedRun.candidate_count ?? '—'}</div>
                <div>Scenarios: {selectedRun.scenario_count ?? '—'}</div>
                <div>Evaluations: {selectedRun.evaluation_count ?? '—'}</div>
              </div>
              <div>
                <div className="font-semibold text-gray-900 mb-1">LLM Usage</div>
                <div>Calls: {selectedRun.llm_usage?.total?.call_count ?? '—'}</div>
                <div>
                  Tokens:{' '}
                  {selectedRun.llm_usage?.total?.total_tokens ??
                    selectedRun.llm_usage?.total?.input_tokens ??
                    '—'}
                </div>
                <div>
                  Cost:{' '}
                  {selectedRun.llm_usage?.total?.cost_usd !== undefined
                    ? `$${selectedRun.llm_usage.total.cost_usd.toFixed(4)}`
                    : '—'}
                </div>
              </div>
            </div>

            {selectedRun.error_summary && (
              <div className="mt-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
                <div className="font-semibold">Error Summary</div>
                <p>{selectedRun.error_summary}</p>
              </div>
            )}

            <div className="mt-3">
              <div className="font-semibold text-gray-900 mb-1">Phase Timings</div>
              {selectedRun.metrics?.phase_timings ? (
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {Object.entries(selectedRun.metrics.phase_timings).map(([phase, timing]) => (
                    <div key={phase} className="border rounded p-2 bg-gray-50">
                      <div className="uppercase text-gray-600 font-semibold">{phase}</div>
                      <div>Duration: {timing.duration_seconds?.toFixed(2) ?? '—'}s</div>
                      <div className="text-gray-500">
                        Started:{' '}
                        {timing.started_at ? new Date(timing.started_at).toLocaleTimeString() : '—'}
                      </div>
                      <div className="text-gray-500">
                        Finished:{' '}
                        {timing.completed_at
                          ? new Date(timing.completed_at).toLocaleTimeString()
                          : '—'}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-500">No timing metrics recorded.</div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-sm text-gray-600">
            Select a run row to see detailed metrics and status information.
          </div>
        )}
      </div>
    </div>
  );
}

