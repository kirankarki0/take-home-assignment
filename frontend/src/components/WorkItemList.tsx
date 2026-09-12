import React, { useState } from 'react';
import type { WorkItem } from '../types/work-item';
import {
  useWorkItems,
  useTriggerAnalysis,
  useRetryAnalysis,
  useCompleteWorkItem,
} from '../api/workItems';
import { StatusBadge } from './StatusBadge';
import {
  Plus,
  RefreshCw,
  Play,
  RotateCcw,
  CheckCircle,
  Inbox,
  AlertCircle,
  Sparkles,
  ChevronRight,
  Filter,
} from 'lucide-react';

interface WorkItemListProps {
  selectedItemId: string | null;
  onSelectItem: (id: string) => void;
  onOpenCreate: () => void;
}

const STATUS_TABS: { label: string; value: string }[] = [
  { label: 'All Items', value: 'ALL' },
  { label: 'Received', value: 'RECEIVED' },
  { label: 'Analysing', value: 'ANALYSING' },
  { label: 'Ready for Review', value: 'READY_FOR_REVIEW' },
  { label: 'Completed', value: 'COMPLETED' },
  { label: 'Failed', value: 'FAILED' },
];

export const WorkItemList: React.FC<WorkItemListProps> = ({
  selectedItemId,
  onSelectItem,
  onOpenCreate,
}) => {
  const [activeFilter, setActiveFilter] = useState<string>('ALL');

  const { data: workItems, isLoading, isError, error, refetch, isFetching } = useWorkItems(
    activeFilter
  );

  const triggerMutation = useTriggerAnalysis();
  const retryMutation = useRetryAnalysis();
  const completeMutation = useCompleteWorkItem();

  const handleQuickAction = (e: React.MouseEvent, item: WorkItem) => {
    e.stopPropagation();
    if (item.status === 'RECEIVED') {
      triggerMutation.mutate(item.id);
    } else if (item.status === 'FAILED') {
      retryMutation.mutate(item.id);
    } else if (item.status === 'READY_FOR_REVIEW') {
      completeMutation.mutate(item.id);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header & Controls */}
      <div className="p-6 border-b border-gray-100 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-blue-600" />
              Work Intake Dashboard
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Operations triage system for incoming external items and LLM analysis
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              title="Refresh"
              className="p-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin text-blue-600' : ''}`} />
            </button>
            <button
              onClick={onOpenCreate}
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-blue-700 transition shadow-sm"
            >
              <Plus className="w-4 h-4" />
              Ingest Work Item
            </button>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 text-xs">
          <Filter className="w-3.5 h-3.5 text-gray-400 mr-1 flex-shrink-0" />
          {STATUS_TABS.map((tab) => {
            const isActive = activeFilter === tab.value;
            return (
              <button
                key={tab.value}
                onClick={() => setActiveFilter(tab.value)}
                className={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 border border-blue-200 font-semibold'
                    : 'text-gray-600 hover:bg-gray-100 border border-transparent'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <div className="w-8 h-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin mb-3" />
            <p className="text-sm">Loading work items...</p>
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center h-64 p-6 text-center">
            <AlertCircle className="w-10 h-10 text-red-500 mb-2" />
            <h3 className="text-sm font-semibold text-gray-900">Failed to load work items</h3>
            <p className="text-xs text-gray-500 mt-1 max-w-sm">
              {error?.message || 'Check backend connection.'}
            </p>
            <button
              onClick={() => refetch()}
              className="mt-4 rounded-lg bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-200 transition"
            >
              Try Again
            </button>
          </div>
        ) : !workItems || workItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 p-6 text-center text-gray-400">
            <Inbox className="w-12 h-12 stroke-1 text-gray-300 mb-2" />
            <h3 className="text-sm font-semibold text-gray-700">No work items found</h3>
            <p className="text-xs text-gray-500 mt-1 max-w-xs">
              {activeFilter !== 'ALL'
                ? `There are currently no items with status '${activeFilter}'.`
                : 'Ingest a work item above to begin processing.'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {workItems.map((item) => {
              const isSelected = selectedItemId === item.id;
              const isItemMutating =
                (triggerMutation.isPending && triggerMutation.variables === item.id) ||
                (retryMutation.isPending && retryMutation.variables === item.id) ||
                (completeMutation.isPending && completeMutation.variables === item.id);

              return (
                <div
                  key={item.id}
                  onClick={() => onSelectItem(item.id)}
                  className={`flex items-center justify-between p-4 cursor-pointer transition hover:bg-blue-50/40 ${
                    isSelected ? 'bg-blue-50/80 border-l-4 border-blue-600' : ''
                  }`}
                >
                  <div className="flex-1 min-w-0 pr-4">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs font-bold text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
                        {item.externalId}
                      </span>
                      <StatusBadge status={item.status} />

                      {item.analysisResult && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                          {item.analysisResult.priority}
                        </span>
                      )}
                    </div>

                    <h4 className="text-sm font-semibold text-gray-900 truncate">
                      {item.title}
                    </h4>
                    <p className="text-xs text-gray-500 line-clamp-1 mt-0.5">
                      {item.description}
                    </p>
                  </div>

                  {/* Contextual Quick Action Button */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {item.status === 'RECEIVED' && (
                      <button
                        onClick={(e) => handleQuickAction(e, item)}
                        disabled={isItemMutating}
                        title="Run AI Analysis"
                        className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700 hover:bg-blue-100 disabled:opacity-50 transition border border-blue-200"
                      >
                        <Play className="w-3.5 h-3.5" />
                        Analyse
                      </button>
                    )}

                    {item.status === 'FAILED' && (
                      <button
                        onClick={(e) => handleQuickAction(e, item)}
                        disabled={isItemMutating}
                        title="Retry Failed AI Analysis"
                        className="inline-flex items-center gap-1 rounded-md bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-700 hover:bg-red-100 disabled:opacity-50 transition border border-red-200"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Retry
                      </button>
                    )}

                    {item.status === 'READY_FOR_REVIEW' && (
                      <button
                        onClick={(e) => handleQuickAction(e, item)}
                        disabled={isItemMutating}
                        title="Complete Work Item"
                        className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 hover:bg-emerald-100 disabled:opacity-50 transition border border-emerald-200"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        Complete
                      </button>
                    )}

                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
