/**
 * Raptorflow Lead Engine - Typed API Client
 * Thin wrapper around fetch for backend API calls with full type safety
 */

import type {
  ICP,
  ICPCreate,
  ICPUpdate,
  Lead,
  LeadFilter,
  BucketCounts,
  SignalInput,
  ClassificationResult,
  OCRResult,
  CSVIngestResult,
  JobBoardScrapeRequest,
  CompanyScrapeRequest,
  LeadDiscoveryRequest,
  CareerPageScrapeRequest,
  ScrapeResult,
} from './types/api';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// ============ Error Handling ============

export class APIError extends Error {
  constructor(
    public status: number,
    public message: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.text();
    throw new APIError(response.status, error || response.statusText);
  }
  return response.json() as Promise<T>;
}

// ============ ICP APIs ============

export async function listICPs(): Promise<ICP[]> {
  const response = await fetch(`${API_BASE}/api/icp/`);
  return handleResponse<ICP[]>(response);
}

export async function getICP(id: number): Promise<ICP> {
  const response = await fetch(`${API_BASE}/api/icp/${id}`);
  return handleResponse<ICP>(response);
}

export async function createICP(icp: ICPCreate): Promise<ICP> {
  const response = await fetch(`${API_BASE}/api/icp/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(icp),
  });
  return handleResponse<ICP>(response);
}

export async function updateICP(id: number, icp: ICPUpdate): Promise<ICP> {
  const response = await fetch(`${API_BASE}/api/icp/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(icp),
  });
  return handleResponse<ICP>(response);
}

export async function deleteICP(id: number): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE}/api/icp/${id}`, {
    method: 'DELETE',
  });
  return handleResponse<{ message: string }>(response);
}

export async function createSoloFounderTemplate(): Promise<ICP> {
  const response = await fetch(`${API_BASE}/api/icp/templates/solo-founder`, {
    method: 'POST',
  });
  return handleResponse<ICP>(response);
}

export async function createSmallD2CTemplate(): Promise<ICP> {
  const response = await fetch(`${API_BASE}/api/icp/templates/small-d2c`, {
    method: 'POST',
  });
  return handleResponse<ICP>(response);
}

// ============ Lead APIs ============

export async function listLeads(params: LeadFilter = {}): Promise<Lead[]> {
  const query = new URLSearchParams();
  if (params.score_min !== undefined) query.append('score_min', params.score_min.toString());
  if (params.score_max !== undefined) query.append('score_max', params.score_max.toString());
  if (params.status) query.append('status', params.status);
  if (params.score_bucket) query.append('score_bucket', params.score_bucket);
  if (params.limit) query.append('limit', params.limit.toString());
  if (params.offset) query.append('offset', params.offset.toString());

  const response = await fetch(`${API_BASE}/api/leads/?${query}`);
  return handleResponse<Lead[]>(response);
}

export async function getLead(id: number): Promise<Lead> {
  const response = await fetch(`${API_BASE}/api/leads/${id}`);
  return handleResponse<Lead>(response);
}

export async function updateLeadStatus(
  id: number,
  status: string
): Promise<{ status: string; lead_id: number; new_status: string }> {
  const response = await fetch(`${API_BASE}/api/leads/${id}/status?status=${status}`, {
    method: 'PATCH',
  });
  return handleResponse<{ status: string; lead_id: number; new_status: string }>(response);
}

export async function updateLeadNotes(
  id: number,
  notes: string
): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE}/api/leads/${id}/notes?notes=${encodeURIComponent(notes)}`, {
    method: 'PATCH',
  });
  return handleResponse<{ status: string }>(response);
}

export async function deleteLead(id: number): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE}/api/leads/${id}`, {
    method: 'DELETE',
  });
  return handleResponse<{ message: string }>(response);
}

export async function getBucketCounts(): Promise<BucketCounts> {
  const response = await fetch(`${API_BASE}/api/leads/score-distribution/bucket-counts`);
  return handleResponse<BucketCounts>(response);
}

// ============ Classification APIs ============

export async function classifySignal(payload: SignalInput): Promise<ClassificationResult> {
  const response = await fetch(`${API_BASE}/api/classify/signal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse<ClassificationResult>(response);
}

export async function classifySignalsBatch(
  signals: SignalInput[]
): Promise<{ count: number; results: Array<{ signal: string; total_score?: number; status: string; error?: string }> }> {
  const response = await fetch(`${API_BASE}/api/classify/signal/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(signals),
  });
  return handleResponse<{ count: number; results: Array<{ signal: string; total_score?: number; status: string; error?: string }> }>(response);
}

// ============ Ingest APIs ============

export async function ocrFile(file: File): Promise<OCRResult> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/api/ingest/ocr`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<OCRResult>(response);
}

export async function ocrAndClassify(
  file: File,
  companyName?: string
): Promise<ClassificationResult> {
  const formData = new FormData();
  formData.append('file', file);
  if (companyName) {
    formData.append('company_name', companyName);
  }

  const response = await fetch(`${API_BASE}/api/ingest/ocr-and-classify`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<ClassificationResult>(response);
}

export async function ingestCSV(file: File): Promise<CSVIngestResult> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/api/ingest/csv`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<CSVIngestResult>(response);
}

// ============ Scraping APIs ============

export async function scrapeJobBoards(request: JobBoardScrapeRequest): Promise<ScrapeResult> {
  const response = await fetch(`${API_BASE}/api/scrape/job-boards`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<ScrapeResult>(response);
}

export async function scrapeCompanyWebsite(request: CompanyScrapeRequest): Promise<ScrapeResult> {
  const response = await fetch(`${API_BASE}/api/scrape/company-website`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<ScrapeResult>(response);
}

export async function discoverLeads(request: LeadDiscoveryRequest): Promise<ScrapeResult> {
  const response = await fetch(`${API_BASE}/api/scrape/discover-leads`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<ScrapeResult>(response);
}

export async function scrapeCareerPage(request: CareerPageScrapeRequest): Promise<ScrapeResult> {
  const response = await fetch(`${API_BASE}/api/scrape/career-page`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<ScrapeResult>(response);
}

export async function listScrapingSources(): Promise<{
  job_boards: Array<{ name: string; description: string; regions: string[]; rate_limit: string; notes?: string }>;
  search_engines: Array<{ name: string; description: string; rate_limit: string }>;
  company_scraping: { description: string; features: string[] };
}> {
  const response = await fetch(`${API_BASE}/api/scrape/sources`);
  return handleResponse<{
    job_boards: Array<{ name: string; description: string; regions: string[]; rate_limit: string; notes?: string }>;
    search_engines: Array<{ name: string; description: string; rate_limit: string }>;
    company_scraping: { description: string; features: string[] };
  }>(response);
}

export async function checkScrapingHealth(): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE}/api/scrape/health`);
  return handleResponse<{ status: string; message: string }>(response);
}

// ============ Health Check ============

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`, {
      method: 'GET',
    });
    return response.ok;
  } catch {
    return false;
  }
}
