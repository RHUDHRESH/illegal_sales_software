import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Lead {
  id: string;
  name: string;
  title: string;
  company: string;
  email: string | null;
  phone: string | null;
  url: string;
  report: string;
  createdAt: Date;
}

export interface Mission {
  id: string;
  icp: string;
  status: 'running' | 'completed' | 'failed';
  leadsFound: number;
  startedAt: Date;
  completedAt?: Date;
}

interface MissionStore {
  leads: Lead[];
  missions: Mission[];
  currentMission: Mission | null;
  settings: {
    ollamaUrl: string;
    n8nWebhookUrl: string;
    fastModel: string;
    reasoningModel: string;
    icp: string;
    raptorFlowFeatures: string;
  };
  addLead: (lead: Lead) => void;
  addMission: (mission: Mission) => void;
  updateMission: (id: string, updates: Partial<Mission>) => void;
  setCurrentMission: (mission: Mission | null) => void;
  startMission: (icp: string) => Mission;
  updateSettings: (settings: Partial<MissionStore['settings']>) => void;
  deleteLead: (id: string) => void;
}

export const useMissionStore = create<MissionStore>()(
  persist(
    (set) => ({
      leads: [],
      missions: [],
      currentMission: null,
      settings: {
        ollamaUrl: 'http://localhost:11434',
        n8nWebhookUrl: 'http://localhost:5678/webhook/my-sdr-mission',
        fastModel: 'gemma3:1b',
        reasoningModel: 'gemma3:4b',
        icp: 'Founder-led B2B SaaS companies with 1-20 employees who are actively posting about marketing challenges or growth hacking.',
        raptorFlowFeatures: `1. Multi-agent architecture: Automates strategy, research, and content.
2. Conversational onboarding: Extracts founder stories to build strategy.
3. Visual ICP Creator: Gamified persona building.
4. "Move System": Turns objectives into step-by-step action plans.
5. Visual Asset Factory: Bulk-brands assets with Canva API.
6. Automation & Distribution: Integrates with LinkedIn, X, email.`,
      },
      addLead: (lead) =>
        set((state) => ({
          leads: [...state.leads, lead],
        })),
      addMission: (mission) =>
        set((state) => ({
          missions: [mission, ...state.missions],
        })),
      updateMission: (id, updates) =>
        set((state) => ({
          missions: state.missions.map((m) =>
            m.id === id ? { ...m, ...updates } : m
          ),
        })),
      setCurrentMission: (mission) => set({ currentMission: mission }),
      startMission: (icp) => {
        const mission: Mission = {
          id: `mission-${Date.now()}`,
          icp,
          status: 'running',
          leadsFound: 0,
          startedAt: new Date(),
        };
        set((state) => ({
          missions: [mission, ...state.missions],
          currentMission: mission,
        }));
        return mission;
      },
      updateSettings: (newSettings) =>
        set((state) => ({
          settings: { ...state.settings, ...newSettings },
        })),
      deleteLead: (id) =>
        set((state) => ({
          leads: state.leads.filter((lead) => lead.id !== id),
        })),
    }),
    {
      name: 'founder-finder-storage',
    }
  )
);

