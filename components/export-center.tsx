"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { FileText, FileSpreadsheet, FileJson, FileType, Download, Filter, Loader2 } from "lucide-react"
import toast from "react-hot-toast"
import { motion } from "framer-motion"

export default function ExportCenter() {
  const [exporting, setExporting] = useState(false)
  const [scoreMin, setScoreMin] = useState(60)
  const [scoreBucket, setScoreBucket] = useState<string | null>(null)
  const [includeDossier, setIncludeDossier] = useState(true)

  const exportLeads = async (format: string) => {
    setExporting(true)
    toast.loading(`Exporting to ${format.toUpperCase()}...`)

    try {
      const params = new URLSearchParams()
      params.append("score_min", scoreMin.toString())
      if (scoreBucket) params.append("score_bucket", scoreBucket)
      if (includeDossier) params.append("include_dossier", "true")

      const response = await fetch(
        `http://localhost:8000/api/enrichment/export/${format}?${params.toString()}`
      )

      if (!response.ok) throw new Error("Export failed")

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url

      const extensions: Record<string, string> = {
        csv: ".csv",
        excel: ".xlsx",
        json: ".json",
        pdf: ".pdf"
      }

      a.download = `leads_export_${new Date().toISOString().split("T")[0]}${extensions[format]}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast.dismiss()
      toast.success(`✅ Exported to ${format.toUpperCase()}!`)
    } catch (error) {
      toast.dismiss()
      toast.error("Export failed")
      console.error("Export error:", error)
    } finally {
      setExporting(false)
    }
  }

  const ExportCard = ({
    icon: Icon,
    title,
    description,
    format,
    gradient,
    iconColor
  }: any) => (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <Card className={`p-6 bg-gradient-to-br ${gradient} border-slate-700 hover:border-cyan-500/50 transition-all cursor-pointer`}>
        <div className="flex items-start gap-4">
          <div className={`p-3 rounded-lg bg-${iconColor}-500/20`}>
            <Icon className={`h-8 w-8 text-${iconColor}-400`} />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white mb-1">{title}</h3>
            <p className="text-sm text-slate-400 mb-4">{description}</p>
            <Button
              onClick={() => exportLeads(format)}
              disabled={exporting}
              className={`w-full bg-${iconColor}-600 hover:bg-${iconColor}-700`}
            >
              {exporting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Export {title}
                </>
              )}
            </Button>
          </div>
        </div>
      </Card>
    </motion.div>
  )

  const bucketOptions = [
    { value: null, label: "All Leads" },
    { value: "red_hot", label: "Red Hot (80+)" },
    { value: "warm", label: "Warm (60-79)" },
    { value: "nurture", label: "Nurture (40-59)" },
    { value: "parked", label: "Parked (<40)" }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-white">Export Center</h2>
        <p className="text-slate-400 mt-1">Download your leads in multiple formats</p>
      </div>

      {/* Filters */}
      <Card className="p-6 bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Filter className="h-5 w-5 text-cyan-400" />
          Export Filters
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Label htmlFor="score-min" className="text-slate-300 mb-2 block">
              Minimum Score
            </Label>
            <div className="flex items-center gap-4">
              <input
                id="score-min"
                type="range"
                min={0}
                max={100}
                step={5}
                value={scoreMin}
                onChange={(e) => setScoreMin(parseInt(e.target.value))}
                className="flex-1"
              />
              <span className="text-white font-mono text-lg w-12 text-right">{scoreMin}</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Only export leads with score ≥ {scoreMin}
            </p>
          </div>

          <div>
            <Label htmlFor="bucket" className="text-slate-300 mb-2 block">
              Score Bucket
            </Label>
            <select
              id="bucket"
              value={scoreBucket || ""}
              onChange={(e) => setScoreBucket(e.target.value || null)}
              className="w-full p-2 rounded-lg bg-slate-700 border border-slate-600 text-white"
            >
              {bucketOptions.map((option) => (
                <option key={option.value || "all"} value={option.value || ""}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <Label className="text-slate-300 mb-2 block">Options</Label>
            <label className="flex items-center gap-2 p-3 rounded-lg bg-slate-700/50 cursor-pointer">
              <input
                type="checkbox"
                checked={includeDossier}
                onChange={(e) => setIncludeDossier(e.target.checked)}
                className="rounded border-slate-600"
              />
              <span className="text-sm text-slate-300">Include full dossier</span>
            </label>
          </div>
        </div>
      </Card>

      {/* Export Formats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ExportCard
          icon={FileText}
          title="CSV"
          description="Clean, parseable format for spreadsheets and CRMs"
          format="csv"
          gradient="from-green-900/20 to-green-950/30"
          iconColor="green"
        />

        <ExportCard
          icon={FileSpreadsheet}
          title="Excel"
          description="Multi-sheet workbook with formatting and color coding"
          format="excel"
          gradient="from-emerald-900/20 to-emerald-950/30"
          iconColor="emerald"
        />

        <ExportCard
          icon={FileJson}
          title="JSON"
          description="Complete data structure for integrations and APIs"
          format="json"
          gradient="from-blue-900/20 to-blue-950/30"
          iconColor="blue"
        />

        <ExportCard
          icon={FileType}
          title="PDF"
          description="Professional report ready to print or email"
          format="pdf"
          gradient="from-red-900/20 to-red-950/30"
          iconColor="red"
        />
      </div>

      {/* Export Info */}
      <Card className="p-6 bg-gradient-to-br from-cyan-900/10 to-cyan-950/20 border-cyan-700/30">
        <h3 className="text-lg font-semibold text-white mb-3">Export Features</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-medium text-cyan-400 mb-2">CSV Export</h4>
            <ul className="text-sm text-slate-400 space-y-1">
              <li>• Compatible with Excel, Google Sheets</li>
              <li>• Import to CRMs (Salesforce, HubSpot)</li>
              <li>• Clean column headers</li>
              <li>• Optional dossier inclusion</li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-medium text-emerald-400 mb-2">Excel Export</h4>
            <ul className="text-sm text-slate-400 space-y-1">
              <li>• Multiple sheets (Summary, All Leads, Hot Leads)</li>
              <li>• Color-coded by score</li>
              <li>• Auto-sized columns</li>
              <li>• Professional formatting</li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-medium text-blue-400 mb-2">JSON Export</h4>
            <ul className="text-sm text-slate-400 space-y-1">
              <li>• Complete data structure</li>
              <li>• Nested objects for relationships</li>
              <li>• Perfect for API integrations</li>
              <li>• Full dossier included</li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-medium text-red-400 mb-2">PDF Export</h4>
            <ul className="text-sm text-slate-400 space-y-1">
              <li>• Professional report format</li>
              <li>• Summary statistics</li>
              <li>• Detailed lead sections</li>
              <li>• Ready to print/email</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  )
}
