import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import {
  Send, Loader2, User, Code, AlertCircle, UserCircle,
  FileText, BarChart3, LogOut, CheckCircle, AlertTriangle, XCircle,
  Download, Shield, Plus, Trash2, MessageSquare,
} from 'lucide-react';
import { API_ENDPOINTS, DEFAULT_TENANT_ID, SHOW_SQL_UI } from '../config';
import { getAuthHeadersWithToken } from '../utils/auth';
import LogsViewer from './LogsViewer';
import AnalyticsDashboard from './AnalyticsDashboard';
import AdminDashboard from './AdminDashboard';

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
  dataWithheld?: boolean;
  clarificationMessage?: string;
}

interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

interface DashboardProps {
  getAccessToken: () => Promise<string>;
  user?: any;
  onLogout?: () => void;
  onOpenAdmin?: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ getAccessToken, user, onLogout, onOpenAdmin }) => {
  const { logout: auth0Logout } = useAuth0();

  // Session state
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  // Message state
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // UI state
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);
  const [sampleQuestions, setSampleQuestions] = useState<string[]>([
    'Show me all equipment',
    'How many assets are at each location?',
    'List employees and their devices',
    'Show recent equipment movements',
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Derived tenant ID
  const activeTenantId = user?.['https://api.sargon.com/tenant_id'] || DEFAULT_TENANT_ID || '';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [messages]);

  // ── Bootstrap on mount ───────────────────────────────────────────────────

  useEffect(() => {
    (async () => {
      if (!activeTenantId) return;
      try {
        const token = await getAccessToken();
        const headers = getAuthHeadersWithToken(token);

        // Admin status
        const meRes = await fetch(API_ENDPOINTS.me, { headers });
        if (meRes.ok) {
          const me = await meRes.json();
          setIsAdmin(me.user?.is_admin === true);
        }

        // Sample questions
        const pRes = await fetch(API_ENDPOINTS.adminConfigPrompt, { headers });
        if (pRes.ok) {
          const pd = await pRes.json();
          if (Array.isArray(pd.sample_questions) && pd.sample_questions.length > 0) {
            setSampleQuestions(pd.sample_questions);
          }
        }

        // Session list
        const sRes = await fetch(
          `${API_ENDPOINTS.sessions}?tenant_id=${encodeURIComponent(activeTenantId)}&limit=50`,
          { headers }
        );
        if (sRes.ok) {
          const sd = await sRes.json();
          const list: ChatSession[] = sd.sessions || [];
          setSessions(list);
          // Auto-open the most recent session
          if (list.length > 0) {
            await loadSession(list[0].id, token);
          }
        }
      } catch {
        // non-fatal
      }
    })();
  }, [getAccessToken, activeTenantId]);

  // ── Session helpers ───────────────────────────────────────────────────────

  const loadSession = useCallback(async (sessionId: string, existingToken?: string) => {
    setCurrentSessionId(sessionId);
    setMessages([]);
    try {
      const token = existingToken ?? await getAccessToken();
      const res = await fetch(
        `${API_ENDPOINTS.history}?session_id=${encodeURIComponent(sessionId)}&tenant_id=${encodeURIComponent(activeTenantId)}`,
        { headers: getAuthHeadersWithToken(token) }
      );
      if (!res.ok) return;
      const data = await res.json();
      const historical: Message[] = [];
      for (const conv of (data.conversations || [])) {
        historical.push({
          id: `hist-user-${conv.id}`,
          role: 'user',
          content: conv.query,
          timestamp: conv.created_at,
        });
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
    } catch {
      // non-fatal
    }
  }, [getAccessToken, activeTenantId]);

  const handleNewChat = useCallback(async () => {
    if (!activeTenantId) return;
    try {
      const token = await getAccessToken();
      const res = await fetch(API_ENDPOINTS.sessions, {
        method: 'POST',
        headers: getAuthHeadersWithToken(token),
        body: JSON.stringify({ tenant_id: activeTenantId, title: 'New Chat' }),
      });
      if (!res.ok) return;
      const data = await res.json();
      const newSession: ChatSession = {
        id: data.session_id,
        title: 'New Chat',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        message_count: 0,
      };
      setSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(data.session_id);
      setMessages([]);
    } catch {
      // non-fatal
    }
  }, [getAccessToken, activeTenantId]);

  const handleDeleteSession = useCallback(async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeletingSessionId(sessionId);
    try {
      const token = await getAccessToken();
      await fetch(
        `${API_ENDPOINTS.session(sessionId)}?tenant_id=${encodeURIComponent(activeTenantId)}`,
        { method: 'DELETE', headers: getAuthHeadersWithToken(token) }
      );
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
        setMessages([]);
      }
    } catch {
      // non-fatal
    } finally {
      setDeletingSessionId(null);
    }
  }, [getAccessToken, activeTenantId, currentSessionId]);

  // ── Save conversation turn ────────────────────────────────────────────────

  const saveConversation = useCallback(async (
    sessionId: string,
    query: string,
    assistantMsg: Message,
  ) => {
    try {
      const token = await getAccessToken();
      await fetch(API_ENDPOINTS.history, {
        method: 'POST',
        headers: getAuthHeadersWithToken(token),
        body: JSON.stringify({
          session_id: sessionId,
          tenant_id: activeTenantId,
          query,
          mode: assistantMsg.sql ? 'sql' : 'chat',
          response: assistantMsg.content,
          sql_generated: assistantMsg.sql ?? null,
          row_count: assistantMsg.rowCount ?? 0,
        }),
      });
      // Bump session to top of list
      setSessions(prev => {
        const idx = prev.findIndex(s => s.id === sessionId);
        if (idx < 0) return prev;
        const updated = { ...prev[idx], updated_at: new Date().toISOString() };
        const rest = prev.filter((_, i) => i !== idx);
        return [updated, ...rest];
      });
    } catch {
      // non-fatal
    }
  }, [getAccessToken, activeTenantId]);

  // ── Streaming submit ──────────────────────────────────────────────────────

  const handleStreamingSubmit = useCallback(async (query: string, sessionId: string) => {
    const assistantMsgId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, {
      id: assistantMsgId, role: 'assistant', content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true, thinkingSteps: [], data: [], columns: [],
    }]);

    try {
      const token = await getAccessToken();
      const response = await fetch(API_ENDPOINTS.askStream, {
        method: 'POST',
        headers: { ...getAuthHeadersWithToken(token), 'X-Tenant-ID': activeTenantId },
        body: JSON.stringify({ query, tenant_id: activeTenantId, execute: true }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No readable stream');
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const eventStr of events) {
          if (!eventStr.trim()) continue;
          const lines = eventStr.split('\n');
          let eventType = '';
          let eventData = '';
          for (const line of lines) {
            if (line.startsWith('event: ')) eventType = line.slice(7);
            else if (line.startsWith('data: ')) eventData = line.slice(6);
          }
          if (!eventType || !eventData) continue;

          try {
            const data = JSON.parse(eventData);
            setMessages(prev => prev.map(msg => {
              if (msg.id !== assistantMsgId) return msg;
              const updated = { ...msg };
              switch (eventType) {
                case 'thinking':
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
                  updated.validation = { status: data.status, reasoning: data.reasoning };
                  break;
                case 'done':
                  updated.isStreaming = false;
                  updated.dataWithheld = data.data_withheld === true;
                  updated.clarificationMessage = data.clarification_message ?? undefined;
                  if (updated.dataWithheld && updated.clarificationMessage) {
                    updated.data = []; updated.columns = []; updated.rowCount = 0;
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
          } catch { /* ignore parse errors */ }
        }
      }

      // Save to DB after stream ends
      setMessages(prev => {
        const finalMsg = prev.find(m => m.id === assistantMsgId);
        if (finalMsg && !finalMsg.error) {
          saveConversation(sessionId, query, finalMsg);
        }
        return prev;
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'An unexpected error occurred';
      setMessages(prev => prev.map(m =>
        m.id === assistantMsgId
          ? { ...m, isStreaming: false, error: msg, content: `Error: ${msg}` }
          : m
      ));
    }
  }, [getAccessToken, activeTenantId, saveConversation]);

  // ── Submit handler ────────────────────────────────────────────────────────

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const query = input.trim();
    setInput('');
    setIsLoading(true);

    // Add user message
    setMessages(prev => [...prev, {
      id: Date.now().toString(), role: 'user', content: query,
      timestamp: new Date().toISOString(),
    }]);

    // Ensure we have a session
    let sessionId = currentSessionId;
    if (!sessionId) {
      try {
        const token = await getAccessToken();
        const res = await fetch(API_ENDPOINTS.sessions, {
          method: 'POST',
          headers: getAuthHeadersWithToken(token),
          body: JSON.stringify({ tenant_id: activeTenantId, title: query.slice(0, 80) }),
        });
        if (res.ok) {
          const data = await res.json();
          sessionId = data.session_id;
          const newSession: ChatSession = {
            id: data.session_id,
            title: query.slice(0, 80),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            message_count: 0,
          };
          setSessions(prev => [newSession, ...prev]);
          setCurrentSessionId(data.session_id);
        }
      } catch { /* non-fatal */ }
    }

    // Update session title from first message if it's still "New Chat"
    if (sessionId) {
      const session = sessions.find(s => s.id === sessionId);
      if (session?.title === 'New Chat' || session?.message_count === 0) {
        const newTitle = query.slice(0, 80);
        setSessions(prev => prev.map(s =>
          s.id === sessionId ? { ...s, title: newTitle } : s
        ));
        try {
          const token = await getAccessToken();
          await fetch(API_ENDPOINTS.sessionTitle(sessionId), {
            method: 'PUT',
            headers: getAuthHeadersWithToken(token),
            body: JSON.stringify({ title: newTitle }),
          });
        } catch { /* non-fatal */ }
      }
    }

    if (sessionId) {
      await handleStreamingSubmit(query, sessionId);
    }
    setIsLoading(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); }
  };

  const handleLogout = () => {
    auth0Logout({ logoutParams: { returnTo: window.location.origin } });
    if (onLogout) onLogout();
  };

  // ── Render helpers ────────────────────────────────────────────────────────

  const exportCSV = (data: any[], filename = 'query_results') => {
    if (!data?.length) return;
    const cols = Object.keys(data[0]);
    const rows = [
      cols.join(','),
      ...data.map(row => cols.map(col => {
        const val = row[col];
        if (val === null || val === undefined) return '';
        const str = String(val);
        return str.includes(',') || str.includes('"') || str.includes('\n')
          ? `"${str.replace(/"/g, '""')}"` : str;
      }).join(',')),
    ];
    const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `${filename}.csv`; a.click();
    URL.revokeObjectURL(url);
  };

  const renderValidationBadge = (validation?: ValidationInfo, hideReasoning?: boolean) => {
    if (!validation || validation.status === 'pending') return null;
    const cfg = {
      valid:   { icon: CheckCircle,   color: 'text-green-400',  bg: 'bg-green-500/10 border-green-500/20',   label: 'Validated' },
      partial: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20', label: 'Partial Match' },
      mismatch:{ icon: XCircle,       color: 'text-red-400',    bg: 'bg-red-500/10 border-red-500/20',       label: 'Mismatch' },
      skipped: { icon: AlertCircle,   color: 'text-slate-400',  bg: 'bg-slate-500/10 border-slate-500/20',   label: 'Skipped' },
      unknown: { icon: AlertCircle,   color: 'text-slate-400',  bg: 'bg-slate-500/10 border-slate-500/20',   label: 'Unknown' },
      pending: { icon: AlertCircle,   color: 'text-slate-400',  bg: 'bg-slate-500/10 border-slate-500/20',   label: 'Pending' },
    };
    const c = cfg[validation.status] ?? cfg.skipped;
    const Icon = c.icon;
    return (
      <details className="mt-3">
        <summary className={`cursor-pointer text-sm flex items-center gap-2 p-2 rounded-lg border ${c.bg}`}>
          <Icon className={`w-4 h-4 ${c.color}`} />
          <span className={c.color}>Data Validation: {c.label}</span>
        </summary>
        {validation.reasoning && !hideReasoning && (
          <p className="text-xs text-slate-400 mt-2 px-2">{validation.reasoning}</p>
        )}
      </details>
    );
  };

  const formatDataTable = (data: any[], isStreaming?: boolean) => {
    if (!data?.length) return null;
    const columns = Object.keys(data[0]);
    return (
      <div className="overflow-x-auto mt-3">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-slate-700">
              {columns.map(col => (
                <th key={col} className="text-left py-2 px-3 text-slate-400 font-semibold">
                  {col.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr key={idx} className={`border-b border-slate-800 hover:bg-slate-800/50 ${isStreaming && idx === data.length - 1 ? 'animate-pulse' : ''}`}>
                {columns.map(col => (
                  <td key={col} className="py-2 px-3 text-slate-300">
                    {row[col] === null || row[col] === undefined ? (
                      <span className="text-slate-500">—</span>
                    ) : typeof row[col] === 'object' ? (
                      <pre className="text-xs">{JSON.stringify(row[col], null, 2)}</pre>
                    ) : String(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-xs text-slate-500 mt-2 px-3">
          {isStreaming ? `${data.length} rows loaded...` : `${data.length} total results`}
        </p>
      </div>
    );
  };

  const renderThinkingSteps = (steps?: string[]) => {
    if (!steps?.length) return null;
    return (
      <div className="mb-1">
        <p className="whitespace-pre-wrap text-xs text-slate-500/90 italic">{steps.join('')}</p>
      </div>
    );
  };

  const formatRelativeTime = (iso: string) => {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  // ── Layout ────────────────────────────────────────────────────────────────

  return (
    <div className="flex h-screen bg-[#0f0f23] text-white overflow-hidden">

      {/* ── Sidebar ── */}
      <div className="w-64 flex-shrink-0 flex flex-col bg-[#0a0a1a] border-r border-slate-800">
        {/* Sidebar header */}
        <div className="p-3 border-b border-slate-800">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors text-sm font-medium text-slate-200"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto py-2">
          {sessions.length === 0 ? (
            <p className="text-xs text-slate-600 text-center mt-6 px-4">No conversations yet</p>
          ) : (
            sessions.map(session => (
              <div
                key={session.id}
                onClick={() => loadSession(session.id)}
                className={`group relative flex items-start gap-2 mx-2 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                  currentSessionId === session.id
                    ? 'bg-slate-700 text-white'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                }`}
              >
                <MessageSquare className="w-4 h-4 mt-0.5 flex-shrink-0 opacity-60" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate leading-snug">{session.title}</p>
                  <p className="text-[11px] text-slate-500 mt-0.5">{formatRelativeTime(session.updated_at)}</p>
                </div>
                <button
                  onClick={(e) => handleDeleteSession(session.id, e)}
                  disabled={deletingSessionId === session.id}
                  className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-1 rounded hover:bg-slate-600 text-slate-400 hover:text-red-400 transition-all"
                >
                  {deletingSessionId === session.id
                    ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    : <Trash2 className="w-3.5 h-3.5" />}
                </button>
              </div>
            ))
          )}
        </div>

        {/* Sidebar footer — user + actions */}
        <div className="border-t border-slate-800 p-3 space-y-1">
          {isAdmin && (
            <>
              <button
                onClick={() => setShowAnalytics(true)}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
              >
                <BarChart3 className="w-4 h-4" />
                Analytics
              </button>
              <button
                onClick={() => setShowLogs(true)}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
              >
                <FileText className="w-4 h-4" />
                Logs
              </button>
              <button
                onClick={() => onOpenAdmin?.()}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-amber-400 hover:bg-slate-800 transition-colors"
              >
                <Shield className="w-4 h-4" />
                Admin
              </button>
            </>
          )}
          <div className="relative">
            <button
              onClick={() => setShowProfileMenu(p => !p)}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
            >
              {user?.picture
                ? <img src={user.picture} alt="" className="w-5 h-5 rounded-full" />
                : <UserCircle className="w-4 h-4" />}
              <span className="truncate">{user?.name || 'Profile'}</span>
            </button>
            {showProfileMenu && (
              <div className="absolute bottom-full left-0 right-0 mb-1 bg-slate-800 border border-slate-700 rounded-lg shadow-lg py-1 z-10">
                <div className="px-3 py-2 border-b border-slate-700">
                  <p className="text-xs text-white font-medium truncate">{user?.name}</p>
                  <p className="text-xs text-slate-400 truncate">{user?.email}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-3 py-2 text-sm text-red-300 hover:bg-slate-700 flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Main chat area ── */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Top bar */}
        <div className="flex items-center px-6 py-3 border-b border-slate-800 bg-[#0f0f23]">
          <h1 className="text-base font-semibold text-white">
            {currentSessionId
              ? (sessions.find(s => s.id === currentSessionId)?.title || 'Chat')
              : 'Invisitag Support'}
          </h1>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <h2 className="text-2xl font-semibold text-slate-300 mb-2">
                  {currentSessionId ? 'Start a conversation' : 'Welcome to Invisitag Support'}
                </h2>
                <p className="text-slate-500">Ask me anything about your database</p>
                <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg mx-auto">
                  {sampleQuestions.filter(Boolean).map(q => (
                    <button
                      key={q}
                      onClick={() => setInput(q)}
                      className="text-left text-sm p-3 rounded-lg bg-slate-800/50 border border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600 transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map(message => (
              <div key={message.id} className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
                    <span className="text-xs">AI</span>
                  </div>
                )}
                <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${message.role === 'user' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-200'}`}>
                  {message.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  ) : (
                    <div className="space-y-3">
                      {message.isStreaming && renderThinkingSteps(message.thinkingSteps)}
                      {!message.isStreaming && message.content && (
                        <div className={message.dataWithheld ? 'rounded-lg border border-amber-500/30 bg-amber-500/5 px-3 py-2.5' : ''}>
                          <p className="whitespace-pre-wrap">{message.content}</p>
                        </div>
                      )}
                      {!message.isStreaming && message.thinkingSteps && message.thinkingSteps.length > 0 && (
                        <details className="mt-2">
                          <summary className="cursor-pointer text-[11px] text-slate-500 hover:text-slate-300">Show model thinking</summary>
                          <div className="mt-1">{renderThinkingSteps(message.thinkingSteps)}</div>
                        </details>
                      )}
                      {message.isStreaming && !message.data?.length && (
                        <div className="flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                          <span className="text-sm text-slate-400">Processing...</span>
                        </div>
                      )}
                      {message.error && (
                        <div className="flex items-start gap-2 p-2 bg-red-500/10 border border-red-500/20 rounded-lg">
                          <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                          <p className="text-sm text-red-300">{message.error}</p>
                        </div>
                      )}
                      {SHOW_SQL_UI && message.sql && (
                        <details className="mt-3">
                          <summary className="cursor-pointer text-sm text-slate-400 hover:text-slate-300 flex items-center gap-2">
                            <Code className="w-4 h-4" /> Show SQL
                          </summary>
                          <div className="mt-2 p-3 bg-slate-900/50 rounded-lg border border-slate-700">
                            <pre className="text-xs text-green-400 font-mono overflow-x-auto whitespace-pre-wrap">{message.sql}</pre>
                            {message.explanation && <p className="text-xs text-slate-400 mt-2">{message.explanation}</p>}
                          </div>
                        </details>
                      )}
                      {message.data && message.data.length > 0 && (
                        <div className="mt-3">
                          {formatDataTable(message.data, message.isStreaming)}
                          {!message.isStreaming && (
                            <button
                              onClick={() => exportCSV(message.data!, `query_${message.id}`)}
                              className="mt-2 flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition-colors"
                            >
                              <Download className="w-3 h-3" /> Export CSV
                            </button>
                          )}
                        </div>
                      )}
                      {renderValidationBadge(message.validation, message.dataWithheld)}
                      {message.executionError && (
                        <div className="flex items-start gap-2 p-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                          <AlertCircle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                          <p className="text-sm text-yellow-300">Execution error: {message.executionError}</p>
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

        {/* Input */}
        <div className="border-t border-slate-800 bg-[#0f0f23] px-4 py-4">
          <div className="max-w-3xl mx-auto">
            <form onSubmit={handleSubmit} className="flex items-end gap-3">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={e => {
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
                {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              </button>
            </form>
            <p className="text-xs text-slate-500 mt-2 text-center">Press Enter to send, Shift+Enter for new line</p>
          </div>
        </div>
      </div>

      {/* Modals */}
      {showLogs && <LogsViewer onClose={() => setShowLogs(false)} />}
      {showAnalytics && <AnalyticsDashboard onClose={() => setShowAnalytics(false)} getAccessToken={getAccessToken} />}
    </div>
  );
};

export default Dashboard;
