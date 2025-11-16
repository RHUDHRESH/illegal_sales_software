'use client';

import { useState, useRef } from 'react';
import { Upload, Loader2, CheckCircle2, AlertCircle, Copy } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ClassificationResult {
  icp_match: boolean;
  total_score: number;
  score_bucket: string;
  company_id: number | null;
  lead_id: number | null;
  classification: Record<string, unknown>;
}

interface OCRResult {
  extracted_text: string;
  detected_emails: string[];
  detected_phones: string[];
  detected_names: string[];
  detected_company: string | null;
}

export default function OCRUploader() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [ocrResult, setOCRResult] = useState<OCRResult | null>(null);
  const [classificationResult, setClassificationResult] = useState<ClassificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && droppedFile.type.startsWith('image/')) {
      setFile(droppedFile);
      setError(null);
      processFile(droppedFile);
    } else {
      setError('Please drop an image file (JPG, PNG, etc.)');
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      processFile(selectedFile);
    }
  };

  const processFile = async (selectedFile: File) => {
    setLoading(true);
    setOCRResult(null);
    setClassificationResult(null);
    setError(null);

    try {
      // Step 1: OCR
      const formData = new FormData();
      formData.append('file', selectedFile);

      const ocrResponse = await fetch('http://localhost:8000/api/ingest/ocr', {
        method: 'POST',
        body: formData,
      });

      if (!ocrResponse.ok) {
        throw new Error('OCR processing failed');
      }

      const ocrData: OCRResult = await ocrResponse.json();
      setOCRResult(ocrData);

      // Step 2: Classify
      const classifyFormData = new FormData();
      classifyFormData.append('file', selectedFile);
      if (ocrData.detected_company) {
        classifyFormData.append('company_name', ocrData.detected_company);
      }

      const classifyResponse = await fetch(
        'http://localhost:8000/api/ingest/ocr-and-classify',
        {
          method: 'POST',
          body: classifyFormData,
        }
      );

      if (!classifyResponse.ok) {
        throw new Error('Classification failed');
      }

      const classifyData: ClassificationResult = await classifyResponse.json();
      setClassificationResult(classifyData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Upload Area */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden flex flex-col">
        <div className="bg-slate-900 border-b border-slate-700 p-4">
          <h2 className="text-lg font-bold text-white">📸 OCR Ingest</h2>
          <p className="text-sm text-slate-400 mt-1">Upload business cards, screenshots, or images</p>
        </div>

        <div className="flex-1 p-6 flex flex-col">
          <motion.div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            animate={{
              borderColor: isDragging ? '#3b82f6' : '#475569',
              backgroundColor: isDragging ? 'rgba(59, 130, 246, 0.05)' : 'transparent',
            }}
            className="flex-1 border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer transition-all"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className={`h-12 w-12 mb-4 ${isDragging ? 'text-blue-400' : 'text-slate-400'}`} />
            <p className="text-center font-semibold text-white mb-1">
              {isDragging ? 'Drop your file here' : 'Drag & drop an image'}
            </p>
            <p className="text-sm text-slate-400 text-center">
              or click to browse
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
            />
          </motion.div>

          {file && (
            <div className="mt-4 p-3 bg-slate-700/50 rounded border border-slate-600">
              <p className="text-sm text-slate-300">
                📄 <span className="font-semibold">{file.name}</span>
              </p>
              <p className="text-xs text-slate-400 mt-1">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
          )}

          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-4 p-3 bg-red-500/10 border border-red-500/50 rounded text-red-300 text-sm flex gap-2"
            >
              <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
              <p>{error}</p>
            </motion.div>
          )}

          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-4 p-4 bg-blue-500/10 border border-blue-500/50 rounded text-blue-300 flex items-center justify-center gap-2"
            >
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Processing OCR & Classification...</span>
            </motion.div>
          )}
        </div>
      </div>

      {/* Results */}
      <div className="space-y-4">
        {/* OCR Results */}
        {ocrResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-slate-800 border border-slate-700 rounded-lg p-4"
          >
            <h3 className="font-bold text-white mb-3">Extracted Text</h3>
            <div className="bg-slate-700/50 p-3 rounded border border-slate-600 text-sm text-slate-300 max-h-32 overflow-y-auto font-mono text-xs">
              {ocrResult.extracted_text}
            </div>

            {ocrResult.detected_emails.length > 0 && (
              <div className="mt-4">
                <p className="text-sm text-slate-400 mb-2">📧 Emails Found:</p>
                <div className="space-y-2">
                  {ocrResult.detected_emails.map((email) => (
                    <div
                      key={email}
                      className="flex items-center gap-2 p-2 bg-slate-700 rounded text-sm text-slate-300"
                    >
                      <span className="flex-1">{email}</span>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(email);
                        }}
                        className="text-slate-400 hover:text-slate-200"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {ocrResult.detected_phones.length > 0 && (
              <div className="mt-4">
                <p className="text-sm text-slate-400 mb-2">📱 Phones Found:</p>
                <div className="space-y-2">
                  {ocrResult.detected_phones.map((phone) => (
                    <div key={phone} className="p-2 bg-slate-700 rounded text-sm text-slate-300">
                      {phone}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {ocrResult.detected_company && (
              <div className="mt-4">
                <p className="text-sm text-slate-400 mb-1">🏢 Company:</p>
                <p className="text-sm font-semibold text-slate-200">{ocrResult.detected_company}</p>
              </div>
            )}
          </motion.div>
        )}

        {/* Classification Results */}
        {classificationResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-slate-800 border border-slate-700 rounded-lg p-4"
          >
            <div className="flex items-start gap-3 mb-4">
              <CheckCircle2 className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-bold text-white">Classification Complete</h3>
                <p className="text-sm text-slate-400">Lead created successfully</p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Score</span>
                <span className={`text-lg font-bold ${
                  classificationResult.total_score >= 80
                    ? 'text-green-400'
                    : classificationResult.total_score >= 60
                    ? 'text-yellow-400'
                    : 'text-blue-400'
                }`}>
                  {classificationResult.total_score.toFixed(1)}/100
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Bucket</span>
                <span className="px-3 py-1 bg-slate-700 text-slate-300 rounded text-sm font-semibold">
                  {classificationResult.score_bucket.replace('_', ' ').toUpperCase()}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">ICP Match</span>
                <span className={classificationResult.icp_match ? 'text-green-400' : 'text-slate-400'}>
                  {classificationResult.icp_match ? '✓ Yes' : '✗ No'}
                </span>
              </div>

              <div>
                <p className="text-sm text-slate-400 mb-2">Lead ID</p>
                <p className="font-mono text-sm text-slate-300">
                  {classificationResult.lead_id ? `#${classificationResult.lead_id}` : 'N/A'}
                </p>
              </div>

              <a
                href="http://localhost:3000"
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition-colors text-center mt-4"
              >
                View in Leads
              </a>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
