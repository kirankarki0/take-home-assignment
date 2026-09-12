import { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WorkItemList } from './components/WorkItemList';
import { WorkItemDetail } from './components/WorkItemDetail';
import { CreateWorkItemModal } from './components/CreateWorkItemModal';
import { useWorkItem } from './api/workItems';
import { Sparkles, Cpu } from 'lucide-react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30,
      retry: 1,
    },
  },
});

function OperationsDashboard() {
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const { data: selectedItem } = useWorkItem(selectedItemId || undefined);

  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 4000);
    return () => clearTimeout(timer);
  }, [toast]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">

      {toast && (
        <div
          role="status"
          className="fixed top-20 left-1/2 -translate-x-1/2 z-50 bg-slate-900 text-white text-sm px-4 py-2 rounded-lg shadow-lg animate-in fade-in slide-in-from-top-2"
        >
          {toast}
        </div>
      )}
      {/* Top Navigation */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-sm">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-base text-gray-900 tracking-tight flex items-center gap-2">
                Work Intake System
              </span>
            </div>
          </div>

        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col md:flex-row gap-6">
        {/* Left Column: Work Items List */}
        <div className="w-full md:w-1/2 lg:w-7/12 flex flex-col min-h-[500px]">
          <WorkItemList
            selectedItemId={selectedItemId}
            onSelectItem={(id) => setSelectedItemId(id)}
            onOpenCreate={() => setIsCreateOpen(true)}
          />
        </div>

        {/* Right Column: Work Item Detail View */}
        <div className="w-full md:w-1/2 lg:w-5/12 flex flex-col min-h-[500px]">
          {selectedItem ? (
            <WorkItemDetail
              item={selectedItem}
              onClose={() => setSelectedItemId(null)}
            />
          ) : (
            <div className="h-full bg-white rounded-xl border border-dashed border-gray-200 p-8 flex flex-col items-center justify-center text-center text-gray-400">
              <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-base font-semibold text-gray-800">Select a Work Item</h3>
              <p className="text-xs text-gray-500 mt-1 max-w-xs">
                Click any work item from the list to review its intake details, trigger or retry AI classification, and complete the review.
              </p>
            </div>
          )}
        </div>
      </main>

      {/* Intake Modal */}
      <CreateWorkItemModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSuccess={(newId) => {
          setSelectedItemId(newId);
        }}
        onDuplicate={() =>
          setToast('That work item already existed — showing the existing record.')
        }
      />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <OperationsDashboard />
    </QueryClientProvider>
  );
}
