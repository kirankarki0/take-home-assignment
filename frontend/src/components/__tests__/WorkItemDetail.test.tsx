import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WorkItemDetail } from '../WorkItemDetail';
import type { WorkItem } from '../../types/work-item';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('WorkItemDetail Component', () => {
  const baseItem: WorkItem = {
    id: '123e4567-e89b-12d3-a456-426614174000',
    externalId: 'CRM-TEST-1',
    title: 'Test Work Item Title',
    description: 'Detailed description of test work item.',
    status: 'RECEIVED',
    analysisResult: null,
    errorMessage: null,
    createdAt: '2026-09-10T00:00:00Z',
    updatedAt: '2026-09-10T00:00:00Z',
  };

  it('renders title, external ID and Trigger AI Analysis button for RECEIVED status', () => {
    render(<WorkItemDetail item={baseItem} onClose={vi.fn()} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText('CRM-TEST-1')).toBeInTheDocument();
    expect(screen.getByText('Test Work Item Title')).toBeInTheDocument();
    expect(screen.getByText(/Trigger AI Analysis/i)).toBeInTheDocument();
  });

  it('renders failure banner and retry button when status is FAILED', () => {
    const failedItem: WorkItem = {
      ...baseItem,
      status: 'FAILED',
      errorMessage: 'LLM timed out after 10 seconds',
    };

    render(<WorkItemDetail item={failedItem} onClose={vi.fn()} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText('AI Analysis Failed')).toBeInTheDocument();
    expect(screen.getByText(/LLM timed out after 10 seconds/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Retry Failed Analysis/i })).toBeInTheDocument();
  });

  it('renders AI insights and complete button when status is READY_FOR_REVIEW', () => {
    const readyItem: WorkItem = {
      ...baseItem,
      status: 'READY_FOR_REVIEW',
      analysisResult: {
        category: 'DOCUMENT_REQUEST',
        priority: 'HIGH',
        summary: 'Applicant needs to provide latest payslip.',
        recommendedAction: 'Request payslip via email.',
      },
    };

    render(<WorkItemDetail item={readyItem} onClose={vi.fn()} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText(/AI Analysis Insight/i)).toBeInTheDocument();
    expect(screen.getByText(/HIGH PRIORITY/i)).toBeInTheDocument();
    expect(screen.getByText(/DOCUMENT REQUEST/i)).toBeInTheDocument();
    expect(screen.getByText('Applicant needs to provide latest payslip.')).toBeInTheDocument();
    expect(screen.getByText('Request payslip via email.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Approve & Complete/i })).toBeInTheDocument();
  });

  it('renders completed indicator when status is COMPLETED', () => {
    const completedItem: WorkItem = {
      ...baseItem,
      status: 'COMPLETED',
    };

    render(<WorkItemDetail item={completedItem} onClose={vi.fn()} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText('Work Item Completed')).toBeInTheDocument();
  });
});
