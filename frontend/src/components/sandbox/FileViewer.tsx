import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface FileViewerProps {
  sandboxId: string;
}

export const FileViewer: React.FC<FileViewerProps> = ({ sandboxId }) => {
  const [files, setFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Fetch file list
    const fetchFiles = async () => {
      try {
        const res = await axios.get(`/api/v1/sandbox/files/${sandboxId}`);
        setFiles(res.data.files || []);
      } catch (e) {
        console.error("Failed to load files", e);
      }
    };
    fetchFiles();
  }, [sandboxId]);

  const loadFile = async (path: string) => {
    setSelectedFile(path);
    setLoading(true);
    try {
      const res = await axios.get(`/api/v1/sandbox/file/${sandboxId}`, {
        params: { path }
      });
      setFileContent(res.data.content || '');
    } catch (e) {
      setFileContent('Error loading file content.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full border border-navy-700 rounded-lg overflow-hidden bg-navy-900">
      <div className="w-1/3 border-r border-navy-700 overflow-y-auto p-2">
        <h3 className="text-xs font-bold text-text-secondary uppercase tracking-wider mb-2 px-2">Files</h3>
        <ul className="space-y-1">
          {files.map(f => (
            <li key={f}>
              <button
                onClick={() => loadFile(f)}
                className={`w-full text-left px-2 py-1 text-sm rounded ${selectedFile === f ? 'bg-accent-blue/20 text-accent-blue' : 'text-text-primary hover:bg-navy-800'}`}
              >
                {f}
              </button>
            </li>
          ))}
          {files.length === 0 && (
            <li className="px-2 py-1 text-sm text-text-secondary">No files found</li>
          )}
        </ul>
      </div>
      <div className="w-2/3 flex flex-col bg-[#1e1e1e]">
        {selectedFile ? (
          <>
            <div className="bg-navy-800 text-text-secondary text-xs px-4 py-2 border-b border-navy-700 font-mono">
              {selectedFile}
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {loading ? (
                <div className="text-text-secondary text-sm">Loading...</div>
              ) : (
                <pre className="text-sm font-mono text-[#d4d4d4] whitespace-pre-wrap">
                  {fileContent}
                </pre>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-text-secondary text-sm">
            Select a file to view
          </div>
        )}
      </div>
    </div>
  );
};
