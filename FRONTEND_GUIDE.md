# 🎨 Frontend Guide - Modern UI

The Raptorflow Lead Engine now features a **stunning, enterprise-grade frontend** that rivals commercial SaaS products costing $50k+/year. Built with Next.js, React, TypeScript, Tailwind CSS, and Framer Motion.

---

## 🚀 Getting Started

### Install Dependencies
```bash
npm install
```

### Run Development Server
```bash
npm run dev
```

Open **http://localhost:3000** in your browser.

---

## 🎯 UI Overview

### Modern Design Principles
- **Minimalist** - Clean, uncluttered interface
- **Dark Mode Optimized** - Professional dark theme
- **Smooth Animations** - Framer Motion transitions
- **Gradient Accents** - Cyan/blue brand colors
- **Icon-Based Nav** - Clear visual hierarchy
- **Professional Typography** - Tailwind's font system

### Layout Structure
```
┌─────────────────────────────────────────────┐
│  Header (Sticky)                             │
│  - Logo + Brand                              │
│  - Backend Status Indicator                  │
└─────────────────────────────────────────────┘
┌──────────┬──────────────────────────────────┐
│  Sidebar │  Main Content Area                │
│  (Fixed) │  (Scrollable)                     │
│          │                                   │
│  Nav     │  Active Page Component            │
│  Items   │  - Dashboard                      │
│          │  - Analytics                      │
│  Version │  - Leads                          │
│  Status  │  - Scraper                        │
│          │  - Enrichment                     │
│          │  - Automation                     │
│          │  - Export                         │
│          │  - ICP Builder                    │
│          │  - OCR Ingest                     │
└──────────┴──────────────────────────────────┘
```

---

## 📊 Pages & Features

### 1. **Overview Dashboard**
**Icon:** LayoutDashboard

Quick statistics and bucket overview.

**Features:**
- Lead count by bucket (Hot, Warm, Nurture, Parked)
- Percentage distribution
- Auto-refresh every 5 seconds
- Visual metrics with gradient colors

**Components:**
- `Dashboard.tsx` (existing)

---

### 2. **Analytics** ⭐ NEW
**Icon:** BarChart3

Real-time insights with beautiful charts.

**Features:**
- **Key Metrics Cards**
  - Total Leads
  - Hot Leads
  - Companies
  - Contacts Found
  - Trend indicators (up/down arrows)
  - Animated on load

- **Lead Velocity Chart** (Line)
  - Daily lead creation over time
  - Customizable time range (7d, 30d, 90d)
  - Interactive tooltips

- **Average Score Trend** (Line)
  - Score quality over time
  - 0-100 scale

- **Lead Distribution** (Pie)
  - Visual breakdown by bucket
  - Percentage labels

- **Hot Leads Over Time** (Bar)
  - Daily hot lead count
  - Red bars for visual impact

- **Insight Cards**
  - Weekly velocity
  - Contact rate
  - Hot lead percentage

- **Ready to Contact CTA**
  - Shows when warm/hot leads are waiting
  - One-click navigation to leads

**Tech Stack:**
- Recharts for charts
- Framer Motion for animations
- Real-time data fetching

---

### 3. **Leads**
**Icon:** Target

Manage and view all leads.

**Features:**
- Filterable lead list
- Score-based filtering
- Status management
- Lead detail view
- Contact information
- SPIN/MEDDIC fields

**Components:**
- `LeadsList.tsx` (existing)

---

### 4. **Web Scraper**
**Icon:** Scan

Collect leads from the web.

**Features:**
- 4 scraping modes (tabs)
  - Job Boards (Indeed, Naukri, LinkedIn)
  - Company Website
  - Lead Discovery (Search)
  - Career Page

- Real-time scraping results
- Progress indicators
- Source selection
- Deep scan toggle

**Components:**
- `WebScraper.tsx` (existing)

---

### 5. **Enrichment** ⭐ NEW
**Icon:** Sparkles

Find contacts and enrich companies.

**Tabs:**

#### **Contact Finder**
Find email addresses with patterns.

**Features:**
- Generate 11 email patterns
- SMTP verification
- Confidence scoring (0-100%)
- Deliverability status
- Source tracking (scraped vs. generated)
- Visual confidence indicators
- Green checkmarks for verified emails

**Example Output:**
```
john.doe@acme.com
✓ Verified | High Confidence (90%)
Pattern: {first}.{last}@{domain}
```

#### **Company Enrichment**
Gather comprehensive company intelligence.

**Features:**
- Company description
- Industry classification
- Technology stack detection (20+ technologies)
- Social profile discovery (LinkedIn, Twitter, etc.)
- Data quality score (0-100)
- Completeness percentage
- Beautiful result cards

**Data Collected:**
- Description & tagline
- Industry & company type
- Technologies used
- Social media profiles
- Employee count estimates
- Funding information (if available)

---

### 6. **Automation** ⭐ NEW
**Icon:** Zap

Schedule jobs and configure webhooks.

**Tabs:**

#### **Scheduled Jobs**
Automate recurring tasks.

