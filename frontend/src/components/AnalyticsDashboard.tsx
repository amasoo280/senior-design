import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, RefreshCw, TrendingUp, AlertCircle, Database, MessageSquare, Clock, CheckCircle, Users, List, Shield, FileText, Save } from 'lucide-react';
import { API_ENDPOINTS } from '../config';
import { getAuthHeaders } from '../utils/auth';

interface AdminConfig {
  guardrails: {
    allowed_tenant_ids: string[];
    dangerous_keywords: string[];
    sql_injection_patterns: string[];
    tenant_column: string;
  };
  prompt_template: string;
}

interface RecentRequest {
  request_id: string;
  tenant_id: string;
  query: string;
  timestamp: string;
  success: boolean;
}

interface AnalyticsData {
  summary: {
    total_requests: number;
    total_errors: number;
    total_sql_queries: number;
    total_chat_responses: number;
    total_clarification_responses: number;
    success_rate: number;
    uptime_hours: number;
  };
  errors: {
    by_type: Record<string, number>;
    total: number;
  };
  performance: {
    avg_query_execution_time_ms: number;
    avg_bedrock_call_time_ms: number;
    query_execution_samples: number;
    bedrock_call_samples: number;
  };
  hourly: Array<{
    hour: number;
    requests: number;
    errors: number;
  }>;
  timestamp: string;
  recent_requests?: RecentRequest[];
  requests_by_tenant?: Record<string, number>;
}

