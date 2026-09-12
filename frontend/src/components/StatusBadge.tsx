import React from 'react';
import type { WorkItemStatus } from '../types/work-item';
import { Clock, Loader2, CheckCircle2, CheckCheck, AlertCircle } from 'lucide-react';

interface StatusBadgeProps {
  status: WorkItemStatus;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  switch (status) {
    case 'RECEIVED':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 ${className}`}>
          <Clock className="w-3.5 h-3.5 text-blue-600" />
          Received
        </span>
      );
    case 'ANALYSING':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200 ${className}`}>
          <Loader2 className="w-3.5 h-3.5 text-amber-600 animate-spin" />
          Analysing
        </span>
      );
    case 'READY_FOR_REVIEW':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200 ${className}`}>
          <CheckCircle2 className="w-3.5 h-3.5 text-purple-600" />
          Ready for Review
        </span>
      );
    case 'COMPLETED':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 ${className}`}>
          <CheckCheck className="w-3.5 h-3.5 text-emerald-600" />
          Completed
        </span>
      );
    case 'FAILED':
      return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200 ${className}`}>
          <AlertCircle className="w-3.5 h-3.5 text-red-600" />
          Failed
        </span>
      );
    default:
      return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 ${className}`}>
          {status}
        </span>
      );
  }
};
