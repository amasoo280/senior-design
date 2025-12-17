import React, { useState, useEffect, useRef } from 'react';
import { X, RefreshCw, Filter, Download } from 'lucide-react';
import { API_ENDPOINTS } from '../config';
import { getAuthHeaders } from '../utils/auth';

interface LogEntry {
  timestamp: string;
  level: string;
  module: string;
  request_id: string;
  tenant_id: string;
  message: string;
  exception?: string;
}

interface LogsViewerProps {
  onClose: () => void;
}

const LogsViewer: React.FC<LogsViewerProps> = ({ onClose }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [filterLevel, setFilterLevel] = useState<string>('ALL');
  const [autoRefresh, setAutoRefresh] = useState<boolean>(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const fetchLogs = async () => {
    try {
      setIsLoading(true);
      const params = new URLSearchParams();
      params.append('limit', '200');
      if (filterLevel !== 'ALL') {
        params.append('level', filterLevel);
      }

      const response = await fetch(`${API_ENDPOINTS.logs}?${params.toString()}`, {
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error('Failed to fetch logs');
      }

      const data = await response.json();
      setLogs(data.logs || []);
    } catch (error) {
      console.error('Error fetching logs:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [filterLevel]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchLogs, 2000); // Refresh every 2 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh, filterLevel]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'text-red-400 bg-red-500/10 border-red-500/20';
      case 'WARNING':
        return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
      case 'INFO':
        return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
      case 'DEBUG':
        return 'text-gray-400 bg-gray-500/10 border-gray-500/20';
      default:
        return 'text-slate-400 bg-slate-500/10 border-slate-500/20';
    }
  };

  const exportLogs = () => {
    const logText = logs
      .map(log => `[${log.timestamp}] ${log.level} | ${log.module} | request_id=${log.request_id} | tenant_id=${log.tenant_id} | ${log.message}`)
      .join('\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs-${new Date().toISOString()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-[#0f0f23] border border-slate-700 rounded-xl w-full max-w-6xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <h2 className="text-xl font-semibold text-white">Application Logs</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                autoRefresh
                  ? 'bg-green-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              <RefreshCw className={`w-4 h-4 inline mr-1 ${autoRefresh ? 'animate-spin' : ''}`} />
              Auto-refresh
            </button>
            <button
              onClick={fetchLogs}
              disabled={isLoading}
              className="px-3 py-1.5 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 inline mr-1 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={exportLogs}
              className="px-3 py-1.5 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
            >
              <Download className="w-4 h-4 inline mr-1" />
              Export
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="p-4 border-b border-slate-700 flex items-center gap-4">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-sm text-slate-400">Filter by level:</span>
          <div className="flex gap-2">
            {['ALL', 'DEBUG', 'INFO', 'WARNING', 'ERROR'].map((level) => (
              <button
                key={level}
                onClick={() => setFilterLevel(level)}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  filterLevel === level
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {level}
              </button>
            ))}
          </div>
          <span className="text-sm text-slate-500 ml-auto">
            {logs.length} log{logs.length !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Logs Container */}
        <div className="flex-1 overflow-y-auto p-4 font-mono text-xs">
          {isLoading && logs.length === 0 ? (
            <div className="text-center text-slate-500 py-8">Loading logs...</div>
          ) : logs.length === 0 ? (
            <div className="text-center text-slate-500 py-8">No logs found</div>
          ) : (
            <div className="space-y-2">
              {logs.map((log, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg border ${getLevelColor(log.level)}`}
                >
                  <div className="flex items-start gap-2 flex-wrap">
                    <span className="font-semibold min-w-[60px]">{log.level}</span>
                    <span className="text-slate-400">{log.timestamp}</span>
                    <span className="text-slate-500">|</span>
                    <span className="text-slate-400">{log.module}</span>
                    <span className="text-slate-500">|</span>
                    <span className="text-slate-400">request_id={log.request_id}</span>
                    <span className="text-slate-500">|</span>
                    <span className="text-slate-400">tenant_id={log.tenant_id}</span>
                  </div>
                  <div className="mt-2 text-slate-200 break-words">{log.message}</div>
                  {log.exception && (
                    <div className="mt-2 p-2 bg-red-900/20 rounded text-red-300 text-xs whitespace-pre-wrap">
                      {log.exception}
                    </div>
                  )}
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LogsViewer;


