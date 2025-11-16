'use client';

import { useState } from 'react';
import { MissionControl } from '@/components/mission-control';
import { DossierPanel } from '@/components/dossier-panel';
import { SettingsPanel } from '@/components/settings-panel';
import { Sidebar, SidebarBody, SidebarLink } from '@/components/ui/sidebar';
import { 
  LayoutDashboard, 
  FileText, 
  Settings, 
  Rocket,
  Menu,
  X
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

type View = 'mission' | 'dossier' | 'settings';

export default function Home() {
  const [currentView, setCurrentView] = useState<View>('mission');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const links = [
    {
      label: 'Mission Control',
      href: '#',
      icon: <Rocket className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
      view: 'mission' as View,
    },
    {
      label: 'Dossier',
      href: '#',
      icon: <FileText className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
      view: 'dossier' as View,
    },
    {
      label: 'Settings',
      href: '#',
      icon: <Settings className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
      view: 'settings' as View,
    },
  ];

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar open={sidebarOpen} setOpen={setSidebarOpen}>
        <SidebarBody className="justify-between gap-10">
          <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center space-x-2">
                <div className="h-5 w-6 bg-black dark:bg-white rounded-br-lg rounded-tr-sm rounded-tl-lg rounded-bl-sm flex-shrink-0" />
                {sidebarOpen && (
                  <span className="font-medium text-black dark:text-white whitespace-pre">
                    Founder-Finder
                  </span>
                )}
              </div>
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden p-2"
              >
                {sidebarOpen ? (
                  <X className="h-5 w-5" />
                ) : (
                  <Menu className="h-5 w-5" />
                )}
              </button>
            </div>
            <div className="mt-8 flex flex-col gap-2 px-4">
              {links.map((link, idx) => (
                <button
                  key={idx}
                  onClick={() => setCurrentView(link.view)}
                  className={`
                    flex items-center gap-3 px-4 py-2 rounded-lg transition-colors
                    ${
                      currentView === link.view
                        ? 'bg-primary text-primary-foreground'
                        : 'text-neutral-700 dark:text-neutral-200 hover:bg-accent'
                    }
                  `}
                >
                  {link.icon}
                  {sidebarOpen && <span>{link.label}</span>}
                </button>
              ))}
            </div>
          </div>
        </SidebarBody>
      </Sidebar>

      <main className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          {currentView === 'mission' && (
            <motion.div
              key="mission"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full"
            >
              <MissionControl />
            </motion.div>
          )}
          {currentView === 'dossier' && (
            <motion.div
              key="dossier"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full"
            >
              <DossierPanel />
            </motion.div>
          )}
          {currentView === 'settings' && (
            <motion.div
              key="settings"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full"
            >
              <SettingsPanel />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

