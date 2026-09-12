import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusBadge } from '../StatusBadge';

describe('StatusBadge Component', () => {
  it('renders RECEIVED badge correctly', () => {
    render(<StatusBadge status="RECEIVED" />);
    expect(screen.getByText(/Received/i)).toBeInTheDocument();
  });

  it('renders ANALYSING badge with spinner', () => {
    render(<StatusBadge status="ANALYSING" />);
    expect(screen.getByText(/Analysing/i)).toBeInTheDocument();
  });

  it('renders READY_FOR_REVIEW badge', () => {
    render(<StatusBadge status="READY_FOR_REVIEW" />);
    expect(screen.getByText(/Ready for Review/i)).toBeInTheDocument();
  });

  it('renders COMPLETED badge', () => {
    render(<StatusBadge status="COMPLETED" />);
    expect(screen.getByText(/Completed/i)).toBeInTheDocument();
  });

  it('renders FAILED badge', () => {
    render(<StatusBadge status="FAILED" />);
    expect(screen.getByText(/Failed/i)).toBeInTheDocument();
  });
});
