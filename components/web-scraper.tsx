"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Loader2, Search, Globe, Briefcase, Building2, CheckCircle2, AlertCircle } from "lucide-react"

interface ScrapeResult {
  status: string
  message: string
  results: any
}

export function WebScraper() {
  const [activeTab, setActiveTab] = useState("job-boards")

  // Job Boards State
  const [jobQuery, setJobQuery] = useState("")
  const [jobLocation, setJobLocation] = useState("")
  const [selectedSources, setSelectedSources] = useState<string[]>(["indeed", "naukri"])
  const [jobPages, setJobPages] = useState(3)
  const [jobLoading, setJobLoading] = useState(false)
  const [jobResult, setJobResult] = useState<ScrapeResult | null>(null)

  // Company Website State
  const [companyUrl, setCompanyUrl] = useState("")
  const [companyName, setCompanyName] = useState("")
  const [deepScan, setDeepScan] = useState(false)
  const [companyLoading, setCompanyLoading] = useState(false)
  const [companyResult, setCompanyResult] = useState<ScrapeResult | null>(null)

  // Lead Discovery State
  const [searchQuery, setSearchQuery] = useState("")
  const [numResults, setNumResults] = useState(20)
  const [scrapeDiscovered, setScrapeDiscovered] = useState(false)
  const [discoveryLoading, setDiscoveryLoading] = useState(false)
  const [discoveryResult, setDiscoveryResult] = useState<ScrapeResult | null>(null)

  // Career Page State
  const [careerUrl, setCareerUrl] = useState("")
  const [careerCompanyName, setCareerCompanyName] = useState("")
  const [careerLoading, setCareerLoading] = useState(false)
  const [careerResult, setCareerResult] = useState<ScrapeResult | null>(null)

  const handleJobBoardScrape = async () => {
    if (!jobQuery) return

    setJobLoading(true)
    setJobResult(null)

    try {
      const response = await fetch("http://localhost:8000/api/scrape/job-boards", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: jobQuery,
          location: jobLocation,
          sources: selectedSources,
          num_pages: jobPages
        })
      })

      if (!response.ok) throw new Error("Scraping failed")

      const data = await response.json()
      setJobResult(data)
    } catch (error) {
      console.error("Error scraping job boards:", error)
      setJobResult({
        status: "error",
        message: "Failed to scrape job boards",
        results: null
      })
    } finally {
      setJobLoading(false)
    }
  }

  const handleCompanyScrape = async () => {
    if (!companyUrl) return

    setCompanyLoading(true)
    setCompanyResult(null)

    try {
      const response = await fetch("http://localhost:8000/api/scrape/company-website", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: companyUrl,
          company_name: companyName || null,
          deep_scan: deepScan
        })
      })

      if (!response.ok) throw new Error("Scraping failed")

      const data = await response.json()
      setCompanyResult(data)
    } catch (error) {
      console.error("Error scraping company:", error)
      setCompanyResult({
        status: "error",
        message: "Failed to scrape company website",
        results: null
      })
    } finally {
      setCompanyLoading(false)
    }
  }

  const handleLeadDiscovery = async () => {
    if (!searchQuery) return

    setDiscoveryLoading(true)
    setDiscoveryResult(null)

    try {
      const response = await fetch("http://localhost:8000/api/scrape/discover-leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          search_query: searchQuery,
          num_results: numResults,
          scrape_companies: scrapeDiscovered
        })
      })

      if (!response.ok) throw new Error("Discovery failed")

      const data = await response.json()
      setDiscoveryResult(data)
    } catch (error) {
      console.error("Error discovering leads:", error)
      setDiscoveryResult({
        status: "error",
        message: "Failed to discover leads",
        results: null
      })
    } finally {
      setDiscoveryLoading(false)
    }
  }

  const handleCareerPageScrape = async () => {
    if (!careerUrl || !careerCompanyName) return

    setCareerLoading(true)
    setCareerResult(null)

    try {
      const response = await fetch("http://localhost:8000/api/scrape/career-page", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: careerUrl,
          company_name: careerCompanyName
        })
      })

      if (!response.ok) throw new Error("Scraping failed")

      const data = await response.json()
      setCareerResult(data)
    } catch (error) {
      console.error("Error scraping career page:", error)
      setCareerResult({
        status: "error",
        message: "Failed to scrape career page",
        results: null
      })
    } finally {
      setCareerLoading(false)
    }
  }

  const toggleSource = (source: string) => {
    setSelectedSources(prev =>
      prev.includes(source)
        ? prev.filter(s => s !== source)
        : [...prev, source]
    )
  }

  const ResultCard = ({ result }: { result: ScrapeResult | null }) => {
    if (!result) return null

    const isSuccess = result.status === "completed"

    return (
      <Alert className={isSuccess ? "border-green-500" : "border-red-500"}>
        <div className="flex items-start gap-2">
          {isSuccess ? (
            <CheckCircle2 className="h-5 w-5 text-green-500" />
          ) : (
            <AlertCircle className="h-5 w-5 text-red-500" />
          )}
          <div className="flex-1">
            <AlertDescription className="font-medium">{result.message}</AlertDescription>
            {result.results && (
              <div className="mt-2 space-y-1 text-sm">
                {result.results.total_jobs !== undefined && (
                  <p>Jobs found: {result.results.total_jobs}</p>
                )}
                {result.results.total_leads_created !== undefined && (
                  <p className="text-green-600 font-medium">
                    Leads created: {result.results.total_leads_created}
                  </p>
                )}
                {result.results.leads_created !== undefined && (
                  <p className="text-green-600 font-medium">
                    Leads created: {result.results.leads_created}
                  </p>
                )}
                {result.results.urls_found !== undefined && (
                  <p>URLs found: {result.results.urls_found}</p>
                )}
                {result.results.jobs_found !== undefined && (
                  <p>Jobs found: {result.results.jobs_found}</p>
                )}
                {result.results.sources && (
                  <div className="mt-2">
                    <p className="font-medium">Sources:</p>
                    {Object.entries(result.results.sources).map(([source, data]: [string, any]) => (
                      <p key={source} className="ml-2">
                        {source}: {data.jobs_found} jobs ({data.status})
                      </p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Web Scraping</h2>
        <p className="text-sm text-muted-foreground">
          Automatically scrape job boards, company websites, and search engines to find leads
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="job-boards">
            <Briefcase className="h-4 w-4 mr-2" />
            Job Boards
          </TabsTrigger>
          <TabsTrigger value="company">
            <Building2 className="h-4 w-4 mr-2" />
            Company Website
          </TabsTrigger>
          <TabsTrigger value="discover">
            <Search className="h-4 w-4 mr-2" />
            Lead Discovery
          </TabsTrigger>
          <TabsTrigger value="career">
            <Globe className="h-4 w-4 mr-2" />
            Career Page
          </TabsTrigger>
        </TabsList>

        {/* Job Boards Tab */}
        <TabsContent value="job-boards" className="space-y-4">
          <Card className="p-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="job-query">Search Query *</Label>
                <Input
                  id="job-query"
                  placeholder="e.g., marketing manager, growth hacker"
                  value={jobQuery}
                  onChange={(e) => setJobQuery(e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="job-location">Location (Optional)</Label>
                <Input
                  id="job-location"
                  placeholder="e.g., Mumbai, Bangalore"
                  value={jobLocation}
                  onChange={(e) => setJobLocation(e.target.value)}
                />
              </div>

              <div>
                <Label>Job Boards</Label>
                <div className="flex gap-2 mt-2">
                  {["indeed", "naukri", "linkedin"].map((source) => (
                    <Badge
                      key={source}
                      variant={selectedSources.includes(source) ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => toggleSource(source)}
                    >
                      {source}
                    </Badge>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Note: LinkedIn may block scraping attempts
                </p>
              </div>

              <div>
                <Label htmlFor="job-pages">Pages per Source</Label>
                <Input
                  id="job-pages"
                  type="number"
                  min={1}
                  max={10}
                  value={jobPages}
                  onChange={(e) => setJobPages(parseInt(e.target.value) || 3)}
                />
              </div>

              <Button
                onClick={handleJobBoardScrape}
                disabled={jobLoading || !jobQuery || selectedSources.length === 0}
                className="w-full"
              >
                {jobLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {jobLoading ? "Scraping..." : "Start Scraping"}
              </Button>

              {jobResult && <ResultCard result={jobResult} />}
            </div>
          </Card>
        </TabsContent>

        {/* Company Website Tab */}
        <TabsContent value="company" className="space-y-4">
          <Card className="p-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="company-url">Company Website URL *</Label>
                <Input
                  id="company-url"
                  placeholder="https://example.com"
                  value={companyUrl}
                  onChange={(e) => setCompanyUrl(e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="company-name">Company Name (Optional)</Label>
                <Input
                  id="company-name"
                  placeholder="Auto-detected if not provided"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="deep-scan"
                  checked={deepScan}
                  onChange={(e) => setDeepScan(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <Label htmlFor="deep-scan" className="cursor-pointer">
                  Deep Scan (also scrape career and contact pages - slower)
                </Label>
              </div>

              <Button
                onClick={handleCompanyScrape}
                disabled={companyLoading || !companyUrl}
                className="w-full"
              >
                {companyLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {companyLoading ? "Scraping..." : "Scrape Company Website"}
              </Button>

              {companyResult && <ResultCard result={companyResult} />}

              {companyResult?.results?.company_data && (
                <Card className="p-4 bg-muted">
                  <h4 className="font-semibold mb-2">Company Data:</h4>
                  <div className="space-y-1 text-sm">
                    <p><strong>Name:</strong> {companyResult.results.company_data.name}</p>
                    {companyResult.results.company_data.emails?.length > 0 && (
                      <p><strong>Emails:</strong> {companyResult.results.company_data.emails.join(", ")}</p>
                    )}
                    {companyResult.results.company_data.phones?.length > 0 && (
                      <p><strong>Phones:</strong> {companyResult.results.company_data.phones.join(", ")}</p>
                    )}
                    {companyResult.results.company_data.career_page_url && (
                      <p><strong>Career Page:</strong> {companyResult.results.company_data.career_page_url}</p>
                    )}
                  </div>
                </Card>
              )}
            </div>
          </Card>
        </TabsContent>

        {/* Lead Discovery Tab */}
        <TabsContent value="discover" className="space-y-4">
          <Card className="p-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="search-query">Search Query *</Label>
                <Input
                  id="search-query"
                  placeholder="e.g., D2C ecommerce India hiring marketing"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Use keywords that identify your ideal customers and hiring signals
                </p>
              </div>

              <div>
                <Label htmlFor="num-results">Number of Results</Label>
                <Input
                  id="num-results"
                  type="number"
                  min={5}
                  max={100}
                  value={numResults}
                  onChange={(e) => setNumResults(parseInt(e.target.value) || 20)}
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="scrape-discovered"
                  checked={scrapeDiscovered}
                  onChange={(e) => setScrapeDiscovered(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <Label htmlFor="scrape-discovered" className="cursor-pointer">
                  Also scrape each discovered company (much slower)
                </Label>
              </div>

              <Button
                onClick={handleLeadDiscovery}
                disabled={discoveryLoading || !searchQuery}
                className="w-full"
              >
                {discoveryLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {discoveryLoading ? "Discovering..." : "Discover Leads"}
              </Button>

              {discoveryResult && <ResultCard result={discoveryResult} />}

              {discoveryResult?.results?.discovered_urls && (
                <Card className="p-4 bg-muted max-h-60 overflow-y-auto">
                  <h4 className="font-semibold mb-2">Discovered URLs:</h4>
                  <ul className="space-y-1 text-sm">
                    {discoveryResult.results.discovered_urls.map((url: string, i: number) => (
                      <li key={i}>
                        <a href={url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                          {url}
                        </a>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}
            </div>
          </Card>
        </TabsContent>

        {/* Career Page Tab */}
        <TabsContent value="career" className="space-y-4">
          <Card className="p-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="career-url">Career Page URL *</Label>
                <Input
                  id="career-url"
                  placeholder="https://example.com/careers"
                  value={careerUrl}
                  onChange={(e) => setCareerUrl(e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="career-company">Company Name *</Label>
                <Input
                  id="career-company"
                  placeholder="Company name"
                  value={careerCompanyName}
                  onChange={(e) => setCareerCompanyName(e.target.value)}
                />
              </div>

              <Button
                onClick={handleCareerPageScrape}
                disabled={careerLoading || !careerUrl || !careerCompanyName}
                className="w-full"
              >
                {careerLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {careerLoading ? "Scraping..." : "Scrape Career Page"}
              </Button>

              {careerResult && <ResultCard result={careerResult} />}
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
