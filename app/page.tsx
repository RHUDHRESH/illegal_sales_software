'use client';

import { useEffect, useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Dashboard from '@/components/dashboard';
import LeadsList from '@/components/leads-list';
import ICPBuilder from '@/components/icp-builder';
import OCRUploader from '@/components/ocr-uploader';
import { WebScraper } from '@/components/web-scraper';

const tabs = [
  { id: 'dashboard', label: '📊 Dashboard' },
  { id: 'leads', label: '🎯 Leads' },
  { id: 'scraper', label: '🕷️ Web Scraper' },
  { id: 'icp', label: '🎨 ICP Whiteboard' },
  { id: 'ingest', label: '📸 OCR Ingest' },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [backendReady, setBackendReady] = useState(false);

  useEffect(() => {
    // Check if backend is available
    fetch('http://localhost:8000/health', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })
      .then((res) => {
        if (res.ok) setBackendReady(true);
      })
      .catch(() => {
        console.warn('Backend not available at localhost:8000');
      });
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-black">
      {/* Header */}
      <div className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
                🚀 Raptorflow Lead Engine
              </h1>
              <p className="text-sm text-slate-400 mt-1">
                Hunt people with marketing pain. Get context. Close them.
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-slate-500">Ollama-powered • Local only</p>
              <div className="mt-1">
                {backendReady ? (
                  <span className="inline-flex items-center gap-2 text-xs px-2 py-1 bg-green-500/20 text-green-300 rounded">
                    <span className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                    Backend Ready
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-2 text-xs px-2 py-1 bg-red-500/20 text-red-300 rounded">
                    <span className="h-2 w-2 bg-red-500 rounded-full animate-pulse" />
                    Backend Offline
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5 bg-slate-800 border border-slate-700 mb-6">
            {tabs.map((tab) => (
              <TabsTrigger key={tab.id} value={tab.id} className="text-sm">
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value="dashboard" className="mt-0">
            <Dashboard />
          </TabsContent>

          <TabsContent value="leads" className="mt-0">
            <LeadsList />
          </TabsContent>

          <TabsContent value="scraper" className="mt-0">
            <WebScraper />
          </TabsContent>

          <TabsContent value="icp" className="mt-0">
            <ICPBuilder />
          </TabsContent>

          <TabsContent value="ingest" className="mt-0">
            <OCRUploader />
          </TabsContent>
        </Tabs>
      </div>

      {/* Footer */}
      <div className="border-t border-slate-700 bg-slate-900/50 backdrop-blur-sm mt-16">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <p className="text-xs text-slate-500 text-center">
            Raptorflow Lead Engine • Local Ollama (Gemma 3 1B/4B) • No external data transfers
          </p>
        </div>
      </div>
    </div>
  );
}

