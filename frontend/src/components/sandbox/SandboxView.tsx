import React, { useState, useEffect } from 'react';
import { apiClient } from '@/api/client';
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

  // Grading Panel state
  const [submission, setSubmission] = useState<any>(null);
  const [mentorScore, setMentorScore] = useState<string>('');
  const [mentorFeedback, setMentorFeedback] = useState<string>('');
  const [savingGrade, setSavingGrade] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    const fetchSubmission = async () => {
      try {
        const res = await apiClient.get(`/mentor/submissions/${submissionId}`);
        setSubmission(res.data);
        if (res.data.mentor_score !== null && res.data.mentor_score !== undefined) {
          setMentorScore(res.data.mentor_score.toString());
        }
        if (res.data.mentor_feedback) {
          setMentorFeedback(res.data.mentor_feedback);
        }
      } catch (err) {
        console.error("Failed to fetch submission details", err);
      }
    };
    fetchSubmission();
  }, [submissionId]);

  useEffect(() => {
    let activeSandboxId: string | null = null;
    let isSubscribed = true;

    const startSandbox = async () => {
      try {
        const res = await apiClient.post(`/sandbox/start/${submissionId}`);
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

    const stopSandboxCall = () => {
      if (activeSandboxId) {
        // Send a reliable beacon if supported or fallback to keepalive fetch
        const url = `${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/sandbox/stop/${activeSandboxId}`;
        const token = localStorage.getItem('sgp-auth') ? JSON.parse(localStorage.getItem('sgp-auth') as string)?.state?.token : null;
        if (token) {
          fetch(url, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            keepalive: true
          }).catch(console.error);
        }
      }
    };

    const handleBeforeUnload = () => {
      stopSandboxCall();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      isSubscribed = false;
      window.removeEventListener('beforeunload', handleBeforeUnload);
      stopSandboxCall();
    };
  }, [submissionId]);

  const handleSaveGrade = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!submission) return;
    setSavingGrade(true);
    setSaveSuccess(false);
    try {
      const scoreNum = mentorScore.trim() === '' ? null : parseFloat(mentorScore);
      const res = await apiClient.post(`/mentor/submissions/${submissionId}/grade`, {
        mentor_score: scoreNum,
        mentor_feedback: mentorFeedback
      });
      setSubmission(res.data);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "Failed to save grade");
    } finally {
      setSavingGrade(false);
    }
  };

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
    <div className="flex flex-col h-[720px] border border-navy-700 rounded-xl overflow-hidden bg-navy-900 shadow-2xl">
      {/* Header */}
      <div className="flex justify-between items-center px-4 py-3 bg-navy-800 border-b border-navy-700">
        <h3 className="font-semibold text-text-primary flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-status-success animate-pulse"></span>
          Interactive Grading Sandbox {submission && `— ${submission.student_name} (${submission.student_roll})`}
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

      {/* Grading Panel */}
      <div className="bg-navy-800 border-t border-navy-700 p-4">
        <form onSubmit={handleSaveGrade} className="flex flex-col md:flex-row gap-4 items-end">
          <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Grader Score */}
            <div className="bg-navy-900 border border-navy-700 rounded-lg p-3 flex flex-col justify-center">
              <span className="text-xs text-text-secondary uppercase tracking-wider font-semibold">Grader Score</span>
              <span className="text-lg font-mono font-bold text-text-primary mt-1">
                {submission && submission.score !== null ? (
                  `${submission.score.toFixed(1)} / ${submission.max_score}`
                ) : (
                  'No Score / Evaluator pending'
                )}
              </span>
            </div>

            {submission?.assignment_category === 'manual_review' && (
              <>
                {/* Mentor Score Input */}
                <div className="flex flex-col">
                  <label htmlFor="mentor_score" className="text-xs text-text-secondary uppercase tracking-wider font-semibold mb-1">
                    Mentor Score {submission && `(Max: ${submission.max_score})`}
                  </label>
                  <input
                    id="mentor_score"
                    type="number"
                    step="0.1"
                    min="0"
                    max={submission ? submission.max_score : 100}
                    placeholder="Enter custom score"
                    value={mentorScore}
                    onChange={(e) => setMentorScore(e.target.value)}
                    className="bg-navy-900 border border-navy-700 rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-accent-blue font-mono"
                  />
                </div>

                {/* Mentor Feedback Textarea */}
                <div className="flex flex-col">
                  <label htmlFor="mentor_feedback" className="text-xs text-text-secondary uppercase tracking-wider font-semibold mb-1">
                    Mentor Feedback / Notes
                  </label>
                  <textarea
                    id="mentor_feedback"
                    placeholder="Add comments or notes..."
                    value={mentorFeedback}
                    onChange={(e) => setMentorFeedback(e.target.value)}
                    rows={1}
                    className="bg-navy-900 border border-navy-700 rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-accent-blue text-sm resize-none"
                  />
                </div>
              </>
            )}
          </div>

          {/* Action Button */}
          {submission?.assignment_category === 'manual_review' && (
            <div className="flex items-center gap-3">
              {saveSuccess && (
                <span className="text-sm text-status-success font-medium animate-pulse">Grade saved successfully!</span>
              )}
              <button
                type="submit"
                disabled={savingGrade || !submission}
                className="px-6 py-2 bg-accent-teal hover:bg-accent-teal/80 disabled:bg-navy-800 disabled:text-text-secondary disabled:cursor-not-allowed rounded-lg font-semibold text-sm transition-colors text-white flex items-center gap-2 cursor-pointer"
              >
                {savingGrade && <Loader2 className="animate-spin" size={16} />}
                Save Grade
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};
