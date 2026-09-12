import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { WorkItem, CreateWorkItemPayload, ApiError } from '../types/work-item';

const API_BASE = '/api';


async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorData: ApiError;
    try {
      errorData = await res.json();
    } catch {
      errorData = {
        error: 'HTTP_ERROR',
        message: `HTTP ${res.status}: ${res.statusText}`,
      };
    }
    throw errorData;
  }
  return res.json();
}

export async function fetchWorkItems(statusFilter?: string): Promise<WorkItem[]> {
  const url = statusFilter && statusFilter !== 'ALL'
    ? `${API_BASE}/work-items/?status=${encodeURIComponent(statusFilter)}`
    : `${API_BASE}/work-items/`;
  const res = await fetch(url);
  return handleResponse<WorkItem[]>(res);
}

export async function fetchWorkItem(id: string): Promise<WorkItem> {
  const res = await fetch(`${API_BASE}/work-items/${id}/`);
  return handleResponse<WorkItem>(res);
}

export async function createWorkItem(payload: CreateWorkItemPayload) : Promise<WorkItem> {
  const res = await fetch(`${API_BASE}/work-items/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse<WorkItem>(res);
}

export async function triggerAnalysis(id: string): Promise<WorkItem> {
  const res = await fetch(`${API_BASE}/work-items/${id}/analyse/`, {
    method: 'POST',
  });
  return handleResponse<WorkItem>(res);
}

export async function retryAnalysis(id: string): Promise<WorkItem> {
  const res = await fetch(`${API_BASE}/work-items/${id}/retry/`, {
    method: 'POST',
  });
  return handleResponse<WorkItem>(res);
}

export async function completeWorkItem(id: string): Promise<WorkItem> {
  const res = await fetch(`${API_BASE}/work-items/${id}/status/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'COMPLETED' }),
  });
  return handleResponse<WorkItem>(res);
}

// TanStack Query Hooks

export function useWorkItems(statusFilter?: string) {
  return useQuery<WorkItem[], ApiError>({
    queryKey: ['work-items', statusFilter],
    queryFn: () => fetchWorkItems(statusFilter),
    refetchInterval: 5000, // Background polling for live status
  });
}

export function useWorkItem(id?: string) {
  return useQuery<WorkItem, ApiError>({
    queryKey: ['work-item', id],
    queryFn: () => fetchWorkItem(id!),
    enabled: !!id,
  });
}

export function useCreateWorkItem() {
  const queryClient = useQueryClient();
  return useMutation<WorkItem, ApiError, CreateWorkItemPayload>({
    mutationFn: createWorkItem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['work-items'] });
    },
  });
}

export function useTriggerAnalysis() {
  const queryClient = useQueryClient();
  return useMutation<WorkItem, ApiError, string>({
    mutationFn: triggerAnalysis,
    onSuccess: (updatedItem) => {
      queryClient.invalidateQueries({ queryKey: ['work-items'] });
      queryClient.setQueryData(['work-item', updatedItem.id], updatedItem);
    },
  });
}

export function useRetryAnalysis() {
  const queryClient = useQueryClient();
  return useMutation<WorkItem, ApiError, string>({
    mutationFn: retryAnalysis,
    onSuccess: (updatedItem) => {
      queryClient.invalidateQueries({ queryKey: ['work-items'] });
      queryClient.setQueryData(['work-item', updatedItem.id], updatedItem);
    },
  });
}

export function useCompleteWorkItem() {
  const queryClient = useQueryClient();
  return useMutation<WorkItem, ApiError, string>({
    mutationFn: completeWorkItem,
    onSuccess: (updatedItem) => {
      queryClient.invalidateQueries({ queryKey: ['work-items'] });
      queryClient.setQueryData(['work-item', updatedItem.id], updatedItem);
    },
  });
}
