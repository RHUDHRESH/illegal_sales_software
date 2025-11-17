'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Target,
  Sparkles,
  Database,
  Scan,
  Zap,
  Download,
  BarChart3,
  Settings,
  Circle
} from 'lucide-react';

import { ToastProvider } from '@/components/toast-provider';
import Dashboard from '@/components/dashboard';
import LeadsList from '@/components/leads-list';
import ICPBuilder from '@/components/icp-builder';
import OCRUploader from '@/components/ocr-uploader';
import { WebScraper } from '@/components/web-scraper';
import EnrichmentCenter from '@/components/enrichment-center';
import ExportCenter from '@/components/export-center';
import AutomationCenter from '@/components/automation-center';
import AnalyticsDashboard from '@/components/analytics-dashboard';

type TabId = 'dashboard' | 'analytics' | 'leads' | 'scraper' | 'enrichment' | 'automation' | 'export' | 'icp' | 'ingest';

interface NavItem {
  id: TabId;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Overview', icon: LayoutDashboard, description: 'Quick stats' },
  { id: 'analytics', label: 'Analytics', icon: BarChart3, description: 'Insights & trends' },
  { id: 'leads', label: 'Leads', icon: Target, description: 'Manage leads' },
  { id: 'scraper', label: 'Web Scraper', icon: Scan, description: 'Collect leads' },
  { id: 'enrichment', label: 'Enrichment', icon: Sparkles, description: 'Find contacts' },
  { id: 'automation', label: 'Automation', icon: Zap, description: 'Jobs & webhooks' },
  { id: 'export', label: 'Export', icon: Download, description: 'Download leads' },
  { id: 'icp', label: 'ICP Builder', icon: Database, description: 'Define ICPs' },
  { id: 'ingest', label: 'OCR Ingest', icon: Settings, description: 'Upload files' },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabId>('dashboard');
  const [backendReady, setBackendReady] = useState(false);

  useEffect(() => {
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
    <>
      <ToastProvider />
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        {/* Header */}
        <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-[1800px] mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center">
                  <Target className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400">
                    Raptorflow Lead Engine
                  </h1>
                  <p className="text-xs text-slate-500">
                    Enterprise-Grade Lead Intelligence Platform
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-xs text-slate-500">Backend Status</p>
                  <div className="flex items-center gap-2 mt-1">
                    {backendReady ? (
                      <>
                        <Circle className="h-2 w-2 fill-green-500 text-green-500 animate-pulse" />
                        <span className="text-xs text-green-400 font-medium">Online</span>
                      </>
                    ) : (
                      <>
                        <Circle className="h-2 w-2 fill-red-500 text-red-500 animate-pulse" />
                        <span className="text-xs text-red-400 font-medium">Offline</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <div className="flex max-w-[1800px] mx-auto">
          {/* Sidebar Navigation */}
          <nav className="w-64 border-r border-slate-800 bg-slate-900/50 min-h-[calc(100vh-73px)] p-4">
            <div className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;

                return (
                  <motion.button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                      isActive
                        ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-500/20'
                        : 'text-slate-400 hover:text-white hover:bg-slate-800'
                    }`}
                    whileHover={{ x: 4 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Icon className={`h-5 w-5 ${isActive ? 'text-white' : ''}`} />
                    <div className="flex-1 text-left">
                      <div className={`text-sm font-medium ${isActive ? 'text-white' : ''}`}>
                        {item.label}
                      </div>
                      <div className={`text-xs ${isActive ? 'text-cyan-100' : 'text-slate-500'}`}>
                        {item.description}
                      </div>
                    </div>
                  </motion.button>
                );
              })}
            </div>

            {/* Footer Stats */}
            <div className="mt-8 pt-6 border-t border-slate-800">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">Version</span>
                  <span className="text-slate-400 font-mono">2.0.0</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">Status</span>
                  <span className="text-green-400">All systems go</span>
                </div>
              </div>
            </div>
          </nav>

          {/* Content Area */}
          <main className="flex-1 p-8 overflow-auto" style={{ maxHeight: 'calc(100vh - 73px)' }}>
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {activeTab === 'dashboard' && <Dashboard />}
              {activeTab === 'analytics' && <AnalyticsDashboard />}
              {activeTab === 'leads' && <LeadsList />}
              {activeTab === 'scraper' && <WebScraper />}
              {activeTab === 'enrichment' && <EnrichmentCenter />}
              {activeTab === 'automation' && <AutomationCenter />}
              {activeTab === 'export' && <ExportCenter />}
              {activeTab === 'icp' && <ICPBuilder />}
              {activeTab === 'ingest' && <OCRUploader />}
            </motion.div>
          </main>
        </div>
      </div>
    </>
  );
}
