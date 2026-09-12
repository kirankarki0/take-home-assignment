export type WorkItemStatus =
  | 'RECEIVED'
  | 'ANALYSING'
  | 'READY_FOR_REVIEW'
  | 'COMPLETED'
  | 'FAILED';

export type Category =
  | 'DOCUMENT_REQUEST'
  | 'IDENTITY_VERIFICATION'
  | 'INCOME_ASSESSMENT'
  | 'COMPLIANCE_REVIEW'
  | 'GENERAL_INQUIRY';

export type Priority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export interface AIAnalysisResult {
  category: Category;
  priority: Priority;
  summary: string;
  recommendedAction: string;
}

export interface WorkItem {
  id: string;
  externalId: string;
  title: string;
  description: string;
  status: WorkItemStatus;
  analysisResult: AIAnalysisResult | null;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CreateWorkItemPayload {
  externalId: string;
  title: string;
  description: string;
}

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, any>;
}

export interface CreateWorkItemResult {
  item: WorkItem;
  wasCreated: boolean;   // true → 201 (new), false → 200 (idempotent duplicate)
}