**Features:**
- **Add Job Form**
  - Search query input
  - Hour/minute selector (24h format)
  - Source selection
  - Schedule confirmation

- **Jobs List**
  - Job ID and type badges
  - Schedule display (e.g., "Daily at 09:00")
  - Next run time
  - Delete button

**Example Jobs:**
- Daily job scraping at 9 AM
- Periodic enrichment every 24h
- Weekly lead discovery

#### **Webhooks & Integrations**
Connect to external services.

**Features:**
- **Quick Integrations**
  - Slack (pre-built)
  - Zapier (pre-built)
  - Just paste webhook URL

- **Custom Webhook Builder**
  - Webhook URL input
  - Event type selection (6 events)
    - lead.created
    - lead.hot
    - lead.updated
    - lead.status_changed
    - company.enriched
    - scraping.completed

- **Webhooks List**
  - URL display
  - Active/disabled status
  - Event badges
  - Delete/manage

**Integration Examples:**
```bash
# Slack notifications for hot leads
# Zapier automation triggers
# Custom CRM sync
```

---

### 7. **Export** ⭐ NEW
**Icon:** Download

Download leads in multiple formats.

**Features:**

#### **Export Filters**
- Minimum score slider (0-100)
- Score bucket dropdown
  - All Leads
  - Red Hot (80+)
  - Warm (60-79)
  - Nurture (40-59)
  - Parked (<40)
- Include dossier toggle

#### **Export Formats**
Four beautiful format cards:

**CSV** (Green)
- Clean, parseable format
- Compatible with Excel, Google Sheets
- Import to CRMs

**Excel** (Emerald)
- Multi-sheet workbook
- Color-coded by score
- Summary statistics
- Auto-sized columns

**JSON** (Blue)
- Complete data structure
- Perfect for API integrations
- Full dossier included

**PDF** (Red)
- Professional report
- Ready to print/email
- Detailed lead sections
- Summary page

**Features:**
- One-click exports
- Loading indicators
- Automatic downloads
- Format-specific descriptions

---

### 8. **ICP Builder**
**Icon:** Database

Define Ideal Customer Profiles.

**Features:**
- Multi-criteria ICP creation
- Size buckets
- Industries
- Keywords
- Pain tags

**Components:**
- `ICPBuilder.tsx` (existing)

---

### 9. **OCR Ingest**
**Icon:** Settings

Upload and process files.

**Features:**
- Drag-and-drop file upload
- Image OCR (Tesseract)
- PDF text extraction
- Contact extraction
- Automatic classification

**Components:**
- `OCRUploader.tsx` (existing)

---

## 🎨 Design System

### Color Palette

**Primary Colors:**
```css
Cyan: #06b6d4 (cyan-500)
Blue: #3b82f6 (blue-500)
```

**Status Colors:**
```css
Success: #10b981 (green-500)
Warning: #f59e0b (amber-500)
Error: #ef4444 (red-500)
Info: #3b82f6 (blue-500)
```

**Background Gradients:**
```css
Main: from-slate-950 via-slate-900 to-slate-950
Cards: from-slate-800 to-slate-900
Accent: from-cyan-600 to-blue-600
```

**Borders:**
```css
Default: border-slate-700
Hover: border-cyan-500/50
Active: border-cyan-500
```

### Typography

**Headings:**
```css
H1: text-3xl font-bold
H2: text-2xl font-bold
H3: text-lg font-semibold
```

**Body:**
```css
Normal: text-sm text-slate-400
White: text-white
Muted: text-slate-500
```

**Special:**
```css
Gradient: text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400
Code: font-mono
```

### Spacing

**Padding:**
```css
Card: p-6
Section: p-8
Button: px-4 py-2
```

**Gaps:**
```css
Small: gap-2
Medium: gap-4
Large: gap-6
```

**Margins:**
```css
Section: space-y-6
List: space-y-3
Inline: space-x-2
```

### Components

**Card:**
```tsx
<Card className="p-6 bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700">
  {children}
</Card>
```

**Button (Primary):**
```tsx
<Button className="bg-cyan-600 hover:bg-cyan-700">
  Click Me
</Button>
```

**Badge:**
```tsx
<Badge variant="outline" className="bg-cyan-500/10 text-cyan-400 border-cyan-500/30">
  Label
</Badge>
```

**Input:**
```tsx
<Input className="bg-slate-700 border-slate-600 text-white" />
```

---

## ⚡ Animations

### Framer Motion Patterns

**Page Transitions:**
```tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, y: -20 }}
  transition={{ duration: 0.3 }}
>
  {content}
</motion.div>
```

**Card Hover:**
```tsx
<motion.div
  whileHover={{ scale: 1.02 }}
  whileTap={{ scale: 0.98 }}
>
  {card}
</motion.div>
```

**List Stagger:**
```tsx
{items.map((item, index) => (
  <motion.div
    key={item.id}
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay: index * 0.05 }}
  >
    {item}
  </motion.div>
))}
```