const AnalyticsDashboard: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(false);
  const [adminConfig, setAdminConfig] = useState<AdminConfig | null>(null);
  const [adminConfigLoading, setAdminConfigLoading] = useState<boolean>(true);
  const [adminConfigSaving, setAdminConfigSaving] = useState<boolean>(false);
  const [adminSaveMessage, setAdminSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchAnalytics = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(API_ENDPOINTS.analytics, {
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error('Failed to fetch analytics');
      }
      const analyticsData = await response.json();
      setData(analyticsData);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchAnalytics, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchAdminConfig = async () => {
    try {
      setAdminConfigLoading(true);
      const response = await fetch(API_ENDPOINTS.adminConfig, { headers: getAuthHeaders() });
      if (!response.ok) throw new Error('Failed to fetch config');
      const config = await response.json();
      setAdminConfig(config);
    } catch (e) {
      console.error('Error fetching admin config:', e);
      setAdminConfig(null);
    } finally {
      setAdminConfigLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminConfig();
  }, []);

  const handleSaveAdminConfig = async () => {
    if (!adminConfig) return;
    setAdminSaveMessage(null);
    setAdminConfigSaving(true);
    try {
      const response = await fetch(API_ENDPOINTS.adminConfig, {
        method: 'POST',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          guardrails: adminConfig.guardrails,
          prompt_template: adminConfig.prompt_template,
        }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        setAdminSaveMessage({ type: 'error', text: result.detail || 'Failed to save config' });
        return;
      }
      setAdminSaveMessage({ type: 'success', text: 'Config saved. New queries will use these settings.' });
    } catch (e) {
      setAdminSaveMessage({ type: 'error', text: 'Failed to save config' });
    } finally {
      setAdminConfigSaving(false);
    }
  };

  if (isLoading && !data) {
    return (
      <div className="min-h-screen bg-[#0f0f23] flex items-center justify-center">
        <div className="text-slate-400">Loading admin dashboard...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-[#0f0f23] flex flex-col items-center justify-center gap-4 p-4">
        <div className="text-red-400">Failed to load admin dashboard</div>
        <Link to="/" className="text-blue-400 hover:text-blue-300 flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>
      </div>
    );
  }

  const { summary, errors, performance, hourly, recent_requests = [], requests_by_tenant = {} } = data;

  return (
    <div className="min-h-screen bg-[#0f0f23] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700 shrink-0">
        <div className="flex items-center gap-4">
          <Link
            to="/"
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to Dashboard</span>
          </Link>
          <h1 className="text-xl font-semibold text-white">Admin Dashboard</h1>
        </div>
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
            onClick={fetchAnalytics}
            disabled={isLoading}
            className="px-3 py-1.5 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 inline mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 max-w-6xl w-full mx-auto">
          {/* Guardrails & Prompts (admin-editable) */}
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mb-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-amber-400" />
              Guardrails & Prompts
            </h3>
            <p className="text-slate-400 text-sm mb-4">
              Changes apply after you click Save. New queries will use the updated config (no per-query refresh).
            </p>
            {adminConfigLoading && !adminConfig ? (
              <div className="text-slate-500 text-sm">Loading config...</div>
            ) : adminConfig ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">Allowed tenant IDs (one per line)</label>
                    <textarea
                      value={adminConfig.guardrails.allowed_tenant_ids.join('\n')}
                      onChange={(e) => setAdminConfig({
                        ...adminConfig,
                        guardrails: {
                          ...adminConfig.guardrails,
                          allowed_tenant_ids: e.target.value.split('\n').map(s => s.trim()).filter(Boolean),
                        },
                      })}
                      rows={3}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white text-sm font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">Dangerous keywords (one per line)</label>
                    <textarea
                      value={adminConfig.guardrails.dangerous_keywords.join('\n')}
                      onChange={(e) => setAdminConfig({
                        ...adminConfig,
                        guardrails: {
                          ...adminConfig.guardrails,
                          dangerous_keywords: e.target.value.split('\n').map(s => s.trim()).filter(Boolean),
                        },
                      })}
                      rows={3}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white text-sm font-mono"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">SQL injection patterns (one regex per line)</label>
                  <textarea
                    value={adminConfig.guardrails.sql_injection_patterns.join('\n')}
                    onChange={(e) => setAdminConfig({
                      ...adminConfig,
                      guardrails: {
                        ...adminConfig.guardrails,
                        sql_injection_patterns: e.target.value.split('\n').map(s => s.trim()).filter(Boolean),
                      },
                    })}
                    rows={2}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white text-sm font-mono"
                  />
                </div>
                <div className="max-w-xs">
                  <label className="block text-sm font-medium text-slate-300 mb-1">Tenant column name</label>
                  <input
                    type="text"
                    value={adminConfig.guardrails.tenant_column}
                    onChange={(e) => setAdminConfig({
                      ...adminConfig,
                      guardrails: { ...adminConfig.guardrails, tenant_column: e.target.value },
                    })}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white text-sm font-mono"
                  />
                </div>
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-1">
                    <FileText className="w-4 h-4" />
                    Prompt template (use {'{schema_context}'}, {'{tenant_id}'}, {'{natural_language_query}'})
                  </label>
                  <textarea
                    value={adminConfig.prompt_template}
                    onChange={(e) => setAdminConfig({ ...adminConfig, prompt_template: e.target.value })}
                    rows={14}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white text-sm font-mono"
                  />
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={handleSaveAdminConfig}
                    disabled={adminConfigSaving}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded-lg font-medium"
                  >
                    <Save className="w-4 h-4" />
                    {adminConfigSaving ? 'Saving...' : 'Save'}
                  </button>
                  {adminSaveMessage && (
                    <span className={adminSaveMessage.type === 'success' ? 'text-green-400 text-sm' : 'text-red-400 text-sm'}>
                      {adminSaveMessage.text}
                    </span>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-slate-500 text-sm">Could not load config.</div>
            )}
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
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

          {/* Requests by tenant (who has how many) */}
          {Object.keys(requests_by_tenant).length > 0 && (
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mb-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Users className="w-5 h-5 text-cyan-400" />
                Requests by Tenant
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-400 border-b border-slate-600">
                      <th className="pb-2 pr-4">Tenant ID</th>
                      <th className="pb-2 text-right">Requests</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(requests_by_tenant).map(([tenantId, count]) => (
                      <tr key={tenantId} className="border-b border-slate-700/50">
                        <td className="py-2 pr-4 text-slate-300 font-mono text-xs truncate max-w-[200px]" title={tenantId}>
                          {tenantId}
                        </td>
                        <td className="py-2 text-right text-white font-semibold">{count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Recent activity: who asked what */}
          {recent_requests.length > 0 && (
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mb-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <List className="w-5 h-5 text-amber-400" />
                Recent Activity (Who Asked What)
              </h3>
              <div className="overflow-x-auto max-h-64 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-slate-800">
                    <tr className="text-left text-slate-400 border-b border-slate-600">
                      <th className="pb-2 pr-2 w-28">Time</th>
                      <th className="pb-2 pr-2 w-44">Tenant</th>
                      <th className="pb-2 pr-2">Query</th>
                      <th className="pb-2 w-20 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recent_requests.map((req) => (
                      <tr key={req.request_id} className="border-b border-slate-700/50">
                        <td className="py-1.5 pr-2 text-slate-400 text-xs whitespace-nowrap">
                          {new Date(req.timestamp).toLocaleTimeString()}
                        </td>
                        <td className="py-1.5 pr-2 text-slate-300 font-mono text-xs truncate max-w-[11rem]" title={req.tenant_id}>
                          {req.tenant_id}
                        </td>
                        <td className="py-1.5 pr-2 text-slate-300 text-xs max-w-md truncate" title={req.query}>
                          {req.query}
                        </td>
                        <td className="py-1.5 text-center">
                          {req.success ? (
                            <span className="text-green-400 text-xs">OK</span>
                          ) : (
                            <span className="text-red-400 text-xs">Failed</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Activity Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
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

          {/* Performance Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">Performance Metrics</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Avg Query Execution</span>
                  <span className="text-white font-semibold">
                    {performance.avg_query_execution_time_ms.toFixed(2)} ms
                  </span>
                </div>
                <div className="text-xs text-slate-500">
                  Based on {performance.query_execution_samples} samples
                </div>
                <div className="flex justify-between items-center mt-4">
                  <span className="text-slate-400">Avg Bedrock Call</span>
                  <span className="text-white font-semibold">
                    {performance.avg_bedrock_call_time_ms.toFixed(2)} ms
                  </span>
                </div>
                <div className="text-xs text-slate-500">
                  Based on {performance.bedrock_call_samples} samples
                </div>
              </div>
            </div>

            {/* Error Breakdown */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">Error Breakdown</h3>
              {Object.keys(errors.by_type).length === 0 ? (
                <div className="text-slate-500 text-sm">No errors recorded</div>
              ) : (
                <div className="space-y-2">
                  {Object.entries(errors.by_type)
                    .sort(([, a], [, b]) => b - a)
                    .map(([errorType, count]) => (
                      <div key={errorType} className="flex justify-between items-center">
                        <span className="text-slate-400 text-sm capitalize">
                          {errorType.replace(/_/g, ' ')}
                        </span>
                        <span className="text-red-400 font-semibold">{count}</span>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>

          {/* Hourly Activity Chart */}
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-4">Hourly Activity (Last 24 Hours)</h3>
            <div className="space-y-2">
              {hourly.map((hourData, index) => {
                const maxRequests = Math.max(...hourly.map(h => h.requests), 1);
                const requestWidth = (hourData.requests / maxRequests) * 100;
                const errorWidth = hourData.requests > 0 
                  ? (hourData.errors / hourData.requests) * 100 
                  : 0;

                return (
                  <div key={index} className="flex items-center gap-4">
                    <div className="w-16 text-xs text-slate-400 text-right">
                      {hourData.hour.toString().padStart(2, '0')}:00
                    </div>
                    <div className="flex-1 relative">
                      <div className="h-6 bg-slate-700 rounded relative overflow-hidden">
                        <div
                          className="h-full bg-blue-500/50 rounded"
                          style={{ width: `${requestWidth}%` }}
                        />
                        {hourData.errors > 0 && (
                          <div
                            className="h-full bg-red-500/70 rounded absolute top-0 right-0"
                            style={{ width: `${errorWidth}%` }}
                          />
                        )}
                      </div>
                    </div>
                    <div className="w-20 text-xs text-slate-400 text-right">
                      {hourData.requests} req
                      {hourData.errors > 0 && (
                        <span className="text-red-400 ml-1">({hourData.errors} err)</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        {/* Last Updated */}
        <div className="text-xs text-slate-500 mt-4 text-center">
          Last updated: {new Date(data.timestamp).toLocaleString()}
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;


