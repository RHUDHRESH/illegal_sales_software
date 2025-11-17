"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Clock, Zap, Webhook, Trash2, Plus, Play, Pause, CheckCircle2, XCircle, Slack } from "lucide-react"
import toast from "react-hot-toast"
import { motion } from "framer-motion"

interface ScheduledJob {
  id: string
  type: string
  schedule: string
  next_run: string | null
  created_at: string
}

interface WebhookConfig {
  id: string
  url: string
  events: string[]
  enabled: boolean
  created_at: string
}

export default function AutomationCenter() {
  const [jobs, setJobs] = useState<ScheduledJob[]>([])
  const [webhooks, setWebhooks] = useState<WebhookConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<"jobs" | "webhooks">("jobs")

  // Job form state
  const [jobQuery, setJobQuery] = useState("")
  const [jobHour, setJobHour] = useState(9)
  const [jobMinute, setJobMinute] = useState(0)

  // Webhook form state
  const [webhookUrl, setWebhookUrl] = useState("")
  const [webhookEvents, setWebhookEvents] = useState<string[]>(["lead.hot"])

  useEffect(() => {
    fetchJobs()
    fetchWebhooks()
  }, [])

  const fetchJobs = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/automation/schedule/jobs")
      const data = await response.json()
      setJobs(data.jobs || [])
    } catch (error) {
      console.error("Error fetching jobs:", error)
    } finally {
      setLoading(false)
    }
  }

  const fetchWebhooks = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/automation/webhooks")
      const data = await response.json()
      setWebhooks(data.webhooks || [])
    } catch (error) {
      console.error("Error fetching webhooks:", error)
    }
  }

  const scheduleJob = async () => {
    if (!jobQuery) {
      toast.error("Please enter a search query")
      return
    }

    try {
      const response = await fetch("http://localhost:8000/api/automation/schedule/job-scrape", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: `job_${Date.now()}`,
          query: jobQuery,
          sources: ["indeed", "naukri"],
          hour: jobHour,
          minute: jobMinute
        })
      })

      if (response.ok) {
        toast.success("Job scheduled successfully!")
        setJobQuery("")
        fetchJobs()
      } else {
        toast.error("Failed to schedule job")
      }
    } catch (error) {
      toast.error("Error scheduling job")
    }
  }

  const deleteJob = async (jobId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/automation/schedule/jobs/${jobId}`, {
        method: "DELETE"
      })

      if (response.ok) {
        toast.success("Job deleted")
        fetchJobs()
      } else {
        toast.error("Failed to delete job")
      }
    } catch (error) {
      toast.error("Error deleting job")
    }
  }

  const addWebhook = async () => {
    if (!webhookUrl) {
      toast.error("Please enter webhook URL")
      return
    }

    try {
      const response = await fetch("http://localhost:8000/api/automation/webhooks/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          webhook_id: `webhook_${Date.now()}`,
          url: webhookUrl,
          events: webhookEvents
        })
      })

      if (response.ok) {
        toast.success("Webhook registered!")
        setWebhookUrl("")
        fetchWebhooks()
      } else {
        toast.error("Failed to register webhook")
      }
    } catch (error) {
      toast.error("Error registering webhook")
    }
  }

  const addSlackWebhook = async (url: string) => {
    try {
      const response = await fetch("http://localhost:8000/api/automation/integrations/slack", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          webhook_url: url,
          events: ["lead.hot", "lead.created"]
        })
      })

      if (response.ok) {
        toast.success("🎉 Slack integration added!")
        fetchWebhooks()
      } else {
        toast.error("Failed to add Slack integration")
      }
    } catch (error) {
      toast.error("Error adding Slack")
    }
  }

  const deleteWebhook = async (webhookId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/automation/webhooks/${webhookId}`, {
        method: "DELETE"
      })

      if (response.ok) {
        toast.success("Webhook deleted")
        fetchWebhooks()
      } else {
        toast.error("Failed to delete webhook")
      }
    } catch (error) {
      toast.error("Error deleting webhook")
    }
  }

  const eventTypes = [
    { value: "lead.created", label: "Lead Created" },
    { value: "lead.hot", label: "Hot Lead (80+)" },
    { value: "lead.updated", label: "Lead Updated" },
    { value: "lead.status_changed", label: "Status Changed" },
    { value: "company.enriched", label: "Company Enriched" },
    { value: "scraping.completed", label: "Scraping Done" }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-white">Automation Center</h2>
        <p className="text-slate-400 mt-1">Schedule jobs and configure integrations</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-700">
        <button
          onClick={() => setActiveTab("jobs")}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === "jobs"
              ? "text-cyan-400 border-b-2 border-cyan-400"
              : "text-slate-400 hover:text-slate-300"
          }`}
        >
          <Clock className="inline h-4 w-4 mr-2" />
          Scheduled Jobs
        </button>
        <button
          onClick={() => setActiveTab("webhooks")}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === "webhooks"
              ? "text-cyan-400 border-b-2 border-cyan-400"
              : "text-slate-400 hover:text-slate-300"
          }`}
        >
          <Webhook className="inline h-4 w-4 mr-2" />
          Webhooks & Integrations
        </button>
      </div>

      {/* Scheduled Jobs Tab */}
      {activeTab === "jobs" && (
        <div className="space-y-6">
          {/* Add Job Form */}
          <Card className="p-6 bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Plus className="h-5 w-5 text-cyan-400" />
              Schedule Daily Job Scraping
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="md:col-span-2">
                <Label htmlFor="job-query" className="text-slate-300">Search Query</Label>
                <Input
                  id="job-query"
                  placeholder="e.g., marketing manager"
                  value={jobQuery}
                  onChange={(e) => setJobQuery(e.target.value)}
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>
              <div>
                <Label htmlFor="job-hour" className="text-slate-300">Hour (24h)</Label>
                <Input
                  id="job-hour"
                  type="number"
                  min={0}
                  max={23}
                  value={jobHour}
                  onChange={(e) => setJobHour(parseInt(e.target.value))}
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>
              <div>
                <Label htmlFor="job-minute" className="text-slate-300">Minute</Label>
                <Input
                  id="job-minute"
                  type="number"
                  min={0}
                  max={59}
                  value={jobMinute}
                  onChange={(e) => setJobMinute(parseInt(e.target.value))}
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>
            </div>
            <Button
              onClick={scheduleJob}
              className="mt-4 bg-cyan-600 hover:bg-cyan-700"
            >
              <Clock className="h-4 w-4 mr-2" />
              Schedule Job
            </Button>
          </Card>

          {/* Jobs List */}
          <div className="space-y-3">
            {jobs.length === 0 ? (
              <Card className="p-8 bg-slate-800/50 border-slate-700 text-center">
                <Clock className="h-12 w-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400">No scheduled jobs yet</p>
                <p className="text-sm text-slate-500 mt-1">Create your first automation above</p>
              </Card>
            ) : (
              jobs.map((job, index) => (
                <motion.div
                  key={job.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="p-4 bg-slate-800 border-slate-700 hover:border-cyan-500/50 transition-all">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Badge variant="outline" className="bg-cyan-500/10 text-cyan-400 border-cyan-500/30">
                            {job.type}
                          </Badge>
                          <code className="text-sm text-slate-400">{job.id}</code>
                        </div>
                        <p className="text-white font-medium">{job.schedule}</p>
                        {job.next_run && (
                          <p className="text-sm text-slate-400 mt-1">
                            Next run: {new Date(job.next_run).toLocaleString()}
                          </p>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteJob(job.id)}
                        className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </Card>
                </motion.div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Webhooks Tab */}
      {activeTab === "webhooks" && (
        <div className="space-y-6">
          {/* Quick Integration */}
          <Card className="p-6 bg-gradient-to-br from-purple-900/20 to-purple-950/30 border-purple-700/50">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Slack className="h-5 w-5 text-purple-400" />
              Quick Integrations
            </h3>
            <p className="text-slate-300 mb-4">
              Get notified instantly when hot leads are discovered
            </p>
            <div className="flex gap-4">
              <Input
                placeholder="https://hooks.slack.com/services/..."
                className="flex-1 bg-slate-700 border-slate-600 text-white"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    addSlackWebhook((e.target as HTMLInputElement).value)
                    ;(e.target as HTMLInputElement).value = ''
                  }
                }}
              />
              <Button className="bg-purple-600 hover:bg-purple-700">
                <Slack className="h-4 w-4 mr-2" />
                Add Slack
              </Button>
            </div>
            <p className="text-xs text-slate-500 mt-2">
              Get your Slack webhook URL from{" "}
              <a href="https://api.slack.com/messaging/webhooks" target="_blank" className="text-purple-400 hover:underline">
                api.slack.com/messaging/webhooks
              </a>
            </p>
          </Card>

          {/* Custom Webhook Form */}
          <Card className="p-6 bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Plus className="h-5 w-5 text-cyan-400" />
              Add Custom Webhook
            </h3>
            <div className="space-y-4">
              <div>
                <Label htmlFor="webhook-url" className="text-slate-300">Webhook URL</Label>
                <Input
                  id="webhook-url"
                  placeholder="https://your-service.com/webhook"
                  value={webhookUrl}
                  onChange={(e) => setWebhookUrl(e.target.value)}
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>
              <div>
                <Label className="text-slate-300 mb-2 block">Events to Subscribe</Label>
                <div className="grid grid-cols-2 gap-2">
                  {eventTypes.map((event) => (
                    <label key={event.value} className="flex items-center gap-2 p-2 rounded bg-slate-700/50 cursor-pointer hover:bg-slate-700">
                      <input
                        type="checkbox"
                        checked={webhookEvents.includes(event.value)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setWebhookEvents([...webhookEvents, event.value])
                          } else {
                            setWebhookEvents(webhookEvents.filter(ev => ev !== event.value))
                          }
                        }}
                        className="rounded border-slate-600"
                      />
                      <span className="text-sm text-slate-300">{event.label}</span>
                    </label>
                  ))}
                </div>
              </div>
              <Button
                onClick={addWebhook}
                className="w-full bg-cyan-600 hover:bg-cyan-700"
              >
                <Webhook className="h-4 w-4 mr-2" />
                Register Webhook
              </Button>
            </div>
          </Card>

          {/* Webhooks List */}
          <div className="space-y-3">
            {webhooks.length === 0 ? (
              <Card className="p-8 bg-slate-800/50 border-slate-700 text-center">
                <Webhook className="h-12 w-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400">No webhooks configured</p>
                <p className="text-sm text-slate-500 mt-1">Add your first integration above</p>
              </Card>
            ) : (
              webhooks.map((webhook, index) => (
                <motion.div
                  key={webhook.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="p-4 bg-slate-800 border-slate-700 hover:border-cyan-500/50 transition-all">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/30">
                            {webhook.enabled ? 'Active' : 'Disabled'}
                          </Badge>
                          <code className="text-xs text-slate-400">{webhook.id}</code>
                        </div>
                        <p className="text-white font-mono text-sm break-all">{webhook.url}</p>
                        <div className="flex gap-2 mt-2 flex-wrap">
                          {webhook.events.map((event) => (
                            <Badge key={event} variant="secondary" className="text-xs">
                              {event}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteWebhook(webhook.id)}
                        className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </Card>
                </motion.div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