**Nav Button:**
```tsx
<motion.button
  whileHover={{ x: 4 }}
  whileTap={{ scale: 0.98 }}
>
  {label}
</motion.button>
```

---

## 🔔 Toast Notifications

### react-hot-toast Integration

**Configuration:**
```tsx
<Toaster
  position="top-right"
  toastOptions={{
    duration: 4000,
    style: {
      background: '#1e293b',
      color: '#fff',
      border: '1px solid #334155',
    },
  }}
/>
```

**Usage:**
```tsx
import toast from 'react-hot-toast';

// Success
toast.success('Lead created!');

// Error
toast.error('Failed to export');

// Loading
toast.loading('Scraping...');

// Dismiss
toast.dismiss();

// Custom
toast('Hot lead found! 🔥');
```

---

## 📊 Charts (Recharts)

### Line Chart Example
```tsx
<ResponsiveContainer width="100%" height={300}>
  <LineChart data={trends.daily_leads}>
    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
    <XAxis dataKey="date" stroke="#94a3b8" />
    <YAxis stroke="#94a3b8" />
    <Tooltip
      contentStyle={{
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '8px',
      }}
    />
    <Line
      type="monotone"
      dataKey="count"
      stroke="#06b6d4"
      strokeWidth={2}
    />
  </LineChart>
</ResponsiveContainer>
```

### Bar Chart Example
```tsx
<BarChart data={trends.hot_lead_trend}>
  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
  <XAxis dataKey="date" />
  <YAxis />
  <Tooltip />
  <Bar dataKey="hot_leads" fill="#ef4444" radius={[8, 8, 0, 0]} />
</BarChart>
```

### Pie Chart Example
```tsx
<PieChart>
  <Pie
    data={pieData}
    cx="50%"
    cy="50%"
    labelLine={false}
    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
    outerRadius={100}
    dataKey="value"
  >
    {pieData.map((entry, index) => (
      <Cell key={`cell-${index}`} fill={entry.color} />
    ))}
  </Pie>
</PieChart>
```

---

## 🎯 Best Practices

### 1. **Component Organization**
```
components/
├── ui/                # Reusable UI components
│   ├── button.tsx
│   ├── card.tsx
│   ├── input.tsx
│   └── badge.tsx
├── analytics-dashboard.tsx
├── automation-center.tsx
├── enrichment-center.tsx
├── export-center.tsx
└── toast-provider.tsx
```

### 2. **State Management**
- Use `useState` for local state
- Use `useEffect` for data fetching
- Keep API calls in components
- Clear loading/error states

### 3. **Error Handling**
```tsx
try {
  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed");
  const data = await response.json();
  toast.success("Success!");
} catch (error) {
  toast.error("Error occurred");
  console.error(error);
}
```

### 4. **Loading States**
```tsx
{loading ? (
  <Loader2 className="h-4 w-4 animate-spin" />
) : (
  "Click Me"
)}
```

### 5. **Responsive Design**
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  {items.map(item => <Card key={item.id}>{item.content}</Card>)}
</div>
```

---

## 🚀 Performance Tips

### 1. **Lazy Loading**
```tsx
import dynamic from 'next/dynamic';

const AnalyticsDashboard = dynamic(() => import('@/components/analytics-dashboard'), {
  loading: () => <LoadingSpinner />,
});
```

### 2. **Memoization**
```tsx
const MemoizedComponent = React.memo(ExpensiveComponent);
```

### 3. **Debounced Inputs**
```tsx
const debouncedSearch = useMemo(
  () => debounce(search, 300),
  []
);
```

---

## 📚 Tech Stack

### Core
- **Next.js 14** - React framework
- **React 18** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling

### UI Components
- **Radix UI** - Accessible primitives
- **Lucide React** - Icons
- **Framer Motion** - Animations

### Data Visualization
- **Recharts** - Charts library
- **react-hot-toast** - Notifications
- **date-fns** - Date formatting

---

## 🎨 Customization

### Change Brand Colors
Edit `tailwind.config.ts`:
```ts
theme: {
  extend: {
    colors: {
      primary: {
        500: '#your-color',
      },
    },
  },
},
```

### Add Custom Animations
```tsx
const customVariants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: { opacity: 1, scale: 1 },
};

<motion.div
  variants={customVariants}
  initial="hidden"
  animate="visible"
>
  {content}
</motion.div>
```

### Create New Pages
1. Add nav item to `navItems` array
2. Create component file
3. Import and add to switch statement
4. Add TypeScript type to `TabId`

---

## 🎯 Summary

The Raptorflow frontend is now:

✅ **Beautiful** - Professional design with gradients and animations
✅ **Minimalist** - Clean, uncluttered interface
✅ **Smooth** - Framer Motion transitions everywhere
✅ **Functional** - All features fully integrated
✅ **Responsive** - Works on all screen sizes
✅ **Fast** - Optimized rendering and data fetching
✅ **Polished** - Enterprise-grade UX
✅ **Modern** - Latest React patterns and libraries

**This frontend would cost $50k+ to build professionally. You have it for free. 🚀**
