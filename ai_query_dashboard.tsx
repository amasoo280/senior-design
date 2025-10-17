import React, { useState } from 'react';
import { Search, Send, Loader2, MapPin, Package, Clock, Activity } from 'lucide-react';

// TODO: Move to config file
const EXAMPLE_QUERIES = [
  "What equipment is active at Site A?",
  "Show me all equipment deployed to Job X",
  "Which assets have been operating for more than 30 days?",
  "List equipment by location",
  "What is the status of equipment ID 12345?"
];

interface Equipment {
  id: string;
  name: string;
  location: string;
  status: string;
  daysActive: number;
}

interface QueryResult {
  query: string;
  timestamp: string;
  data: Equipment[];
  summary: string;
}

interface HistoryItem {
  query: string;
  timestamp: string;
}

const Dashboard: React.FC = () => {
  const [query, setQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [queryResults, setQueryResults] = useState<QueryResult | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  const executeQuery = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    
    // API integration placeholder
    // TODO: Replace with backend endpoint
    try {
      // const res = await fetch('/api/query', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ query })
      // });
      // const data = await res.json();
      
      // Temporary mock data for frontend testing
      setTimeout(() => {
        const mockData = {
          query: query,
          timestamp: new Date().toISOString(),
          data: [
            { id: 'EQ-001', name: 'Excavator A', location: 'Site A', status: 'Active', daysActive: 15 },
            { id: 'EQ-002', name: 'Crane B', location: 'Site A', status: 'Active', daysActive: 22 },
            { id: 'EQ-003', name: 'Loader C', location: 'Site B', status: 'Maintenance', daysActive: 0 }
          ],
          summary: `Found 3 pieces of equipment matching your query.`
        };
        
        setQueryResults(mockData);
        setHistory(prev => [{ query, timestamp: new Date().toISOString() }, ...prev.slice(0, 9)]);
        setIsLoading(false);
      }, 1500);
    } catch (err) {
      console.error('Query failed:', err);
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      executeQuery();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Top nav bar */}
      <div className="bg-slate-800/50 border-b border-slate-700 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Asset Query Dashboard</h1>
              <p className="text-slate-400 text-sm mt-1">Natural language database querying powered by AI</p>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-green-500 text-sm font-medium">System Online</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main content area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Query input section */}
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6 shadow-xl">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Search className="w-5 h-5 text-blue-400" />
                Ask a Question
              </h2>
              
              <div className="space-y-4">
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="Ask about equipment, locations, status, deployment duration..."
                  className="w-full bg-slate-900/50 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows="3"
                />
                
                <button
                  onClick={executeQuery}
                  disabled={isLoading || !query.trim()}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Processing Query...
                    </>
                  ) : (
                    <>
                      <Send className="w-5 h-5" />
                      Submit Query
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Results section */}
            {queryResults && (
              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6 shadow-xl">
                <div className="flex items-start justify-between mb-4">
                  <h2 className="text-lg font-semibold text-white">Query Results</h2>
                  <span className="text-xs text-slate-400">
                    {new Date(queryResults.timestamp).toLocaleString()}
                  </span>
                </div>
                
                <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                  <p className="text-blue-300 text-sm font-medium">{queryResults.summary}</p>
                </div>

                {/* Equipment cards */}
                <div className="space-y-3">
                  {queryResults.data.map((equipment, index) => (
                    <div
                      key={index}
                      className="bg-slate-900/50 border border-slate-600 rounded-lg p-4 hover:border-slate-500 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <Package className="w-5 h-5 text-blue-400" />
                            <h3 className="text-white font-semibold">{equipment.name}</h3>
                            <span className="text-xs text-slate-400">({equipment.id})</span>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-3 mt-3">
                            <div className="flex items-center gap-2 text-sm">
                              <MapPin className="w-4 h-4 text-slate-400" />
                              <span className="text-slate-300">{equipment.location}</span>
                            </div>
                            
                            <div className="flex items-center gap-2 text-sm">
                              <Clock className="w-4 h-4 text-slate-400" />
                              <span className="text-slate-300">{equipment.daysActive} days active</span>
                            </div>
                          </div>
                        </div>
                        
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          equipment.status === 'Active' 
                            ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                            : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                        }`}>
                          {equipment.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Stats widget */}
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6 shadow-xl">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-purple-400" />
                Quick Stats
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 text-sm">Total Equipment</span>
                  <span className="text-white font-semibold">247</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 text-sm">Active Deployments</span>
                  <span className="text-green-400 font-semibold">189</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 text-sm">Under Maintenance</span>
                  <span className="text-yellow-400 font-semibold">23</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 text-sm">Available</span>
                  <span className="text-blue-400 font-semibold">35</span>
                </div>
              </div>
            </div>

            {/* Example queries */}
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6 shadow-xl">
              <h3 className="text-lg font-semibold text-white mb-4">Sample Queries</h3>
              <div className="space-y-2">
                {EXAMPLE_QUERIES.map((example, i) => (
                  <button
                    key={i}
                    onClick={() => setQuery(example)}
                    className="w-full text-left px-3 py-2 bg-slate-900/50 hover:bg-slate-700/50 border border-slate-600 hover:border-slate-500 rounded-lg text-sm text-slate-300 hover:text-white transition-colors"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>

            {/* Query history */}
            {history.length > 0 && (
              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6 shadow-xl">
                <h3 className="text-lg font-semibold text-white mb-4">Recent Queries</h3>
                <div className="space-y-2">
                  {history.map((item, i) => (
                    <div key={i} className="text-sm text-slate-400 border-l-2 border-slate-600 pl-3 py-1">
                      {item.query}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;