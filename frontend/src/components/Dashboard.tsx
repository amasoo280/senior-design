import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import {
  Send, Loader2, User, Code, AlertCircle, UserCircle,
  FileText, BarChart3, LogOut, CheckCircle, AlertTriangle, XCircle, Download, Shield
} from 'lucide-react';
import { API_ENDPOINTS, DEFAULT_TENANT_ID, SHOW_SQL_UI } from '../config';
import { getAuthHeadersWithToken } from '../utils/auth';
import LogsViewer from './LogsViewer';
import AnalyticsDashboard from './AnalyticsDashboard';
import AdminDashboard from './AdminDashboard';

interface StreamEvent {
  type: string;
  data: any;
}

interface ValidationInfo {
  status: 'valid' | 'partial' | 'mismatch' | 'skipped' | 'pending' | 'unknown';
  reasoning: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sql?: string;
  explanation?: string;
  data?: any[];
  columns?: string[];
  rowCount?: number;
  error?: string;
  executionError?: string;
  isStreaming?: boolean;
  thinkingSteps?: string[];
  validation?: ValidationInfo;
  /** True when low data validation caused rows to be withheld from the client */
  dataWithheld?: boolean;
  clarificationMessage?: string;
}

interface DashboardProps {
  getAccessToken: () => Promise<string>;
  user?: any;
  onLogout?: () => void;
  onOpenAdmin?: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ getAccessToken, user, onLogout, onOpenAdmin }) => {
  const { logout: auth0Logout } = useAuth0();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showProfileMenu, setShowProfileMenu] = useState<boolean>(false);
  const [showLogs, setShowLogs] = useState<boolean>(false);
  const [showAnalytics, setShowAnalytics] = useState<boolean>(false);
  const [sampleQuestions, setSampleQuestions] = useState<string[]>([
    'Show me all equipment',
    'How many assets are at each location?',
    'List employees and their devices',
    'Show recent equipment movements',
  ]);
  // Check admin status from backend /auth/me endpoint
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  const [historyLoaded, setHistoryLoaded] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch admin status from /auth/me on mount
  useEffect(() => {
    (async () => {
      try {
        const accessToken = await getAccessToken();
        const res = await fetch(API_ENDPOINTS.me, {
          headers: getAuthHeadersWithToken(accessToken),
        });
        if (res.ok) {
          const data = await res.json();
          setIsAdmin(data.user?.is_admin === true);
        }
      } catch {
        // If /auth/me fails, user is not admin
        setIsAdmin(false);
      }
    })();
  }, [getAccessToken]);

  const handleLogout = async () => {
    auth0Logout({ logoutParams: { returnTo: window.location.origin } });
    if (onLogout) onLogout();
  };

  // Load sample questions from admin config on first mount.
  useEffect(() => {
    (async () => {
      try {
        const accessToken = await getAccessToken();
        const res = await fetch(API_ENDPOINTS.adminConfigPrompt, {
          headers: getAuthHeadersWithToken(accessToken),
        });
        if (!res.ok) return;
        const data = await res.json();
        if (Array.isArray(data.sample_questions) && data.sample_questions.length > 0) {
          setSampleQuestions(data.sample_questions);
        }
      } catch {
        // Silently ignore; fallback defaults are fine.
      }
    })();
  }, [getAccessToken]);

  // Load conversation history on mount
  useEffect(() => {
    (async () => {
      try {
        const accessToken = await getAccessToken();
        const tokenTenantId = user?.['https://api.sargon.com/tenant_id'];
        const activeTenantId = tokenTenantId || DEFAULT_TENANT_ID || '';
        if (!activeTenantId) return;

        const res = await fetch(
          `${API_ENDPOINTS.history}?tenant_id=${encodeURIComponent(activeTenantId)}&limit=50`,
          { headers: getAuthHeadersWithToken(accessToken) }
        );
        if (!res.ok) return;
        const data = await res.json();

        if (Array.isArray(data.conversations) && data.conversations.length > 0) {
          const historical: Message[] = [];
          for (const conv of data.conversations) {
            // User message
            historical.push({
              id: `hist-user-${conv.id}`,
              role: 'user',
              content: conv.query,
              timestamp: conv.created_at,
            });
            // Assistant message
            historical.push({
              id: `hist-asst-${conv.id}`,
              role: 'assistant',
              content: conv.response || '',
              timestamp: conv.created_at,
              sql: conv.sql_generated || undefined,
              rowCount: conv.row_count ?? 0,
            });
          }
          setMessages(historical);
        }
      } catch {
        // History load failure is non-fatal — start with empty chat
      } finally {
        setHistoryLoaded(true);
      }
    })();
  }, [getAccessToken, user]);

  // Save a completed conversation to the backend
  const saveConversation = useCallback(async (
    query: string,
    assistantMsg: Message,
    tenantId: string,
  ) => {
    try {
      const accessToken = await getAccessToken();
      await fetch(API_ENDPOINTS.history, {
        method: 'POST',
        headers: getAuthHeadersWithToken(accessToken),
        body: JSON.stringify({
          tenant_id: tenantId,
          query,
          mode: assistantMsg.sql ? 'sql' : 'chat',
          response: assistantMsg.content,
          sql_generated: assistantMsg.sql ?? null,
          row_count: assistantMsg.rowCount ?? 0,
        }),
      });
    } catch {
      // Save failure is silent — chat still works
    }
  }, [getAccessToken]);

  /**
   * Handle streaming SSE response from /ask/stream endpoint.
   * Data is rendered progressively as it arrives.
   */
  const handleStreamingSubmit = useCallback(async (query: string, tenantId: string) => {
    const assistantMsgId = (Date.now() + 1).toString();

    // Create initial assistant message in streaming state
    const streamingMsg: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true,
      thinkingSteps: [],
      data: [],
      columns: [],
    };
    setMessages(prev => [...prev, streamingMsg]);

    try {
      const accessToken = await getAccessToken();

      // Get tenant ID from custom Auth0 claim, fallback to env default
      const tokenTenantId = user?.['https://api.sargon.com/tenant_id'];
      const activeTenantId = tokenTenantId || DEFAULT_TENANT_ID || '';
      console.log("Extracted Auth0 Tenant ID:", tokenTenantId);
      console.log("Using Active Tenant ID:", activeTenantId);

      const response = await fetch(API_ENDPOINTS.askStream, {
        method: 'POST',
        headers: {
          ...getAuthHeadersWithToken(accessToken),
          'X-Tenant-ID': activeTenantId,
        },
        body: JSON.stringify({
          query: query,
          tenant_id: activeTenantId,
          execute: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No readable stream');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const events = buffer.split('\n\n');
        buffer = events.pop() || ''; // Keep incomplete event in buffer

        for (const eventStr of events) {
          if (!eventStr.trim()) continue;

          const lines = eventStr.split('\n');
          let eventType = '';
          let eventData = '';

          for (const line of lines) {
            if (line.startsWith('event: ')) {
              eventType = line.slice(7);
            } else if (line.startsWith('data: ')) {
              eventData = line.slice(6);
            }
          }

          if (!eventType || !eventData) continue;

          try {
            const data = JSON.parse(eventData);

            setMessages(prev => prev.map(msg => {
              if (msg.id !== assistantMsgId) return msg;

              const updated = { ...msg };

              switch (eventType) {
                case 'thinking':
                  // Server sends a full sanitized snapshot each time (model reasoning is
                  // accumulated server-side so UUIDs/SQL are not split across chunks).
                  updated.thinkingSteps = [data.message];
                  updated.content = data.message;
                  break;

                case 'sql':
                  updated.sql = data.sql;
                  updated.explanation = data.explanation;
                  break;

                case 'columns':
                  updated.columns = data.columns;
                  break;

                case 'data_row':
                  updated.data = [...(updated.data || []), data.row];
                  updated.rowCount = (updated.data?.length || 0);
                  break;

                case 'validation':
                  updated.validation = {
                    status: data.status,
                    reasoning: data.reasoning,
                  };
                  break;

                case 'done':
                  updated.isStreaming = false;
                  updated.dataWithheld = data.data_withheld === true;
                  updated.clarificationMessage = data.clarification_message ?? undefined;
                  if (updated.dataWithheld && updated.clarificationMessage) {
                    updated.data = [];
                    updated.columns = [];
                    updated.rowCount = 0;
                    updated.content = updated.clarificationMessage;
                    break;
                  }
                  updated.rowCount = data.row_count ?? updated.data?.length ?? 0;
                  if (data.mode !== 'sql' && data.message) {
                    updated.content = data.message;
                  } else if (updated.rowCount > 0) {
                    updated.content = `Found ${updated.rowCount} result${updated.rowCount === 1 ? '' : 's'}.`;
                  } else if (updated.rowCount === 0 && data.mode === 'sql') {
                    updated.content = 'The query executed successfully but returned no results.';
                  }
                  break;

                case 'error':
                  updated.isStreaming = false;
                  updated.error = data.message;
                  updated.content = `Error: ${data.message}`;
                  break;
              }

              return updated;
            }));
          } catch (parseErr) {
            console.error('Failed to parse SSE event:', parseErr);
          }
        }
      }
      // Save completed conversation to backend
      setMessages(prev => {
        const finalMsg = prev.find(m => m.id === assistantMsgId);
        if (finalMsg && !finalMsg.error && tenantId) {
          saveConversation(query, finalMsg, tenantId);
        }
        return prev;
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
      setMessages(prev => prev.map(msg =>
        msg.id === assistantMsgId
          ? { ...msg, isStreaming: false, error: errorMessage, content: `Error: ${errorMessage}` }
          : msg
      ));
    }
  }, [getAccessToken, saveConversation]);

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
    const query = input.trim();
    setInput('');
    setIsLoading(true);

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

    // Use streaming endpoint
    const tokenTenantId = user?.['https://api.sargon.com/tenant_id'];
    const activeTenantId = tokenTenantId || DEFAULT_TENANT_ID || '';
    await handleStreamingSubmit(query, activeTenantId);
    setIsLoading(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const exportCSV = (data: any[], filename: string = 'query_results') => {
    if (!data || data.length === 0) return;
    const columns = Object.keys(data[0]);
    const csvRows = [
      columns.join(','),
      ...data.map(row =>
        columns.map(col => {
          const val = row[col];
          if (val === null || val === undefined) return '';
          const str = String(val);
          return str.includes(',') || str.includes('"') || str.includes('\n')
            ? `"${str.replace(/"/g, '""')}"`
            : str;
        }).join(',')
      ),
    ];
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const renderValidationBadge = (validation?: ValidationInfo, hideReasoning?: boolean) => {
    if (!validation || validation.status === 'pending') return null;

    const statusConfig = {
      valid: { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20', label: 'Validated' },
      partial: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20', label: 'Partial Match' },
      mismatch: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20', label: 'Mismatch' },
      skipped: { icon: AlertCircle, color: 'text-slate-400', bg: 'bg-slate-500/10 border-slate-500/20', label: 'Skipped' },
      unknown: { icon: AlertCircle, color: 'text-slate-400', bg: 'bg-slate-500/10 border-slate-500/20', label: 'Unknown' },
      pending: { icon: AlertCircle, color: 'text-slate-400', bg: 'bg-slate-500/10 border-slate-500/20', label: 'Pending' },
    };

    const config = statusConfig[validation.status] ?? statusConfig.skipped;
    const Icon = config.icon;

    return (
      <details className="mt-3">
        <summary className={`cursor-pointer text-sm flex items-center gap-2 p-2 rounded-lg border ${config.bg}`}>
          <Icon className={`w-4 h-4 ${config.color}`} />
          <span className={config.color}>Data Validation: {config.label}</span>
        </summary>
        {validation.reasoning && !hideReasoning && (
          <p className="text-xs text-slate-400 mt-2 px-2">{validation.reasoning}</p>
        )}
      </details>
    );
  };

  const formatDataTable = (data: any[], isStreaming?: boolean) => {
    if (!data || data.length === 0) return null;

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
            {data.map((row, idx) => (
              <tr
                key={idx}
                className={`border-b border-slate-800 hover:bg-slate-800/50 ${isStreaming && idx === data.length - 1 ? 'animate-pulse' : ''
                  }`}
              >
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
        {data.length > 0 && (
          <p className="text-xs text-slate-500 mt-2 px-3">
            {isStreaming ? `${data.length} rows loaded...` : `${data.length} total results`}
          </p>
        )}
      </div>
    );
  };

  const renderThinkingSteps = (steps?: string[]) => {
    if (!steps || steps.length === 0) return null;
    // Join all thinking chunks into a single continuous paragraph so it
    // feels like a normal LLM streaming response instead of bullet points.
    const fullThought = steps.join('');
    return (
      <div className="mb-1">
        <p className="whitespace-pre-wrap text-xs text-slate-500/90 italic">
          {fullThought}
        </p>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-[#0f0f23] text-white">
      {/* Top Bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-[#0f0f23]">
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-semibold text-white">Invisitag Support</h1>
        </div>
        <div className="relative flex items-center gap-2">
          <button
            onClick={() => setShowAnalytics(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-800 transition-colors"
            title="View Analytics Dashboard"
          >
            <BarChart3 className="w-5 h-5 text-slate-400" />
            <span className="text-sm text-slate-300">Analytics</span>
          </button>
          {isAdmin && (
            <button
              onClick={() => setShowLogs(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-800 transition-colors"
              title="View Application Logs"
            >
              <FileText className="w-5 h-5 text-slate-400" />
              <span className="text-sm text-slate-300">Logs</span>
            </button>
          )}
          {isAdmin && (
            <button
              onClick={() => onOpenAdmin && onOpenAdmin()}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-800 transition-colors"
              title="Admin Dashboard"
            >
              <Shield className="w-5 h-5 text-amber-400" />
              <span className="text-sm text-slate-300">Admin</span>
            </button>
          )}
          <button
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            {user?.picture ? (
              <img src={user.picture} alt="" className="w-6 h-6 rounded-full" />
            ) : (
              <UserCircle className="w-5 h-5 text-slate-400" />
            )}
            <span className="text-sm text-slate-300">{user?.name || 'Profile'}</span>
          </button>
          {showProfileMenu && (
            <div className="absolute right-0 top-full mt-1 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-lg py-1 z-10">
              <div className="px-4 py-2 border-b border-slate-700">
                <p className="text-sm text-white">{user?.name}</p>
                <p className="text-xs text-slate-400">{user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
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
              <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg mx-auto">
                {sampleQuestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => { setInput(q); }}
                    className="text-left text-sm p-3 rounded-lg bg-slate-800/50 border border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
            >
              {message.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
                  <span className="text-xs">AI</span>
                </div>
              )}

              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 ${message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-200'
                  }`}
              >
                {message.role === 'user' ? (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                ) : (
                  <div className="space-y-3">
                    {/* Thinking steps (streaming) */}
                    {message.isStreaming && renderThinkingSteps(message.thinkingSteps)}

                    {/* Main content */}
                    {!message.isStreaming && message.content && (
                      <div
                        className={
                          message.dataWithheld
                            ? 'rounded-lg border border-amber-500/30 bg-amber-500/5 px-3 py-2.5'
                            : ''
                        }
                      >
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      </div>
                    )}

                    {/* Post-result thinking viewer */}
                    {!message.isStreaming && message.thinkingSteps && message.thinkingSteps.length > 0 && (
                      <details className="mt-2">
                        <summary className="cursor-pointer text-[11px] text-slate-500 hover:text-slate-300">
                          Show model thinking
                        </summary>
                        <div className="mt-1">
                          {renderThinkingSteps(message.thinkingSteps)}
                        </div>
                      </details>
                    )}

                    {/* Streaming indicator */}
                    {message.isStreaming && !message.data?.length && (
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                        <span className="text-sm text-slate-400">Processing...</span>
                      </div>
                    )}

                    {/* Error */}
                    {message.error && (
                      <div className="flex items-start gap-2 p-2 bg-red-500/10 border border-red-500/20 rounded-lg">
                        <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-red-300">{message.error}</p>
                      </div>
                    )}

                    {/* SQL (dev-only unless VITE_SHOW_SQL overrides; see config.ts) */}
                    {SHOW_SQL_UI && message.sql && (
                      <details className="mt-3">
                        <summary className="cursor-pointer text-sm text-slate-400 hover:text-slate-300 flex items-center gap-2">
                          <Code className="w-4 h-4" />
                          Show SQL
                        </summary>
                        <div className="mt-2 p-3 bg-slate-900/50 rounded-lg border border-slate-700">
                          <pre className="text-xs text-green-400 font-mono overflow-x-auto whitespace-pre-wrap">
                            {message.sql}
                          </pre>
                          {message.explanation && (
                            <p className="text-xs text-slate-400 mt-2">{message.explanation}</p>
                          )}
                        </div>
                      </details>
                    )}

                    {/* Data table (streamed progressively) */}
                    {message.data && message.data.length > 0 && (
                      <div className="mt-3">
                        {formatDataTable(message.data, message.isStreaming)}
                        {/* CSV Export button */}
                        {!message.isStreaming && (
                          <button
                            onClick={() => exportCSV(message.data!, `query_${message.id}`)}
                            className="mt-2 flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition-colors"
                          >
                            <Download className="w-3 h-3" />
                            Export CSV
                          </button>
                        )}
                      </div>
                    )}

                    {/* Data validation badge */}
                    {renderValidationBadge(message.validation, message.dataWithheld)}

                    {/* Execution error (non-fatal) */}
                    {message.executionError && (
                      <div className="flex items-start gap-2 p-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                        <AlertCircle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-yellow-300">
                          Execution error: {message.executionError}
                        </p>
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

          {isLoading && !messages.some(m => m.isStreaming) && (
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

      {/* Analytics Dashboard Modal */}
      {showAnalytics && <AnalyticsDashboard onClose={() => setShowAnalytics(false)} getAccessToken={getAccessToken} />}
    </div>
  );
};

export default Dashboard;
