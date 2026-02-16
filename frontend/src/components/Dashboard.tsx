import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Send, Loader2, User, Code, AlertCircle, UserCircle, FileText, BarChart3, LogOut, Download, FileJson } from 'lucide-react';
import { API_ENDPOINTS, DEFAULT_TENANT_ID } from '../config';
import { getAuthHeaders, logout as authLogout } from '../utils/auth';
import LogsViewer from './LogsViewer';
import { exportResults } from '../utils/export';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sql?: string;
  explanation?: string;
  data?: any[];
  rowCount?: number;
  error?: string;
  executionError?: string;
}

interface DashboardProps {
  onLogout?: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ onLogout }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showProfileMenu, setShowProfileMenu] = useState<boolean>(false);
  const [showLogs, setShowLogs] = useState<boolean>(false);
  const [exportingFormat, setExportingFormat] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Validate tenant ID is set
    if (!DEFAULT_TENANT_ID) {
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Error: Tenant ID is not configured. Please set VITE_DEFAULT_TENANT_ID in your .env file.',
        timestamp: new Date().toISOString(),
        error: 'Missing tenant ID configuration',
      };
      setMessages(prev => [...prev, errorResponse]);
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch(API_ENDPOINTS.ask, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'X-Tenant-ID': DEFAULT_TENANT_ID,
        },
        body: JSON.stringify({
          query: userMessage.content,
          tenant_id: DEFAULT_TENANT_ID,
          execute: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Determine response type: SQL mode (has row_count) vs chat/clarification mode
      const isSqlMode = data.row_count !== null && data.row_count !== undefined;
      const hasSql = data.sql && data.sql.trim() !== '';

      // Build appropriate message content based on response type
      let messageContent: string;
      if (data.execution_error) {
        messageContent = `I generated the SQL query, but there was an error executing it: ${data.execution_error}`;
      } else if (isSqlMode) {
        // SQL mode response
        if (data.row_count === 0) {
          messageContent = 'The query executed successfully but returned no results.';
        } else {
          messageContent = `I found ${data.row_count} result${data.row_count === 1 ? '' : 's'}.`;
        }
      } else {
        // Chat or clarification mode - use explanation or a default message
        messageContent = data.explanation || 'I received your message.';
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: messageContent,
        timestamp: new Date().toISOString(),
        sql: hasSql ? data.sql : undefined,
        explanation: data.explanation,
        data: data.rows || [],
        rowCount: data.row_count ?? 0,
        error: data.execution_error,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I encountered an error: ${errorMessage}`,
        timestamp: new Date().toISOString(),
        error: errorMessage,
      };
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const formatDataTable = (data: any[]) => {
    if (data.length === 0) return null;

    const columns = Object.keys(data[0]);
    return (
      <div className="overflow-x-auto mt-3">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-slate-700">
              {columns.map((col) => (
                <th key={col} className="text-left py-2 px-3 text-slate-400 font-semibold">
                  {col.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 10).map((row, idx) => (
              <tr key={idx} className="border-b border-slate-800 hover:bg-slate-800/50">
                {columns.map((col) => (
                  <td key={col} className="py-2 px-3 text-slate-300">
                    {row[col] === null || row[col] === undefined ? (
                      <span className="text-slate-500">—</span>
                    ) : typeof row[col] === 'object' ? (
                      <pre className="text-xs">{JSON.stringify(row[col], null, 2)}</pre>
                    ) : (
                      String(row[col])
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {data.length > 10 && (
          <p className="text-xs text-slate-500 mt-2 px-3">
            Showing 10 of {data.length} results
          </p>
        )}
      </div>
    );
  };

  const handleExport = async (format: 'csv' | 'pdf' | 'both') => {
    const lastMessage = messages[messages.length - 1];
    
    if (!lastMessage || lastMessage.role !== 'assistant' || !lastMessage.data || lastMessage.data.length === 0) {
      alert('No data to export. Please run a query first.');
      return;
    }

    setExportingFormat(format);
    
    try {
      console.log(`Starting export | format=${format} | rows=${lastMessage.data.length}`);
      
      const result = await exportResults(
        lastMessage.data,
        lastMessage.id,
        format
      );
      
      console.log('Export result:', result);
      
      // Download files with proper blob handling
      if (result.csv) {
        const { downloadFile } = await import('../utils/export');
        await downloadFile(result.csv, `query_${lastMessage.id}.csv`);
        console.log('CSV downloaded successfully');
      }
      
      if (result.pdf) {
        const { downloadFile } = await import('../utils/export');
        await downloadFile(result.pdf, `query_${lastMessage.id}.pdf`);
        console.log('PDF downloaded successfully');
      }
      
    } catch (error) {
      console.error('Export error:', error);
      alert(`Export failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setExportingFormat(null);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#0f0f23] text-white">
      {/* Top Bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-[#0f0f23]">
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-semibold text-white">Invisitag Support</h1>
        </div>
        <div className="relative flex items-center gap-2">
          <Link
            to="/admin"
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-800 transition-colors"
            title="View Admin Dashboard"
          >
            <BarChart3 className="w-5 h-5 text-slate-400" />
            <span className="text-sm text-slate-300">Admin</span>
          </Link>
          <button
            onClick={() => setShowLogs(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-800 transition-colors"
            title="View Application Logs"
          >
            <FileText className="w-5 h-5 text-slate-400" />
            <span className="text-sm text-slate-300">Logs</span>
          </button>
          <button
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <UserCircle className="w-5 h-5 text-slate-400" />
            <span className="text-sm text-slate-300">Profile</span>
          </button>
          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-lg py-1 z-10">
              <button className="w-full text-left px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 flex items-center gap-2">
                <UserCircle className="w-4 h-4" />
                Account Settings
              </button>
              <button
                onClick={async () => {
                  await authLogout();
                  if (onLogout) {
                    onLogout();
                  }
                }}
                className="w-full text-left px-4 py-2 text-sm text-red-300 hover:bg-slate-700 flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <h2 className="text-2xl font-semibold text-slate-300 mb-2">Welcome to Invisitag Support</h2>
              <p className="text-slate-500">Ask me anything about your database</p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
                  <span className="text-xs">AI</span>
                </div>
              )}

              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-200'
                }`}
              >
                {message.role === 'user' ? (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                ) : (
                  <div className="space-y-3">
                    <p className="whitespace-pre-wrap">{message.content}</p>

                    {message.error && (
                      <div className="flex items-start gap-2 p-2 bg-red-500/10 border border-red-500/20 rounded-lg">
                        <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-red-300">{message.error}</p>
                      </div>
                    )}

                    {message.sql && (
                      <details className="mt-3">
                        <summary className="cursor-pointer text-sm text-slate-400 hover:text-slate-300 flex items-center gap-2">
                          <Code className="w-4 h-4" />
                          Show SQL
                        </summary>
                        <div className="mt-2 p-3 bg-slate-900/50 rounded-lg border border-slate-700">
                          <pre className="text-xs text-green-400 font-mono overflow-x-auto">
                            {message.sql}
                          </pre>
                          {message.explanation && (
                            <p className="text-xs text-slate-400 mt-2">{message.explanation}</p>
                          )}
                        </div>
                      </details>
                    )}

                    {message.data && message.data.length > 0 && (
                      <div className="mt-3">
                        {formatDataTable(message.data)}
                      </div>
                    )}

                    {message.executionError && (
                      <div className="flex items-start gap-2 p-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                        <AlertCircle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-yellow-300">
                          Execution error: {message.executionError}
                        </p>
                      </div>
                    )}

                    {message.role === 'assistant' && message.data && message.data.length > 0 && (
                      <div className="flex gap-2 mt-3">
                        <button
                          onClick={() => handleExport('csv')}
                          disabled={exportingFormat !== null}
                          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 transition-colors text-sm"
                        >
                          <FileJson className="w-4 h-4" />
                          {exportingFormat === 'csv' ? 'Exporting...' : 'CSV'}
                        </button>
                        <button
                          onClick={() => handleExport('pdf')}
                          disabled={exportingFormat !== null}
                          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 disabled:bg-slate-700 transition-colors text-sm"
                        >
                          <FileText className="w-4 h-4" />
                          {exportingFormat === 'pdf' ? 'Exporting...' : 'PDF'}
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {message.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-4 justify-start">
              <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
                <span className="text-xs">AI</span>
              </div>
              <div className="bg-slate-800 rounded-2xl px-4 py-3">
                <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-800 bg-[#0f0f23] px-4 py-4">
        <div className="max-w-3xl mx-auto">
          <form onSubmit={handleSubmit} className="flex items-end gap-3">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  e.target.style.height = 'auto';
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
                }}
                onKeyDown={handleKeyPress}
                placeholder="Ask me anything about your database..."
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 pr-12 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none max-h-[200px]"
                rows={1}
              />
            </div>
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="flex items-center justify-center w-10 h-10 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed transition-colors flex-shrink-0"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </form>
          <p className="text-xs text-slate-500 mt-2 text-center">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>

      {/* Logs Viewer Modal */}
      {showLogs && <LogsViewer onClose={() => setShowLogs(false)} />}
      
    </div>
  );
};

export default Dashboard;
