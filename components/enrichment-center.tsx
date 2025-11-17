"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Mail, Phone, Globe, User, Building2, Loader2, CheckCircle2, Search, Sparkles } from "lucide-react"
import toast from "react-hot-toast"
import { motion, AnimatePresence } from "framer-motion"

interface EmailCandidate {
  email: string
  pattern: string
  confidence: number
  deliverable: boolean | null
  source: string
}

interface EnrichmentResult {
  company_name: string
  description?: string
  technologies?: string[]
  social_profiles?: Record<string, string>
  employees?: string
  industry?: string
  completeness?: number
  data_quality_score?: number
}

export default function EnrichmentCenter() {
  const [activeTab, setActiveTab] = useState<"contacts" | "company">("contacts")

  // Contact Finding State
  const [companyName, setCompanyName] = useState("")
  const [website, setWebsite] = useState("")
  const [personName, setPersonName] = useState("")
  const [emailCandidates, setEmailCandidates] = useState<EmailCandidate[]>([])
  const [findingContacts, setFindingContacts] = useState(false)

  // Company Enrichment State
  const [enrichCompanyName, setEnrichCompanyName] = useState("")
  const [enrichWebsite, setEnrichWebsite] = useState("")
  const [enrichmentResult, setEnrichmentResult] = useState<EnrichmentResult | null>(null)
  const [enriching, setEnriching] = useState(false)

  const findContacts = async () => {
    if (!companyName) {
      toast.error("Please enter a company name")
      return
    }

    setFindingContacts(true)
    setEmailCandidates([])

    try {
      const response = await fetch("http://localhost:8000/api/enrichment/find-contacts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: companyName,
          website: website || null,
          person_name: personName || null
        })
      })

      if (!response.ok) throw new Error("Contact finding failed")

      const data = await response.json()
      setEmailCandidates(data.candidates || [])
      toast.success(`Found ${data.total_candidates} email candidates!`)
    } catch (error) {
      toast.error("Failed to find contacts")
      console.error(error)
    } finally {
      setFindingContacts(false)
    }
  }

  const enrichCompany = async () => {
    if (!enrichCompanyName) {
      toast.error("Please enter a company name")
      return
    }

    setEnriching(true)
    setEnrichmentResult(null)

    try {
      const response = await fetch("http://localhost:8000/api/enrichment/enrich-company", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: enrichCompanyName,
          website: enrichWebsite || null,
          deep: true
        })
      })

      if (!response.ok) throw new Error("Enrichment failed")

      const data = await response.json()
      setEnrichmentResult(data.enrichment)
      toast.success("Company enriched successfully!")
    } catch (error) {
      toast.error("Failed to enrich company")
      console.error(error)
    } finally {
      setEnriching(false)
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return "text-green-400"
    if (confidence >= 0.6) return "text-yellow-400"
    return "text-orange-400"
  }

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.8) return "High"
    if (confidence >= 0.6) return "Medium"
    return "Low"
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-white">Enrichment Center</h2>
        <p className="text-slate-400 mt-1">Find contacts and enrich company data</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-700">
        <button
          onClick={() => setActiveTab("contacts")}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === "contacts"
              ? "text-cyan-400 border-b-2 border-cyan-400"
              : "text-slate-400 hover:text-slate-300"
          }`}
        >
          <Mail className="inline h-4 w-4 mr-2" />
          Contact Finder
        </button>
        <button
          onClick={() => setActiveTab("company")}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === "company"
              ? "text-cyan-400 border-b-2 border-cyan-400"
              : "text-slate-400 hover:text-slate-300"
          }`}
        >
          <Building2 className="inline h-4 w-4 mr-2" />
          Company Enrichment
        </button>
      </div>

      {/* Contact Finder Tab */}
      {activeTab === "contacts" && (
        <div className="space-y-6">
          {/* Input Form */}
          <Card className="p-6 bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Search className="h-5 w-5 text-cyan-400" />
              Find Email Addresses
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="company" className="text-slate-300">Company Name *</Label>
                <Input
                  id="company"
                  placeholder="e.g., Acme Corp"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>
              <div>
                <Label htmlFor="website" className="text-slate-300">Website (Optional)</Label>
                <Input
                  id="website"
                  placeholder="https://acme.com"
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>
              <div>
                <Label htmlFor="person" className="text-slate-300">Person Name (Optional)</Label>
                <Input
                  id="person"
                  placeholder="John Doe"
                  value={personName}
                  onChange={(e) => setPersonName(e.target.value)}
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>
            </div>
            <Button
              onClick={findContacts}
              disabled={findingContacts}
              className="mt-4 bg-cyan-600 hover:bg-cyan-700"
            >
              {findingContacts ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Finding...
                </>
              ) : (
                <>
                  <Mail className="h-4 w-4 mr-2" />
                  Find Contacts
                </>
              )}
            </Button>
          </Card>

          {/* Results */}
          <AnimatePresence>
            {emailCandidates.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-3"
              >
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-yellow-400" />
                  {emailCandidates.length} Email Candidates Found
                </h3>
                {emailCandidates.map((candidate, index) => (
                  <motion.div
                    key={candidate.email}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card className="p-4 bg-slate-800 border-slate-700 hover:border-cyan-500/50 transition-all">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <Mail className="h-4 w-4 text-cyan-400" />
                            <code className="text-white font-mono">{candidate.email}</code>
                            {candidate.deliverable === true && (
                              <CheckCircle2 className="h-4 w-4 text-green-400" />
                            )}
                          </div>
                          <div className="flex gap-2 text-xs">
                            <Badge variant="outline" className={`${getConfidenceColor(candidate.confidence)}`}>
                              {getConfidenceBadge(candidate.confidence)} Confidence
                            </Badge>
                            <Badge variant="outline" className="bg-slate-700 text-slate-300">
                              {candidate.pattern === "scraped" ? "Found on website" : `Pattern: ${candidate.pattern}`}
                            </Badge>
                            {candidate.deliverable === true && (
                              <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/30">
                                Verified ✓
                              </Badge>
                            )}
                            {candidate.deliverable === false && (
                              <Badge variant="outline" className="bg-red-500/10 text-red-400 border-red-500/30">
                                Not deliverable
                              </Badge>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className={`text-2xl font-bold ${getConfidenceColor(candidate.confidence)}`}>
                            {Math.round(candidate.confidence * 100)}%
                          </div>
                        </div>
                      </div>
                    </Card>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Company Enrichment Tab */}
      {activeTab === "company" && (
        <div className="space-y-6">
          {/* Input Form */}
          <Card className="p-6 bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-400" />
              Enrich Company Data
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="enrich-company" className="text-slate-300">Company Name *</Label>
                <Input
                  id="enrich-company"
                  placeholder="e.g., Acme Corp"
                  value={enrichCompanyName}
                  onChange={(e) => setEnrichCompanyName(e.target.value)}
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>
              <div>
                <Label htmlFor="enrich-website" className="text-slate-300">Website (Optional)</Label>
                <Input
                  id="enrich-website"
                  placeholder="https://acme.com"
                  value={enrichWebsite}
                  onChange={(e) => setEnrichWebsite(e.target.value)}
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>
            </div>
            <Button
              onClick={enrichCompany}
              disabled={enriching}
              className="mt-4 bg-purple-600 hover:bg-purple-700"
            >
              {enriching ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Enriching...
                </>
              ) : (
                <>
                  <Building2 className="h-4 w-4 mr-2" />
                  Enrich Company
                </>
              )}
            </Button>
          </Card>

          {/* Enrichment Results */}
          <AnimatePresence>
            {enrichmentResult && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                {/* Data Quality Score */}
                <Card className="p-6 bg-gradient-to-br from-purple-900/20 to-purple-950/30 border-purple-700/50">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-1">Data Quality Score</h3>
                      <p className="text-sm text-slate-400">Completeness: {enrichmentResult.completeness}%</p>
                    </div>
                    <div className="text-right">
                      <div className="text-4xl font-bold text-purple-400">
                        {enrichmentResult.data_quality_score || 0}
                      </div>
                      <p className="text-xs text-slate-400">out of 100</p>
                    </div>
                  </div>
                </Card>

                {/* Company Info */}
                <Card className="p-6 bg-slate-800 border-slate-700">
                  <h3 className="text-lg font-semibold text-white mb-4">Company Information</h3>
                  <div className="space-y-3">
                    {enrichmentResult.description && (
                      <div>
                        <Label className="text-slate-400 text-sm">Description</Label>
                        <p className="text-white mt-1">{enrichmentResult.description}</p>
                      </div>
                    )}
                    {enrichmentResult.industry && (
                      <div>
                        <Label className="text-slate-400 text-sm">Industry</Label>
                        <Badge className="mt-1">{enrichmentResult.industry}</Badge>
                      </div>
                    )}
                  </div>
                </Card>

                {/* Tech Stack */}
                {enrichmentResult.technologies && enrichmentResult.technologies.length > 0 && (
                  <Card className="p-6 bg-slate-800 border-slate-700">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                      <Globe className="h-5 w-5 text-blue-400" />
                      Technology Stack
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {enrichmentResult.technologies.map((tech) => (
                        <Badge key={tech} variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30">
                          {tech}
                        </Badge>
                      ))}
                    </div>
                  </Card>
                )}

                {/* Social Profiles */}
                {enrichmentResult.social_profiles && Object.keys(enrichmentResult.social_profiles).length > 0 && (
                  <Card className="p-6 bg-slate-800 border-slate-700">
                    <h3 className="text-lg font-semibold text-white mb-4">Social Profiles</h3>
                    <div className="space-y-2">
                      {Object.entries(enrichmentResult.social_profiles).map(([platform, url]) => (
                        <a
                          key={platform}
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-3 p-3 rounded-lg bg-slate-700/50 hover:bg-slate-700 transition-colors"
                        >
                          <div className="capitalize text-slate-300">{platform}:</div>
                          <div className="flex-1 text-cyan-400 hover:underline truncate">{url}</div>
                        </a>
                      ))}
                    </div>
                  </Card>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}
