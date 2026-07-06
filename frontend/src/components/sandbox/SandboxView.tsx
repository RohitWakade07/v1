import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FileViewer } from './FileViewer';
import { Terminal } from './Terminal';
import { Loader2, X } from 'lucide-react';

interface SandboxViewProps {
  submissionId: string;
  onClose: () => void;
}

export const SandboxView: React.FC<SandboxViewProps> = ({ submissionId, onClose }) => {
  const [sandboxId, setSandboxId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let activeSandboxId: string | null = null;
    let isSubscribed = true;

    const startSandbox = async () => {
      try {
        const res = await axios.post(`/api/v1/sandbox/start/${submissionId}`);
        if (isSubscribed) {
          setSandboxId(res.data.sandbox_id);
          activeSandboxId = res.data.sandbox_id;
          setLoading(false);
        }
      } catch (e: any) {
        if (isSubscribed) {
          setError(e?.response?.data?.detail || "Failed to start sandbox");
          setLoading(false);
        }
      }
    };

    startSandbox();

    return () => {
      isSubscribed = false;
      if (activeSandboxId) {
        axios.post(`/api/v1/sandbox/stop/${activeSandboxId}`).catch(console.error);
      }
    };
  }, [submissionId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 bg-navy-900 rounded-lg border border-navy-800">
        <Loader2 className="animate-spin text-accent-blue mb-4" size={32} />
        <p className="text-text-secondary">Provisioning interactive sandbox...</p>
      </div>
    );
  }

  if (error || !sandboxId) {
    return (
      <div className="p-6 bg-status-danger/10 border border-status-danger/20 rounded-lg">
        <h3 className="text-status-danger font-semibold mb-2">Sandbox Error</h3>
        <p className="text-sm text-text-secondary">{error}</p>
        <button onClick={onClose} className="mt-4 px-4 py-2 bg-navy-800 rounded-lg text-sm hover:bg-navy-700 text-text-primary">
          Close Sandbox
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[600px] border border-navy-700 rounded-xl overflow-hidden bg-navy-900 shadow-2xl">
      {/* Header */}
      <div className="flex justify-between items-center px-4 py-3 bg-navy-800 border-b border-navy-700">
        <h3 className="font-semibold text-text-primary flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-status-success animate-pulse"></span>
          Interactive Grading Sandbox
        </h3>
        <button onClick={onClose} className="text-text-secondary hover:text-text-primary p-1 rounded-md hover:bg-navy-700">
          <X size={18} />
        </button>
      </div>

      {/* Main Content Split View */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left pane: File Viewer */}
        <div className="w-1/2 h-full p-2">
          <FileViewer sandboxId={sandboxId} />
        </div>
        
        {/* Right pane: Terminal */}
        <div className="w-1/2 h-full p-2 pl-0">
          <Terminal sandboxId={sandboxId} />
        </div>
      </div>
    </div>
  );
};
