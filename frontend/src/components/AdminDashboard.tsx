import React, { useState, useEffect, useCallback } from 'react';
import {
  X,
  RefreshCw,
  Shield,
  FileText,
  Settings,
  BarChart3,
  Users,
  Save,
  AlertCircle,
  TrendingUp,
  Database,
  MessageSquare,
  Clock,
  CheckCircle,
} from 'lucide-react';
import { API_ENDPOINTS } from '../config';
import { getAuthHeadersWithToken } from '../utils/auth';

interface AdminDashboardProps {
  onClose: () => void;
  getAccessToken: () => Promise<string>;
  user?: any;
}

type Section = 'guardrails' | 'accounts' | 'totals' | 'analytics';

// Fixed response-format block. Kept in code so we never show it in the UI;
// we strip it when displaying and append it when saving so the backend still gets the full prompt.
const FIXED_RESPONSE_SCHEMA = `

Your response (internal format for the application) must be valid JSON with:
{
  "mode": "chat" | "clarification" | "sql",
  "response": "Short natural language reply for the user",
  "sql": "Single-line SQL query if mode is sql, otherwise null"
}`;

// Default prompt text to show when no custom template has been saved yet.
// Does not include the internal JSON format; that is appended on save and hidden from view.
const DEFAULT_VISIBLE_PROMPT_TEMPLATE = `You are an AI assistant for the Sargon Partners asset-tracking system.
Your job is to help users ask questions about their tagged assets and translate those questions into safe SQL.

Always:
- Be concise and clear in your natural language responses.
- If you generate SQL, strictly follow the provided database schema and tenant/account rules.
- Never show raw SQL to the user unless explicitly requested.

SQL generation rules (when the request is clearly about data):
- Only generate SELECT queries.
- Always filter by the user's tenant/accountId (do not allow cross-tenant access).
- Use human-friendly identifiers (like serialNumber, description) in the SELECT list; avoid exposing internal IDs.
- Do not include accountId in the visible output columns.

Context you have:
- Database schema:\n{schema_context}\n
- Extra codes / enums / business rules (optional):\n{db_context}\n
- Tenant ID for this request: {tenant_id}
- User's original question: {natural_language_query}

Decide how to respond:
- If the user is just greeting or asking a general question, respond in natural language (no SQL needed).
- If the user question is unclear or missing key details, ask a follow-up clarification question.
- If the user clearly wants data, generate a SQL query that follows the rules above.`;

