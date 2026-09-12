import React, { useState } from 'react';
import { useCreateWorkItem } from '../api/workItems';
import { X, Sparkles, AlertCircle } from 'lucide-react';

interface CreateWorkItemModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (id: string) => void;
  onDuplicate?: () => void;
}

export const CreateWorkItemModal: React.FC<CreateWorkItemModalProps> = ({ isOpen, onClose, onSuccess, onDuplicate }) => {
  const [externalId, setExternalId] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [errorBanner, setErrorBanner] = useState<string | null>(null);

  const createMutation = useCreateWorkItem();

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorBanner(null);

    if (!externalId.trim() || !title.trim() || !description.trim()) {
      setErrorBanner('All fields are required.');
      return;
    }

    try {
      const { item, wasCreated } = await createMutation.mutateAsync({
        externalId: externalId.trim(),
        title: title.trim(),
        description: description.trim(),
      });
      onSuccess(item.id);
      onClose();
      if (!wasCreated) {
        onDuplicate?.();
      }
    }  catch (err: unknown) {
        const message =
        err && typeof err === 'object' && 'message' in err
          ? String((err as { message: unknown }).message)
          : 'Failed to ingest work item.';
      setErrorBanner(message);
    }
  };

  const handlePreFill = (preset: 'income' | 'identity' | 'timeout') => {
    if (preset === 'income') {
      const id = `CRM-${Math.floor(1000 + Math.random() * 9000)}`;
      setExternalId(id);
      setTitle('Missing income document');
      setDescription('The applicant submitted their application but has not provided their latest payslip.');
    } else if (preset === 'identity') {
      const id = `CRM-${Math.floor(1000 + Math.random() * 9000)}`;
      setExternalId(id);
      setTitle('Passport photo verification required');
      setDescription('Uploaded identification image has high glare and is blurry. Needs manual review or re-upload.');
    } else if (preset === 'timeout') {
      const id = `CRM-${Math.floor(1000 + Math.random() * 9000)}`;
      setExternalId(id);
      setTitle('Complex assessment [SIMULATE_TIMEOUT]');
      setDescription('Simulated slow upstream processing to test failure resilience and retry flow.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-xl bg-white shadow-2xl overflow-hidden border border-gray-100 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">Ingest New Work Item</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errorBanner && (
            <div className="flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorBanner}</span>
            </div>
          )}

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-gray-600">
                Quick Sample Presets
              </label>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => handlePreFill('income')}
                className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 hover:bg-blue-100 transition"
              >
                <Sparkles className="w-3 h-3" /> Income Doc
              </button>
              <button
                type="button"
                onClick={() => handlePreFill('identity')}
                className="inline-flex items-center gap-1 rounded-md bg-purple-50 px-2.5 py-1 text-xs font-medium text-purple-700 hover:bg-purple-100 transition"
              >
                <Sparkles className="w-3 h-3" /> Identity Check
              </button>
              <button
                type="button"
                onClick={() => handlePreFill('timeout')}
                className="inline-flex items-center gap-1 rounded-md bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700 hover:bg-amber-100 transition"
              >
                <Sparkles className="w-3 h-3" /> Simulate Timeout
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              External ID (Idempotency Key)
            </label>
            <input
              type="text"
              required
              value={externalId}
              onChange={(e) => setExternalId(e.target.value)}
              placeholder="e.g. CRM-12345"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Submitting an existing external ID will return the existing record idempotently.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Missing income document"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              required
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Detailed description from external business system..."
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition shadow-sm"
            >
              {createMutation.isPending ? 'Ingesting...' : 'Ingest Item'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
