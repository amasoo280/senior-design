import React, { useState, useEffect } from 'react';
import { X, RefreshCw, TrendingUp, AlertCircle, Database, MessageSquare, Clock, CheckCircle } from 'lucide-react';
import { API_ENDPOINTS } from '../config';

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
}

interface AnalyticsDashboardProps {
  onClose: () => void;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ onClose }) => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(false);

  const fetchAnalytics = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(API_ENDPOINTS.analytics);
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

  if (isLoading && !data) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-[#0f0f23] border border-slate-700 rounded-xl p-8">
          <div className="text-slate-400">Loading analytics...</div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-[#0f0f23] border border-slate-700 rounded-xl p-8">
          <div className="text-red-400">Failed to load analytics</div>
        </div>
      </div>
    );
  }

  const { summary, errors, performance, hourly } = data;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-[#0f0f23] border border-slate-700 rounded-xl w-full max-w-6xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <h2 className="text-xl font-semibold text-white">Analytics Dashboard</h2>
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
            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
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
    </div>
  );
};

export default AnalyticsDashboard;