export default function AdminDashboard({ onClose, getAccessToken, user }: AdminDashboardProps) {
  const [activeSection, setActiveSection] = useState<Section>('totals');
  const [totals, setTotals] = useState<{
    total_requests: number;
    total_errors: number;
    total_sql_queries: number;
    success_rate: number;
    uptime_hours: number;
  } | null>(null);
  const [tenantIds, setTenantIds] = useState<string[]>([]);
  const [selectedTenantId, setSelectedTenantId] = useState<string>('');
  const [accountMetrics, setAccountMetrics] = useState<Record<string, unknown> | null>(null);
  const [accountLogs, setAccountLogs] = useState<Array<{ timestamp: string; level: string; message: string; tenant_id: string }>>([]);
  const [guardrails, setGuardrails] = useState<{
    allowed_tenant_ids: string[];
    dangerous_keywords: string[];
    sql_injection_patterns: string[];
    tenant_column: string;
  } | null>(null);
  const [promptTemplate, setPromptTemplate] = useState<string>('');
  const [dbContext, setDbContext] = useState<string>('');
  const [sampleQuestions, setSampleQuestions] = useState<string[]>([
    'Show me all equipment',
    'How many assets are at each location?',
    'List employees and their devices',
    'Show recent equipment movements',
  ]);
  const [llmConfig, setLlmConfig] = useState<{ max_tokens: number; temperature: number; validation_max_tokens: number } | null>(null);
  const [analyticsData, setAnalyticsData] = useState<{
    summary: {
      total_requests: number;
      total_errors: number;
      total_sql_queries: number;
      total_chat_responses: number;
      total_clarification_responses: number;
      success_rate: number;
      uptime_hours: number;
      total_input_tokens: number;
      total_output_tokens: number;
      total_tokens: number;
    };
    errors: { by_type: Record<string, number>; total: number };
    performance: {
      avg_query_execution_time_ms: number;
      avg_bedrock_call_time_ms: number;
      query_execution_samples: number;
      bedrock_call_samples: number;
    };
    hourly: Array<{ hour: number; requests: number; errors: number }>;
    timestamp: string;
  } | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchWithAuth = useCallback(
    async (url: string, options?: RequestInit) => {
      const token = await getAccessToken();
      const res = await fetch(url, {
        ...options,
        headers: {
          ...getAuthHeadersWithToken(token),
          ...options?.headers,
        },
      });
      if (!res.ok) throw new Error(res.statusText || 'Request failed');
      return res.json();
    },
    [getAccessToken]
  );

  const loadTotals = useCallback(async () => {
    try {
      const data = await fetchWithAuth(API_ENDPOINTS.adminMetrics);
      setTotals(data.summary || null);
      setTenantIds((data.by_tenant && Object.keys(data.by_tenant)) || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load metrics');
    }
  }, [fetchWithAuth]);

  const loadAccountMetrics = useCallback(async () => {
    if (!selectedTenantId) return;
    try {
      const data = await fetchWithAuth(API_ENDPOINTS.adminMetricsAccount(selectedTenantId));
      setAccountMetrics(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load account metrics');
    }
  }, [fetchWithAuth, selectedTenantId]);

  const loadAccountLogs = useCallback(async () => {
    if (!selectedTenantId) return;
    try {
      const data = await fetchWithAuth(
        `${API_ENDPOINTS.adminLogs}?tenant_id=${encodeURIComponent(selectedTenantId)}&limit=100`
      );
      setAccountLogs(data.logs || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load logs');
    }
  }, [fetchWithAuth, selectedTenantId]);

  const loadGuardrails = useCallback(async () => {
    try {
      const data = await fetchWithAuth(API_ENDPOINTS.adminConfigGuardrails);
      setGuardrails(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load guardrails');
    }
  }, [fetchWithAuth]);

  const loadPrompt = useCallback(async () => {
    try {
      const data = await fetchWithAuth(API_ENDPOINTS.adminConfigPrompt);
      if (data.prompt_template) {
        // Strip the fixed JSON schema so admins only see the editable part.
        const schemaBlock = FIXED_RESPONSE_SCHEMA.trim();
        const withoutSchema = data.prompt_template.includes(schemaBlock)
          ? data.prompt_template.replace(schemaBlock, '').trim()
          : data.prompt_template;
        setPromptTemplate(withoutSchema);
      } else {
        setPromptTemplate(DEFAULT_VISIBLE_PROMPT_TEMPLATE);
      }
      if (Array.isArray(data.sample_questions) && data.sample_questions.length > 0) {
        setSampleQuestions(data.sample_questions);
      }
      setDbContext(typeof data.db_context === 'string' ? data.db_context : '');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load prompt');
    }
  }, [fetchWithAuth]);

  const loadLlm = useCallback(async () => {
    try {
      const data = await fetchWithAuth(API_ENDPOINTS.adminConfigLlm);
      setLlmConfig(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load LLM config');
    }
  }, [fetchWithAuth]);

  const loadAnalytics = useCallback(async () => {
    setAnalyticsLoading(true);
    try {
      const data = await fetchWithAuth(API_ENDPOINTS.analytics);
      setAnalyticsData(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load analytics');
    } finally {
      setAnalyticsLoading(false);
    }
  }, [fetchWithAuth]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        await loadTotals();
        await loadGuardrails();
        await loadPrompt();
        await loadLlm();
      } finally {
        setLoading(false);
      }
    })();
  }, [loadTotals, loadGuardrails, loadPrompt, loadLlm]);

  useEffect(() => {
    if (activeSection === 'accounts' && selectedTenantId) {
      loadAccountMetrics();
      loadAccountLogs();
    }
  }, [activeSection, selectedTenantId, loadAccountMetrics, loadAccountLogs]);

  useEffect(() => {
    if (activeSection === 'analytics') {
      loadAnalytics();
    }
  }, [activeSection, loadAnalytics]);

  useEffect(() => {
    if (activeSection === 'analytics' && autoRefresh) {
      const interval = setInterval(loadAnalytics, 5000);
      return () => clearInterval(interval);
    }
  }, [activeSection, autoRefresh, loadAnalytics]);

  // Guardrails are safety-critical (tenant isolation, dangerous SQL keywords, accountId column).
  // Per client request, these are view-only in the dashboard and can only be changed in code.
  const handleSaveGuardrails = async () => {
    // No-op on purpose; leaving here in case we add limited, safe edits later.
    return;
  };

  const handleSavePrompt = async () => {
    setSaving('prompt');
    setError(null);
    const fullPrompt = promptTemplate?.trim()
      ? promptTemplate.trim() + FIXED_RESPONSE_SCHEMA
      : null;
    try {
      const token = await getAccessToken();
      const res = await fetch(API_ENDPOINTS.adminConfigPrompt, {
        method: 'PUT',
        headers: getAuthHeadersWithToken(token),
        body: JSON.stringify({ prompt_template: fullPrompt }),
      });
      if (!res.ok) throw new Error('Save failed');
      setSaving(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save prompt');
      setSaving(null);
    }
  };

  const handleSaveSampleQuestions = async () => {
    setSaving('sample_questions');
    setError(null);
    try {
      const token = await getAccessToken();
      const res = await fetch(API_ENDPOINTS.adminConfigPrompt, {
        method: 'PUT',
        headers: getAuthHeadersWithToken(token),
        body: JSON.stringify({ sample_questions: sampleQuestions }),
      });
      if (!res.ok) throw new Error('Save failed');
      setSaving(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save sample questions');
      setSaving(null);
    }
  };

  const handleSaveDbContext = async () => {
    setSaving('db_context');
    setError(null);
    try {
      const token = await getAccessToken();
      const res = await fetch(API_ENDPOINTS.adminConfigPrompt, {
        method: 'PUT',
        headers: getAuthHeadersWithToken(token),
        body: JSON.stringify({ db_context: dbContext }),
      });
      if (!res.ok) throw new Error('Save failed');
      setSaving(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save database context');
      setSaving(null);
    }
  };

  const handleSaveLlm = async () => {
    if (!llmConfig) return;
    setSaving('llm');
    setError(null);
    try {
      const token = await getAccessToken();
      const res = await fetch(API_ENDPOINTS.adminConfigLlm, {
        method: 'PUT',
        headers: getAuthHeadersWithToken(token),
        body: JSON.stringify(llmConfig),
      });
      if (!res.ok) throw new Error('Save failed');
      setSaving(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save LLM config');
      setSaving(null);
    }
  };

  if (loading && !totals) {
    return (
      <div className="h-screen bg-[#0f0f23] flex items-center justify-center">
        <div className="text-slate-400">Loading admin dashboard...</div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#0f0f23] text-white flex flex-col overflow-hidden">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-slate-800 bg-[#0f0f23]">
        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
          <Shield className="w-5 h-5 text-amber-400" />
          Admin Dashboard
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              loadTotals();
              loadGuardrails();
              loadPrompt();
              loadLlm();
              setError(null);
            }}
            className="px-3 py-1.5 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
          >
            <RefreshCw className="w-4 h-4 inline mr-1" />
            Refresh
          </button>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mx-4 mt-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Section tabs */}
      <div className="flex border-b border-slate-700 px-4 gap-1">
        {(
          [
            { id: 'totals' as Section, label: 'Totals', icon: BarChart3 },
            { id: 'accounts' as Section, label: 'Per account', icon: Users },
            { id: 'analytics' as Section, label: 'Analytics', icon: TrendingUp },
            { id: 'guardrails' as Section, label: 'Prompt & LLM', icon: Settings },
          ] as const
        ).map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveSection(id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeSection === id
                ? 'border-amber-500 text-amber-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Main content: min-h-0 lets flex children shrink; guardrails tab uses full-height prompt editor */}
      <div className="flex-1 min-h-0 overflow-y-auto p-6 flex flex-col">
        {/* Section 3: Totals */}
        {activeSection === 'totals' && totals && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Total usage & metrics</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-sm text-slate-400">Total requests</div>
                <div className="text-2xl font-bold text-white">{totals.total_requests}</div>
              </div>
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-sm text-slate-400">Total errors</div>
                <div className="text-2xl font-bold text-red-400">{totals.total_errors}</div>
              </div>
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-sm text-slate-400">Total SQL queries</div>
                <div className="text-2xl font-bold text-white">{totals.total_sql_queries}</div>
              </div>
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-sm text-slate-400">Success rate</div>
                <div className="text-2xl font-bold text-green-400">
                  {totals.success_rate?.toFixed(1) ?? 0}%
                </div>
              </div>
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-sm text-slate-400">Uptime (hours)</div>
                <div className="text-2xl font-bold text-white">
                  {totals.uptime_hours?.toFixed(1) ?? 0}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Section 2: Per-account */}
        {activeSection === 'accounts' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Information by account</h3>
            <div className="flex flex-wrap items-center gap-2">
              <label className="text-sm text-slate-400">Account (tenant):</label>
              <select
                value={selectedTenantId}
                onChange={(e) => setSelectedTenantId(e.target.value)}
                className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm min-w-[280px]"
              >
                <option value="">Select an account</option>
                {tenantIds.map((id) => (
                  <option key={id} value={id}>
                    {id}
                  </option>
                ))}
              </select>
            </div>
            {selectedTenantId && (
              <>
                {accountMetrics && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="bg-slate-800 rounded-lg p-3 border border-slate-700">
                      <div className="text-xs text-slate-400">Requests</div>
                      <div className="text-xl font-bold text-white">
                        {(accountMetrics as any).requests ?? 0}
                      </div>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-3 border border-slate-700">
                      <div className="text-xs text-slate-400">Errors</div>
                      <div className="text-xl font-bold text-red-400">
                        {(accountMetrics as any).errors ?? 0}
                      </div>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-3 border border-slate-700">
                      <div className="text-xs text-slate-400">SQL queries</div>
                      <div className="text-xl font-bold text-white">
                        {(accountMetrics as any).sql_queries ?? 0}
                      </div>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-3 border border-slate-700">
                      <div className="text-xs text-slate-400">Success rate</div>
                      <div className="text-xl font-bold text-green-400">
                        {(accountMetrics as any).success_rate ?? 0}%
                      </div>
                    </div>
                  </div>
                )}
                <div>
                  <h4 className="text-sm font-semibold text-slate-300 mb-2">
                    Query log (this account)
                  </h4>
                  <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
                    <div className="max-h-64 overflow-y-auto">
                      {accountLogs.length === 0 ? (
                        <p className="p-4 text-slate-500 text-sm">No logs for this account yet.</p>
                      ) : (
                        <table className="w-full text-sm">
                          <thead className="bg-slate-800/80 sticky top-0">
                            <tr className="text-left text-slate-400">
                              <th className="p-2">Time</th>
                              <th className="p-2">Level</th>
                              <th className="p-2">Message</th>
                            </tr>
                          </thead>
                          <tbody>
                            {accountLogs.map((log, i) => (
                              <tr key={i} className="border-t border-slate-700">
                                <td className="p-2 text-slate-500 whitespace-nowrap">
                                  {log.timestamp?.slice(0, 19)}
                                </td>
                                <td className="p-2">{log.level}</td>
                                <td className="p-2 text-slate-300 break-all">{log.message}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* Analytics tab */}
        {activeSection === 'analytics' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">Analytics</h3>
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
                  onClick={loadAnalytics}
                  disabled={analyticsLoading}
                  className="px-3 py-1.5 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 text-sm disabled:opacity-50"
                >
                  <RefreshCw className={`w-4 h-4 inline mr-1 ${analyticsLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>
            </div>

            {analyticsLoading && !analyticsData && (
              <div className="text-slate-400 text-sm">Loading analytics...</div>
            )}

            {analyticsData && (() => {
              const { summary, errors, performance, hourly } = analyticsData;
              return (
                <>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                      <div className="flex items-center justify-between mb-2">
                        <TrendingUp className="w-5 h-5 text-blue-400" />
                        <span className="text-2xl font-bold text-white">{summary.total_requests}</span>
                      </div>
                      <div className="text-sm text-slate-400">Total Requests</div>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                      <div className="flex items-center justify-between mb-2">
                        <AlertCircle className="w-5 h-5 text-red-400" />
                        <span className="text-2xl font-bold text-white">{summary.total_errors}</span>
                      </div>
                      <div className="text-sm text-slate-400">Total Errors</div>
                      <div className="text-xs text-slate-500 mt-1">
                        {summary.total_requests > 0
                          ? `${((summary.total_errors / summary.total_requests) * 100).toFixed(1)}% error rate`
                          : '0% error rate'}
                      </div>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                      <div className="flex items-center justify-between mb-2">
                        <CheckCircle className="w-5 h-5 text-green-400" />
                        <span className="text-2xl font-bold text-white">{summary.success_rate.toFixed(1)}%</span>
                      </div>
                      <div className="text-sm text-slate-400">Success Rate</div>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                      <div className="flex items-center justify-between mb-2">
                        <Clock className="w-5 h-5 text-purple-400" />
                        <span className="text-2xl font-bold text-white">{summary.uptime_hours.toFixed(1)}h</span>
                      </div>
                      <div className="text-sm text-slate-400">Uptime</div>
                    </div>
                  </div>

                  {/* Token usage */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                      <div className="text-sm text-slate-400 mb-1">Input Tokens</div>
                      <div className="text-2xl font-bold text-white">{summary.total_input_tokens.toLocaleString()}</div>
                      <div className="text-xs text-slate-500 mt-1">Prompt tokens sent to model</div>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                      <div className="text-sm text-slate-400 mb-1">Output Tokens</div>
                      <div className="text-2xl font-bold text-white">{summary.total_output_tokens.toLocaleString()}</div>
                      <div className="text-xs text-slate-500 mt-1">Tokens generated by model</div>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                      <div className="text-sm text-slate-400 mb-1">Total Tokens</div>
                      <div className="text-2xl font-bold text-amber-400">{summary.total_tokens.toLocaleString()}</div>
                      <div className="text-xs text-slate-500 mt-1">Combined usage</div>
                    </div>
                  </div>

                  {/* Activity breakdown */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                      <div className="flex items-center gap-2 mb-2">
                        <Database className="w-5 h-5 text-blue-400" />
                        <span className="text-lg font-semibold text-white">SQL Queries</span>
                      </div>
                      <div className="text-3xl font-bold text-white">{summary.total_sql_queries}</div>
                      <div className="text-xs text-slate-500 mt-1">
                        {summary.total_requests > 0
                          ? `${((summary.total_sql_queries / summary.total_requests) * 100).toFixed(1)}% of requests`
                          : '0% of requests'}
                      </div>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                      <div className="flex items-center gap-2 mb-2">
                        <MessageSquare className="w-5 h-5 text-green-400" />
                        <span className="text-lg font-semibold text-white">Chat Responses</span>
                      </div>
                      <div className="text-3xl font-bold text-white">{summary.total_chat_responses}</div>
                      <div className="text-xs text-slate-500 mt-1">
                        {summary.total_requests > 0
                          ? `${((summary.total_chat_responses / summary.total_requests) * 100).toFixed(1)}% of requests`
                          : '0% of requests'}
                      </div>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                      <div className="flex items-center gap-2 mb-2">
                        <MessageSquare className="w-5 h-5 text-yellow-400" />
                        <span className="text-lg font-semibold text-white">Clarifications</span>
                      </div>
                      <div className="text-3xl font-bold text-white">{summary.total_clarification_responses}</div>
                      <div className="text-xs text-slate-500 mt-1">
                        {summary.total_requests > 0
                          ? `${((summary.total_clarification_responses / summary.total_requests) * 100).toFixed(1)}% of requests`
                          : '0% of requests'}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                      <h4 className="text-sm font-semibold text-slate-200 mb-4">Performance Metrics</h4>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-slate-400 text-sm">Avg Query Execution</span>
                          <span className="text-white font-semibold">{performance.avg_query_execution_time_ms.toFixed(2)} ms</span>
                        </div>
                        <div className="text-xs text-slate-500">Based on {performance.query_execution_samples} samples</div>
                        <div className="flex justify-between items-center mt-4">
                          <span className="text-slate-400 text-sm">Avg Bedrock Call</span>
                          <span className="text-white font-semibold">{performance.avg_bedrock_call_time_ms.toFixed(2)} ms</span>
                        </div>
                        <div className="text-xs text-slate-500">Based on {performance.bedrock_call_samples} samples</div>
                      </div>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                      <h4 className="text-sm font-semibold text-slate-200 mb-4">Error Breakdown</h4>
                      {Object.keys(errors.by_type).length === 0 ? (
                        <div className="text-slate-500 text-sm">No errors recorded</div>
                      ) : (
                        <div className="space-y-2">
                          {Object.entries(errors.by_type)
                            .sort(([, a], [, b]) => b - a)
                            .map(([errorType, count]) => (
                              <div key={errorType} className="flex justify-between items-center">
                                <span className="text-slate-400 text-sm capitalize">{errorType.replace(/_/g, ' ')}</span>
                                <span className="text-red-400 font-semibold">{count}</span>
                              </div>
                            ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                    <h4 className="text-sm font-semibold text-slate-200 mb-4">Hourly Activity (Last 24 Hours)</h4>
                    <div className="space-y-2">
                      {hourly.map((hourData, index) => {
                        const maxRequests = Math.max(...hourly.map(h => h.requests), 1);
                        const requestWidth = (hourData.requests / maxRequests) * 100;
                        const errorWidth = hourData.requests > 0 ? (hourData.errors / hourData.requests) * 100 : 0;
                        return (
                          <div key={index} className="flex items-center gap-4">
                            <div className="w-16 text-xs text-slate-400 text-right">
                              {hourData.hour.toString().padStart(2, '0')}:00
                            </div>
                            <div className="flex-1 relative">
                              <div className="h-6 bg-slate-700 rounded relative overflow-hidden">
                                <div className="h-full bg-blue-500/50 rounded" style={{ width: `${requestWidth}%` }} />
                                {hourData.errors > 0 && (
                                  <div className="h-full bg-red-500/70 rounded absolute top-0 right-0" style={{ width: `${errorWidth}%` }} />
                                )}
                              </div>
                            </div>
                            <div className="w-20 text-xs text-slate-400 text-right">
                              {hourData.requests} req
                              {hourData.errors > 0 && <span className="text-red-400 ml-1">({hourData.errors} err)</span>}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="text-xs text-slate-500 text-center">
                    Last updated: {new Date(analyticsData.timestamp).toLocaleString()}
                  </div>
                </>
              );
            })()}
          </div>
        )}

        {/* Section 1: Prompt & LLM */}
        {activeSection === 'guardrails' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-white">Prompt & LLM configuration</h3>

            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 flex flex-col">
              <h4 className="text-sm font-semibold text-slate-200 mb-2 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Database context
              </h4>
              <p className="text-xs text-slate-500 mb-3">
                Optional notes for the model: enum values, column meanings, or business rules not obvious from the schema.
                Example: locationType 0 = warehouse, 1 = truck, 2 = on job site. Injected into every NL→SQL prompt (built-in
                or custom). Custom templates can use {'{db_context}'}.
              </p>
              <textarea
                value={dbContext}
                onChange={(e) => setDbContext(e.target.value)}
                placeholder="e.g. EquipmentLocation.locationType: 0 = warehouse, 1 = truck, 2 = on job..."
                className="w-full min-h-[8rem] max-h-64 bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white text-sm font-mono resize-y overflow-y-auto"
              />
              <button
                onClick={handleSaveDbContext}
                disabled={saving === 'db_context'}
                className="mt-2 flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-600 text-white hover:bg-amber-500 disabled:opacity-50 text-sm"
              >
                <Save className="w-4 h-4" />
                {saving === 'db_context' ? 'Saving...' : 'Save database context'}
              </button>
            </div>

            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 flex flex-col">
              <h4 className="text-sm font-semibold text-slate-200 mb-2 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                LLM prompt template
              </h4>
              <p className="text-xs text-slate-500 mb-3">
                Use placeholders: {'{schema_context}'}, {'{tenant_id}'}, {'{natural_language_query}'}, {'{db_context}'}.
                Leave empty to use built-in prompt.
              </p>
              <textarea
                value={promptTemplate}
                onChange={(e) => setPromptTemplate(e.target.value)}
                placeholder="Optional custom prompt template..."
                className="w-full min-h-[14rem] h-64 bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white text-sm font-mono resize-y overflow-y-auto"
              />
              <button
                onClick={handleSavePrompt}
                disabled={saving === 'prompt'}
                className="mt-2 flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-600 text-white hover:bg-amber-500 disabled:opacity-50 text-sm"
              >
                <Save className="w-4 h-4" />
                {saving === 'prompt' ? 'Saving...' : 'Save prompt'}
              </button>
            </div>

            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h4 className="text-sm font-semibold text-slate-200 mb-2 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Sample questions on welcome screen
              </h4>
              <p className="text-xs text-slate-500 mb-3">
                These appear as quick-start buttons when the chat is empty. Use short, clear
                questions that demonstrate common use cases for your data.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {sampleQuestions.map((q, idx) => (
                  <div key={idx} className="space-y-1">
                    <label className="text-[11px] text-slate-500 block">
                      Question {idx + 1}
                    </label>
                    <input
                      type="text"
                      value={q}
                      onChange={(e) => {
                        const next = [...sampleQuestions];
                        next[idx] = e.target.value;
                        setSampleQuestions(next);
                      }}
                      placeholder={`Sample question ${idx + 1}`}
                      className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-xs text-white"
                    />
                  </div>
                ))}
              </div>
              <p className="text-[11px] text-slate-500 mt-2">
                Leave any field blank to hide that question from the welcome screen.
              </p>
              <button
                onClick={handleSaveSampleQuestions}
                disabled={saving === 'sample_questions'}
                className="mt-3 flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-600 text-white hover:bg-amber-500 disabled:opacity-50 text-sm"
              >
                <Save className="w-4 h-4" />
                {saving === 'sample_questions' ? 'Saving...' : 'Save sample questions'}
              </button>
            </div>

            {llmConfig && (
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  LLM parameters
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Answer length</label>
                    <p className="text-[11px] text-slate-500 mb-1">
                      Choose how long you want typical answers to be.
                    </p>
                    <select
                      value={
                        llmConfig.max_tokens <= 600
                          ? 'short'
                          : llmConfig.max_tokens <= 1400
                          ? 'medium'
                          : 'long'
                      }
                      onChange={(e) => {
                        const preset = e.target.value as 'short' | 'medium' | 'long';
                        const maxTokens =
                          preset === 'short' ? 512 : preset === 'medium' ? 1024 : 2048;
                        const validationTokens = Math.min(1024, Math.floor(maxTokens / 2));
                        setLlmConfig({
                          ...llmConfig,
                          max_tokens: maxTokens,
                          validation_max_tokens: validationTokens,
                        });
                      }}
                      className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white text-sm"
                    >
                      <option value="short">Short (~1–2 paragraphs)</option>
                      <option value="medium">Medium (~2–4 paragraphs)</option>
                      <option value="long">Long (more detailed answers)</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Style</label>
                    <p className="text-[11px] text-slate-500 mb-1">
                      More conservative answers stick closely to the data; more creative answers are
                      freer in wording.
                    </p>
                    <select
                      value={
                        llmConfig.temperature <= 0.15
                          ? 'conservative'
                          : llmConfig.temperature <= 0.35
                          ? 'balanced'
                          : 'creative'
                      }
                      onChange={(e) => {
                        const preset = e.target.value as 'conservative' | 'balanced' | 'creative';
                        const temperature =
                          preset === 'conservative' ? 0.1 : preset === 'balanced' ? 0.3 : 0.6;
                        setLlmConfig({
                          ...llmConfig,
                          temperature,
                        });
                      }}
                      className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white text-sm"
                    >
                      <option value="conservative">Conservative (very literal, safest)</option>
                      <option value="balanced">Balanced (default)</option>
                      <option value="creative">More conversational</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">
                      Advanced (validation detail)
                    </label>
                    <p className="text-[11px] text-slate-500 mb-1">
                      How much text the model sees when double-checking results. In most cases, you
                      can leave this as-is.
                    </p>
                    <input
                      type="number"
                      min={256}
                      max={2048}
                      value={llmConfig.validation_max_tokens}
                      onChange={(e) =>
                        setLlmConfig({
                          ...llmConfig,
                          validation_max_tokens: parseInt(e.target.value, 10) || 1024,
                        })
                      }
                      className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white text-sm"
                    />
                  </div>
                </div>
                <button
                  onClick={handleSaveLlm}
                  disabled={saving === 'llm'}
                  className="mt-3 flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-600 text-white hover:bg-amber-500 disabled:opacity-50 text-sm"
                >
                  <Save className="w-4 h-4" />
                  {saving === 'llm' ? 'Saving...' : 'Save LLM settings'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
