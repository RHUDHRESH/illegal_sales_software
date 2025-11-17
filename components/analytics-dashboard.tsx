"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, TrendingDown, Users, Building2, Mail, Phone, Target, Zap, Clock, Award } from "lucide-react"
import { motion } from "framer-motion"

interface AnalyticsData {
  leads: {
    total: number
    hot: number
    warm: number
    nurture: number
    average_score: number
    this_week: number
    ready_to_contact: number
  }
  companies: {
    total: number
    with_website: number
    with_contacts: number
    contact_rate: number
  }
  contacts: {
    total: number
    emails: number
    phones: number
  }
  insights: {
    hot_lead_percentage: number
    weekly_velocity: number
  }
}

interface TrendData {
  daily_leads: Array<{ date: string; count: number }>
  score_trend: Array<{ date: string; average_score: number }>
  hot_lead_trend: Array<{ date: string; hot_leads: number }>
}

export default function AnalyticsDashboard() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [trends, setTrends] = useState<TrendData | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState(30)

  useEffect(() => {
    fetchAnalytics()
    fetchTrends(timeRange)
  }, [timeRange])

  const fetchAnalytics = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/analytics/overview")
      const data = await response.json()
      setAnalytics(data)
    } catch (error) {
      console.error("Error fetching analytics:", error)
    }
  }

  const fetchTrends = async (days: number) => {
    try {
      setLoading(true)
      const response = await fetch(`http://localhost:8000/api/analytics/trends?days=${days}`)
      const data = await response.json()
      setTrends(data)
    } catch (error) {
      console.error("Error fetching trends:", error)
    } finally {
      setLoading(false)
    }
  }

  if (!analytics || !trends) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
      </div>
    )
  }

  const pieData = [
    { name: 'Red Hot', value: analytics.leads.hot, color: '#ef4444' },
    { name: 'Warm', value: analytics.leads.warm, color: '#f59e0b' },
    { name: 'Nurture', value: analytics.leads.nurture, color: '#3b82f6' },
  ]

  const MetricCard = ({ icon: Icon, label, value, change, color }: any) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="p-6 bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700 hover:border-cyan-500/50 transition-all duration-300">
        <div className="flex items-start justify-between">
          <div className="space-y-2 flex-1">
            <p className="text-sm text-slate-400">{label}</p>
            <p className="text-3xl font-bold text-white">{value}</p>
            {change !== undefined && (
              <div className="flex items-center gap-1">
                {change >= 0 ? (
                  <TrendingUp className="h-4 w-4 text-green-400" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-400" />
                )}
                <span className={`text-sm ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {Math.abs(change)}% this week
                </span>
              </div>
            )}
          </div>
          <div className={`p-3 rounded-lg bg-${color}-500/10`}>
            <Icon className={`h-6 w-6 text-${color}-400`} />
          </div>
        </div>
      </Card>
    </motion.div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white">Analytics Dashboard</h2>
          <p className="text-slate-400 mt-1">Real-time insights and performance metrics</p>
        </div>
        <div className="flex gap-2">
          {[7, 30, 90].map((days) => (
            <button
              key={days}
              onClick={() => setTimeRange(days)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                timeRange === days
                  ? 'bg-cyan-500 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              {days}d
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={Target}
          label="Total Leads"
          value={analytics.leads.total}
          change={15}
          color="cyan"
        />
        <MetricCard
          icon={Zap}
          label="Hot Leads"
          value={analytics.leads.hot}
          change={23}
          color="red"
        />
        <MetricCard
          icon={Building2}
          label="Companies"
          value={analytics.companies.total}
          change={8}
          color="blue"
        />
        <MetricCard
          icon={Mail}
          label="Contacts Found"
          value={analytics.contacts.emails}
          change={12}
          color="green"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Lead Velocity Chart */}
        <Card className="p-6 bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-cyan-400" />
            Lead Velocity
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trends.daily_leads}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="date"
                stroke="#94a3b8"
                tick={{ fill: '#94a3b8', fontSize: 12 }}
                tickFormatter={(value) => {
                  const date = new Date(value)
                  return `${date.getMonth() + 1}/${date.getDate()}`
                }}
              />
              <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#06b6d4"
                strokeWidth={2}
                dot={{ fill: '#06b6d4', r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* Score Trend Chart */}
        <Card className="p-6 bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Award className="h-5 w-5 text-amber-400" />
            Average Score Trend
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trends.score_trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="date"
                stroke="#94a3b8"
                tick={{ fill: '#94a3b8', fontSize: 12 }}
                tickFormatter={(value) => {
                  const date = new Date(value)
                  return `${date.getMonth() + 1}/${date.getDate()}`
                }}
              />
              <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Line
                type="monotone"
                dataKey="average_score"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={{ fill: '#f59e0b', r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Lead Distribution Pie Chart */}
        <Card className="p-6 bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Lead Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* Hot Leads Trend */}
        <Card className="p-6 bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Zap className="h-5 w-5 text-red-400" />
            Hot Leads Over Time
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trends.hot_lead_trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="date"
                stroke="#94a3b8"
                tick={{ fill: '#94a3b8', fontSize: 12 }}
                tickFormatter={(value) => {
                  const date = new Date(value)
                  return `${date.getMonth() + 1}/${date.getDate()}`
                }}
              />
              <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Bar dataKey="hot_leads" fill="#ef4444" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Insights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6 bg-gradient-to-br from-cyan-900/20 to-cyan-950/30 border-cyan-700/50">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-cyan-500/20">
              <Clock className="h-6 w-6 text-cyan-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Weekly Velocity</p>
              <p className="text-2xl font-bold text-white">{analytics.insights.weekly_velocity}</p>
              <p className="text-xs text-cyan-400">leads/week</p>
            </div>
          </div>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-amber-900/20 to-amber-950/30 border-amber-700/50">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-amber-500/20">
              <Users className="h-6 w-6 text-amber-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Contact Rate</p>
              <p className="text-2xl font-bold text-white">{analytics.companies.contact_rate}%</p>
              <p className="text-xs text-amber-400">companies with contacts</p>
            </div>
          </div>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-green-900/20 to-green-950/30 border-green-700/50">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-green-500/20">
              <Target className="h-6 w-6 text-green-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Hot Lead Rate</p>
              <p className="text-2xl font-bold text-white">{analytics.insights.hot_lead_percentage}%</p>
              <p className="text-xs text-green-400">score 80+</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Ready to Contact CTA */}
      {analytics.leads.ready_to_contact > 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-bold text-white mb-1">Ready to Contact</h3>
              <p className="text-cyan-50">
                You have <span className="font-bold">{analytics.leads.ready_to_contact}</span> warm/hot leads waiting for outreach
              </p>
            </div>
            <button className="px-6 py-3 bg-white text-cyan-600 font-semibold rounded-lg hover:bg-cyan-50 transition-colors">
              View Leads →
            </button>
          </div>
        </motion.div>
      )}
    </div>
  )
}
