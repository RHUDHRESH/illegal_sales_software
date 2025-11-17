/**
 * Type definitions for API requests and responses
 * Mirrors backend Pydantic schemas
 */

// ============ ICP Types ============

export interface ICP {
  id: number;
  name: string;
  description?: string;
  size_buckets: string[];
  industries: string[];
  locations: string[];
  stages: string[];
  hiring_keywords: string[];
  pain_keywords: string[];
  channel_preferences: string[];
  budget_signals: string[];
  created_at: string;
  updated_at: string;
}

export interface ICPCreate {
  name: string;
  description?: string;
  size_buckets?: string[];
  industries?: string[];
  locations?: string[];
  stages?: string[];
  hiring_keywords?: string[];
  pain_keywords?: string[];
  channel_preferences?: string[];
  budget_signals?: string[];
}

export interface ICPUpdate {
  name?: string;
  description?: string;
  size_buckets?: string[];
  industries?: string[];
  locations?: string[];
  stages?: string[];
  hiring_keywords?: string[];
  pain_keywords?: string[];
  channel_preferences?: string[];
  budget_signals?: string[];
}

// ============ Lead Types ============

export interface Company {
  id: number;
  name: string;
  website?: string;
  sector?: string;
}

export interface Contact {
  id: number;
  name?: string;
  role?: string;
  email?: string;
  phone_numbers: string[];
}

export interface Lead {
  id: number;
  company_id: number;
  contact_id?: number;
  score_icp_fit: number;
  score_marketing_pain: number;
  score_data_quality: number;
  total_score: number;
  score_bucket: string;
  role_type?: string;
  pain_tags: string[];
  status: string;
  created_at: string;
  updated_at: string;
  context_dossier?: string;
  challenger_insight?: string;
  reframe_suggestion?: string;
  company?: Company;
  contact?: Contact;
}

export interface LeadFilter {
  score_min?: number;
  score_max?: number;
  status?: string;
  score_bucket?: string;
  limit?: number;
  offset?: number;
}

export interface LeadStatusUpdate {
  status: string;
}

export interface LeadNotesUpdate {
  notes: string;
}

export interface BucketCounts {
  red_hot: number;
  warm: number;
  nurture: number;
  parked: number;
}

// ============ Classification Types ============

export interface SignalInput {
  signal_text: string;
  source_type?: string;
  source_url?: string;
  company_name?: string;
  company_website?: string;
}

export interface ClassificationResult {
  icp_match: boolean;
  total_score: number;
  score_bucket: string;
  classification: Record<string, any>;
  company_id?: number;
  lead_id?: number;
}

// ============ Ingest Types ============

export interface OCRResult {
  extracted_text: string;
  detected_emails: string[];
  detected_phones: string[];
  detected_names: string[];
  detected_company?: string;
}

export interface CSVIngestResult {
  total_processed: number;
  total_created: number;
  results: Array<{
    company?: string;
    score?: number;
    bucket?: string;
    lead_id?: number;
    status: string;
    error?: string;
  }>;
  message: string;
}

// ============ Scraping Types ============

export interface JobBoardScrapeRequest {
  query: string;
  location?: string;
  sources?: string[];
  num_pages?: number;
}

export interface CompanyScrapeRequest {
  url: string;
  company_name?: string;
  deep_scan?: boolean;
}

export interface LeadDiscoveryRequest {
  search_query: string;
  num_results?: number;
  scrape_companies?: boolean;
}

export interface CareerPageScrapeRequest {
  url: string;
  company_name: string;
}

export interface ScrapeResult {
  status: string;
  message: string;
  results: Record<string, any>;
}
