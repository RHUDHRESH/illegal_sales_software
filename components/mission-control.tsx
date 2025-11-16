'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { TextShimmer } from '@/components/ui/text-shimmer';
import { Rocket, Send, Loader2, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { useMissionStore } from '@/lib/store';
import { motion, AnimatePresence } from 'framer-motion';

interface LogEntry {
  id: string;
  timestamp: Date;
  agent: string;
  message: string;
  type: 'info' | 'success' | 'error' | 'warning';
}

export function MissionControl() {
  const [input, setInput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [selectedAgent, setSelectedAgent] = useState('🚀 Founder-Finder Agent (Mission)');
  const logsEndRef = useRef<HTMLDivElement>(null);
  const { startMission, currentMission } = useMissionStore();

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  const addLog = (agent: string, message: string, type: LogEntry['type'] = 'info') => {
    setLogs((prev) => [
      ...prev,
      {
        id: `${Date.now()}-${Math.random()}`,
        timestamp: new Date(),
        agent,
        message,
        type,
      },
    ]);
  };

  const handleLaunchMission = async () => {
    if (!input.trim() || isRunning) return;

    const missionPrompt = input;
    setInput('');
    setIsRunning(true);
    setLogs([]);

    addLog('[Mission Control]', `Mission "Founder-Finder-${Date.now()}" LAUNCHED.`, 'info');
    addLog('[Search Agent]', 'Parsing ICP... Generating search queries...', 'info');

    try {
      // Simulate the agent workflow
      await simulateAgentWorkflow(missionPrompt);
    } catch (error) {
      addLog('[Mission Control]', `Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    } finally {
      setIsRunning(false);
      addLog('[Mission Control]', 'Mission COMPLETE. View results in the Dossier panel.', 'success');
    }
  };

  const simulateAgentWorkflow = async (prompt: string) => {
    // Simulate search agent
    await new Promise((resolve) => setTimeout(resolve, 1000));
    addLog('[Search Agent]', 'Querying live web... Found 15 potential domains.', 'info');

    // Simulate scraping
    await new Promise((resolve) => setTimeout(resolve, 1500));
    addLog('[Scrape Agent]', "Analyzing 'startup-blog.com/about-us'...", 'info');

    // Simulate extraction
    await new Promise((resolve) => setTimeout(resolve, 800));
    addLog('[Extraction Agent (gemma3:1b)]', 'Text sanitized. Scanning for contacts...', 'info');
    await new Promise((resolve) => setTimeout(resolve, 600));
    addLog('[Extraction Agent (gemma3:1b)]', "SUCCESS: Found email 'jane@startup-blog.com' and phone '(555) 123-4567'.", 'success');

    // Simulate another lead attempt
    await new Promise((resolve) => setTimeout(resolve, 1000));
    addLog('[Scrape Agent]', "Analyzing 'generic-news-article.com'...", 'info');
    await new Promise((resolve) => setTimeout(resolve, 800));
    addLog('[Extraction Agent (gemma3:1b)]', 'Text sanitized. Scanning for contacts...', 'info');
    await new Promise((resolve) => setTimeout(resolve, 600));
    addLog('[Extraction Agent (gemma3:1b)]', 'INFO: No direct contact info found. Discarding lead.', 'warning');

    // Simulate reasoning agent
    await new Promise((resolve) => setTimeout(resolve, 1200));
    addLog('[Reasoning Agent (gemma3:4b)]', "Lead 'jane@startup-blog.com' is valid. Synthesizing all scraped data to generate Contextual Relevance Report...", 'info');
    await new Promise((resolve) => setTimeout(resolve, 2000));
    addLog('[Reasoning Agent (gemma3:4b)]', 'Contextual Relevance Report generated successfully.', 'success');
  };

  const getLogIcon = (type: LogEntry['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'warning':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-blue-500" />;
    }
  };

  const getLogColor = (type: LogEntry['type']) => {
    switch (type) {
      case 'success':
        return 'text-green-600 dark:text-green-400';
      case 'error':
        return 'text-red-600 dark:text-red-400';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400';
      default:
        return 'text-neutral-600 dark:text-neutral-400';
    }
  };

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="border-b border-border p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Mission Control</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Launch autonomous lead generation missions
            </p>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="px-4 py-2 rounded-lg border border-border bg-background text-foreground"
            >
              <option value="gemma3:4b (Raw Reasoning)">gemma3:4b (Raw Reasoning)</option>
              <option value="gemma3:1b (Fast Tasking)">gemma3:1b (Fast Tasking)</option>
              <option value="🚀 Founder-Finder Agent (Mission)">🚀 Founder-Finder Agent (Mission)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Chat/Log Window */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {logs.length === 0 && !isRunning && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Rocket className="h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-xl font-semibold mb-2">Ready for Mission</h3>
            <p className="text-muted-foreground max-w-md">
              Describe your Ideal Customer Profile (ICP) and launch a lead generation mission.
              The system will autonomously search, scrape, extract, and qualify leads.
            </p>
          </div>
        )}

        <AnimatePresence>
          {logs.map((log) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex gap-3 items-start"
            >
              <div className="mt-1">{getLogIcon(log.type)}</div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm text-foreground">{log.agent}</span>
                  <span className="text-xs text-muted-foreground">
                    {log.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <p className={`text-sm ${getLogColor(log.type)}`}>{log.message}</p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isRunning && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <TextShimmer className="text-sm" duration={1}>
              Processing...
            </TextShimmer>
          </div>
        )}

        <div ref={logsEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-border p-6">
        <div className="flex gap-4">
          <div className="flex-1">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleLaunchMission();
                }
              }}
              placeholder="Describe the new mission. Define the Ideal Customer Profile (ICP) and the number of leads required. Example: 'Find me 10 new leads. The ICP is founder-led B2B SaaS companies in North America with 1-10 employees who have recently posted on X or LinkedIn about marketing challenges.'"
              className="w-full px-4 py-3 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary"
              rows={3}
              disabled={isRunning}
            />
          </div>
          <Button
            onClick={handleLaunchMission}
            disabled={!input.trim() || isRunning}
            size="lg"
            className="h-auto px-6"
          >
            {isRunning ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Rocket className="h-4 w-4 mr-2" />
                Launch Mission
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

