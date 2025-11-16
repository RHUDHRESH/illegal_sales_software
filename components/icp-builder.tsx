'use client';

import { useEffect, useState } from 'react';
import { Loader2, Plus, Trash2, Save } from 'lucide-react';
import { motion } from 'framer-motion';
import { listICPs, createICP, deleteICP, type ICP } from '@/lib/api';

const SIZE_BUCKETS = ['1', '2-5', '6-10', '11-20'];
const INDUSTRIES = [
  'ecommerce',
  'd2c',
  'saas',
  'consulting',
  'freelance',
  'agency',
  'coaching',
  'marketplace',
  'fintech',
  'healthtech',
];
const CHANNELS = [
  'instagram',
  'linkedin',
  'facebook',
  'google',
  'tiktok',
  'twitter',
  'email',
  'offline',
];

export default function ICPBuilder() {
  const [icps, setICPs] = useState<ICP[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedICP, setSelectedICP] = useState<ICP | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    size_buckets: [] as string[],
    industries: [] as string[],
    locations: ['india'] as string[],
    hiring_keywords: [] as string[],
    pain_keywords: [] as string[],
    channel_preferences: [] as string[],
  });

  const fetchICPs = async () => {
    setLoading(true);
    try {
      const data = await listICPs();
      setICPs(data);
    } catch (err) {
      console.error('Error fetching ICPs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchICPs();
  }, []);

  const handleSaveICP = async () => {
    if (!formData.name.trim()) {
      alert('ICP name is required');
      return;
    }

    try {
      await createICP(formData);

      // Refresh list
      await fetchICPs();

      // Reset form
      setFormData({
        name: '',
        description: '',
        size_buckets: [],
        industries: [],
        locations: ['india'],
        hiring_keywords: [],
        pain_keywords: [],
        channel_preferences: [],
      });
      setIsEditing(false);
      alert('ICP saved!');
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const toggleMultiSelect = (field: keyof typeof formData, value: string) => {
    const currentArray = formData[field] as string[];
    if (currentArray.includes(value)) {
      setFormData({
        ...formData,
        [field]: currentArray.filter((item) => item !== value),
      });
    } else {
      setFormData({
        ...formData,
        [field]: [...currentArray, value],
      });
    }
  };

  const addKeyword = (field: 'hiring_keywords' | 'pain_keywords', keyword: string) => {
    if (keyword.trim()) {
      const currentArray = formData[field];
      if (!currentArray.includes(keyword.trim())) {
        setFormData({
          ...formData,
          [field]: [...currentArray, keyword.trim()],
        });
      }
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* ICP List */}
      <div className="lg:col-span-1">
        <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
          <div className="bg-slate-900 border-b border-slate-700 p-4">
            <h2 className="text-lg font-bold text-white mb-4">📋 ICP Profiles</h2>
            <button
              onClick={() => {
                setIsEditing(true);
                setSelectedICP(null);
              }}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition-colors flex items-center justify-center gap-2"
            >
              <Plus className="h-4 w-4" />
              New Profile
            </button>
          </div>

          <div className="p-3 space-y-2 max-h-96 overflow-y-auto">
            {loading && (
              <div className="flex justify-center py-4">
                <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />
              </div>
            )}

            {icps.length === 0 && !loading && (
              <p className="text-slate-400 text-sm text-center py-4">No ICP profiles yet</p>
            )}

            {icps.map((icp, idx) => (
              <motion.button
                key={icp.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                onClick={() => {
                  setSelectedICP(icp);
                  setIsEditing(false);
                }}
                className={`w-full p-3 rounded-lg text-left transition-colors border ${
                  selectedICP?.id === icp.id
                    ? 'bg-blue-600/20 border-blue-500'
                    : 'bg-slate-700/50 border-slate-600 hover:bg-slate-700'
                }`}
              >
                <p className="font-semibold text-white text-sm truncate">{icp.name}</p>
                <p className="text-xs text-slate-400 mt-1 line-clamp-1">{icp.description}</p>
              </motion.button>
            ))}
          </div>
        </div>
      </div>

      {/* ICP Editor / Viewer */}
      <div className="lg:col-span-2">
        {isEditing ? (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-slate-800 border border-slate-700 rounded-lg p-6 space-y-4 max-h-96 overflow-y-auto"
          >
            <h3 className="text-lg font-bold text-white">
              {selectedICP ? 'Edit' : 'Create'} ICP Profile
            </h3>

            <div>
              <label className="block text-sm text-slate-300 mb-2">Profile Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none text-sm"
                placeholder="e.g., Solo Founder D2C"
              />
            </div>

            <div>
              <label className="block text-sm text-slate-300 mb-2">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 focus:outline-none text-sm resize-none"
                rows={3}
                placeholder="Who is this ICP?"
              />
            </div>

            <div>
              <label className="block text-sm text-slate-300 mb-2">Company Size</label>
              <div className="flex gap-2 flex-wrap">
                {SIZE_BUCKETS.map((size) => (
                  <button
                    key={size}
                    onClick={() => toggleMultiSelect('size_buckets', size)}
                    className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${
                      formData.size_buckets.includes(size)
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm text-slate-300 mb-2">Industries</label>
              <div className="flex gap-2 flex-wrap">
                {INDUSTRIES.map((ind) => (
                  <button
                    key={ind}
                    onClick={() => toggleMultiSelect('industries', ind)}
                    className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${
                      formData.industries.includes(ind)
                        ? 'bg-green-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {ind}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm text-slate-300 mb-2">Channels</label>
              <div className="flex gap-2 flex-wrap">
                {CHANNELS.map((ch) => (
                  <button
                    key={ch}
                    onClick={() => toggleMultiSelect('channel_preferences', ch)}
                    className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${
                      formData.channel_preferences.includes(ch)
                        ? 'bg-purple-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {ch}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-2 pt-4">
              <button
                onClick={handleSaveICP}
                className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-semibold transition-colors flex items-center justify-center gap-2"
              >
                <Save className="h-4 w-4" />
                Save Profile
              </button>
              <button
                onClick={() => {
                  setIsEditing(false);
                  setFormData({
                    name: '',
                    description: '',
                    size_buckets: [],
                    industries: [],
                    locations: ['india'],
                    hiring_keywords: [],
                    pain_keywords: [],
                    channel_preferences: [],
                  });
                }}
                className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-semibold transition-colors"
              >
                Cancel
              </button>
            </div>
          </motion.div>
        ) : selectedICP ? (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-slate-800 border border-slate-700 rounded-lg p-6 space-y-4 max-h-96 overflow-y-auto"
          >
            <h3 className="text-lg font-bold text-white">{selectedICP.name}</h3>
            <p className="text-sm text-slate-400">{selectedICP.description}</p>

            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wide">Size</p>
              <div className="flex gap-2 flex-wrap mt-2">
                {selectedICP.size_buckets.map((s) => (
                  <span key={s} className="px-2 py-1 bg-blue-600/20 text-blue-300 text-xs rounded">
                    {s}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wide">Industries</p>
              <div className="flex gap-2 flex-wrap mt-2">
                {selectedICP.industries.map((ind) => (
                  <span key={ind} className="px-2 py-1 bg-green-600/20 text-green-300 text-xs rounded">
                    {ind}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wide">Channels</p>
              <div className="flex gap-2 flex-wrap mt-2">
                {selectedICP.channel_preferences.map((ch) => (
                  <span key={ch} className="px-2 py-1 bg-purple-600/20 text-purple-300 text-xs rounded">
                    {ch}
                  </span>
                ))}
              </div>
            </div>

            <button
              onClick={() => setIsEditing(true)}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition-colors"
            >
              Edit Profile
            </button>
          </motion.div>
        ) : (
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 text-center text-slate-400">
            <p>Select or create an ICP profile</p>
          </div>
        )}
      </div>
    </div>
  );
}
