import React from 'react';
import type { WorkItem } from '../types/work-item';
import { StatusBadge } from './StatusBadge';
import {
  useTriggerAnalysis,
  useRetryAnalysis,
  useCompleteWorkItem,
} from '../api/workItems';
import {
  X,
  Play,
  RotateCcw,
  CheckCircle,
  FileText,
  Clock,
  Sparkles,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';

interface WorkItemDetailProps {
  item: WorkItem;
  onClose: () => void;
}

export const WorkItemDetail: React.FC<WorkItemDetailProps> = ({ item, onClose }) => {
  const triggerMutation = useTriggerAnalysis();
  const retryMutation = useRetryAnalysis();
  const completeMutation = useCompleteWorkItem();

  const isMutating =
    triggerMutation.isPending ||
    retryMutation.isPending ||
    completeMutation.isPending;

  const handleAnalyse = () => {
    triggerMutation.mutate(item.id);
  };

  const handleRetry = () => {
    retryMutation.mutate(item.id);
  };

  const handleComplete = () => {
    completeMutation.mutate(item.id);
  };

  const getPriorityBadgeColor = (priority: string) => {
    switch (priority) {
      case 'URGENT':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'HIGH':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Detail Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50/50">
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs font-bold text-gray-500 bg-gray-200/70 px-2 py-0.5 rounded">
            {item.externalId}
          </span>
          <StatusBadge status={item.status} />
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1 text-gray-400 hover:bg-gray-200/60 hover:text-gray-700 transition"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Content Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900">{item.title}</h2>
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              Received: {new Date(item.createdAt).toLocaleString()}
            </span>
            <span>•</span>
            <span>Updated: {new Date(item.updatedAt).toLocaleString()}</span>
          </div>
        </div>

        {/* Work Item Intake Description */}
        <div className="rounded-lg bg-gray-50 p-4 border border-gray-200/70">
          <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-gray-600 mb-2">
            <FileText className="w-4 h-4 text-gray-500" />
            Intake Description
          </div>
          <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
            {item.description}
          </p>
        </div>

        {/* AI Failure Banner if FAILED */}
        {item.status === 'FAILED' && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-4">
            <div className="flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-red-800">AI Analysis Failed</h4>
                <p className="mt-1 text-xs text-red-700">
                  {item.errorMessage || 'An error occurred during AI processing.'}
                </p>
                <div className="mt-3">
                  <button
                    onClick={handleRetry}
                    disabled={isMutating}
                    className="inline-flex items-center gap-1.5 rounded-md bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-700 disabled:opacity-50 transition shadow-sm"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    Retry Analysis
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* AI Analysis Result Card */}
        {item.analysisResult && (
          <div className="rounded-xl border border-indigo-100 bg-gradient-to-br from-indigo-50/40 via-white to-purple-50/30 p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-indigo-100/60 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                <h3 className="text-sm font-bold text-gray-900">AI Analysis Insight</h3>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold border ${getPriorityBadgeColor(
                    item.analysisResult.priority
                  )}`}
                >
                  {item.analysisResult.priority} PRIORITY
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800 border border-indigo-200">
                  {item.analysisResult.category.replace(/_/g, ' ')}
                </span>
              </div>
            </div>

            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Summary</span>
              <p className="mt-1 text-sm font-medium text-gray-800 bg-white/80 p-3 rounded-lg border border-gray-100">
                {item.analysisResult.summary}
              </p>
            </div>

            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Recommended Action</span>
              <div className="mt-1 flex items-start gap-2 bg-indigo-50/60 p-3 rounded-lg border border-indigo-100/80 text-sm text-indigo-950">
                <ArrowRight className="w-4 h-4 text-indigo-600 flex-shrink-0 mt-0.5" />
                <span className="font-semibold">{item.analysisResult.recommendedAction}</span>
              </div>
            </div>
          </div>
        )}

        {/* Analysing Progress Display */}
        {item.status === 'ANALYSING' && (
          <div className="flex flex-col items-center justify-center p-8 rounded-xl bg-amber-50/50 border border-amber-200/60 text-center">
            <div className="w-8 h-8 rounded-full border-2 border-amber-600 border-t-transparent animate-spin mb-3" />
            <h4 className="text-sm font-semibold text-amber-900">AI Analysis in Progress</h4>
            <p className="text-xs text-amber-700 mt-1 max-w-xs">
              Extracting key data points, determining category, priority, and recommended operational next steps...
            </p>
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="border-t border-gray-200 bg-gray-50 px-6 py-4 flex items-center justify-between">
        <div className="text-xs text-gray-500">
          ID: <span className="font-mono">{item.id}</span>
        </div>

        <div className="flex items-center gap-3">
          {item.status === 'RECEIVED' && (
            <button
              onClick={handleAnalyse}
              disabled={isMutating}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 transition shadow-sm"
            >
              <Play className="w-4 h-4" />
              {triggerMutation.isPending ? 'Starting...' : 'Trigger AI Analysis'}
            </button>
          )}

          {item.status === 'FAILED' && (
            <button
              onClick={handleRetry}
              disabled={isMutating}
              className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50 transition shadow-sm"
            >
              <RotateCcw className="w-4 h-4" />
              {retryMutation.isPending ? 'Retrying...' : 'Retry Failed Analysis'}
            </button>
          )}

          {item.status === 'READY_FOR_REVIEW' && (
            <button
              onClick={handleComplete}
              disabled={isMutating}
              className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50 transition shadow-sm"
            >
              <CheckCircle className="w-4 h-4" />
              {completeMutation.isPending ? 'Completing...' : 'Approve & Complete'}
            </button>
          )}

          {item.status === 'COMPLETED' && (
            <span className="inline-flex items-center gap-1 text-sm font-medium text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
              <CheckCircle className="w-4 h-4" /> Work Item Completed
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
