'use client';

import { useEffect, useState } from 'react';
import { AlertCircle, Loader2, Eye, Trash2 } from 'lucide-react';
import { motion } from 'framer-motion';

interface Lead {
  id: number;
  company_id: number;
  company: {
    id: number;
    name: string;
    website?: string;
    sector?: string;
  };
  total_score: number;
  score_bucket: string;
  role_type?: string;
  pain_tags: string[];
  status: string;
  created_at: string;
  context_dossier?: string;
}

export default function LeadsList() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scoreFilter, setScoreFilter] = useState(60);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  const fetchLeads = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `http://localhost:8000/api/leads?score_min=${scoreFilter}&limit=50`,
        { headers: { 'Content-Type': 'application/json' } }
      );
      if (!response.ok) throw new Error('Failed to fetch leads');
      const data = await response.json();
      setLeads(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, [scoreFilter]);

  const getBucketColor = (bucket: string) => {
    switch (bucket) {
      case 'red_hot':
        return 'bg-red-500/20 text-red-300 border border-red-500/50';
      case 'warm':
        return 'bg-orange-500/20 text-orange-300 border border-orange-500/50';
      case 'nurture':
        return 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/50';
      default:
        return 'bg-slate-500/20 text-slate-300 border border-slate-500/50';
    }
  };

  const getBucketEmoji = (bucket: string) => {
    switch (bucket) {
      case 'red_hot':
        return '🔥';
      case 'warm':
        return '🔆';
      case 'nurture':
        return '👀';
      default:
        return '📦';
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Leads List */}
      <div className="lg:col-span-2">
        <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
          {/* Header */}
          <div className="bg-slate-900 border-b border-slate-700 p-4">
            <h2 className="text-xl font-bold text-white mb-4">🎯 Leads</h2>
            <div className="flex gap-2">
              <input
                type="range"
                min="0"
                max="100"
                value={scoreFilter}
                onChange={(e) => setScoreFilter(Number(e.target.value))}
                className="flex-1"
              />
              <span className="text-sm text-slate-400 whitespace-nowrap">
                Score: {scoreFilter}+
              </span>
            </div>
          </div>

          {/* Content */}
          <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
            {loading && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />
              </div>
            )}

            {error && (
              <div className="flex gap-2 text-red-400 text-sm p-3 bg-red-500/10 rounded">
                <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {!loading && leads.length === 0 && (
              <div className="text-center py-8 text-slate-400">
                <p>No leads found</p>
              </div>
            )}

            {leads.map((lead, idx) => (
              <motion.button
                key={lead.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                onClick={() => setSelectedLead(lead)}
                className="w-full p-3 bg-slate-700/50 hover:bg-slate-700 border border-slate-600 rounded-lg text-left transition-colors"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-white truncate">
                        {lead.company.name}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-xs ${getBucketColor(lead.score_bucket)}`}>
                        {getBucketEmoji(lead.score_bucket)} {lead.score_bucket}
                      </span>
                    </div>
                    <p className="text-sm text-slate-400 mb-2">
                      {lead.role_type ? `Role: ${lead.role_type}` : 'Unknown role'}
                    </p>
                    <div className="flex gap-1 flex-wrap">
                      {lead.pain_tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="text-xs px-2 py-1 bg-slate-600 text-slate-300 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                      {lead.pain_tags.length > 3 && (
                        <span className="text-xs px-2 py-1 text-slate-400">
                          +{lead.pain_tags.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="text-lg font-bold text-blue-400">
                      {lead.total_score.toFixed(1)}
                    </div>
                    <div className="text-xs text-slate-400">/100</div>
                  </div>
                </div>
              </motion.button>
            ))}
          </div>
        </div>
      </div>

      {/* Selected Lead Detail */}
      <div className="lg:col-span-1">
        {selectedLead ? (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-slate-800 border border-slate-700 rounded-lg p-4 sticky top-0"
          >
            <h3 className="font-bold text-white mb-4">Lead Details</h3>
            <div className="space-y-4 text-sm">
              <div>
                <p className="text-slate-400 text-xs uppercase tracking-wide">Company</p>
                <p className="text-white font-semibold">{selectedLead.company.name}</p>
                {selectedLead.company.website && (
                  <a
                    href={selectedLead.company.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:underline text-xs mt-1 block"
                  >
                    {selectedLead.company.website}
                  </a>
                )}
              </div>

              <div>
                <p className="text-slate-400 text-xs uppercase tracking-wide">Score</p>
                <p className="text-white font-semibold">{selectedLead.total_score.toFixed(1)}</p>
              </div>

              <div>
                <p className="text-slate-400 text-xs uppercase tracking-wide">Status</p>
                <select
                  value={selectedLead.status}
                  onChange={(e) => {
                    // TODO: Update lead status
                  }}
                  className="w-full mt-1 px-2 py-1 bg-slate-700 text-white rounded text-xs border border-slate-600"
                >
                  <option>new</option>
                  <option>contacted</option>
                  <option>qualified</option>
                  <option>pitched</option>
                  <option>won</option>
                  <option>lost</option>
                </select>
              </div>

              {selectedLead.context_dossier && (
                <div>
                  <p className="text-slate-400 text-xs uppercase tracking-wide">Dossier</p>
                  <p className="text-slate-300 mt-2 text-xs line-clamp-4">
                    {selectedLead.context_dossier}
                  </p>
                </div>
              )}

              <div className="flex gap-2 pt-4">
                <button className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold transition-colors">
                  <Eye className="h-3 w-3 inline mr-1" />
                  View
                </button>
                <button className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-xs font-semibold transition-colors">
                  <Trash2 className="h-3 w-3 inline mr-1" />
                  Delete
                </button>
              </div>
            </div>
          </motion.div>
        ) : (
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 text-center text-slate-400">
            <p className="text-sm">Select a lead to view details</p>
          </div>
        )}
      </div>
    </div>
  );
}
