# Frontend Wireframes

ASCII-art wireframes showing the layout and structure of key pages in the Bluelabel AIOS frontend.

## Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ BLUELABEL AIOS                                          [_][□][X] │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌───────────┐                                                               │
│ │ DASHBOARD │ INBOX  AGENTS  KNOWLEDGE  LOGS  TERMINAL                      │
│ └───────────┘                                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐   │
│  │ SYSTEM STATUS      │ │ ACTIVE AGENTS       │ │ RECENT ACTIVITY     │   │
│  │ ┌─────────────────┐│ │ ┌─────────────────┐│ │ ┌─────────────────┐│   │
│  │ │ OPERATIONAL     ││ │ │ ContentMind  ⚡  ││ │ │ Email processed  ││   │
│  │ │ ████████████    ││ │ │ WebFetcher   ✓  ││ │ │ 10:42 AM        ││   │
│  │ │ 98.5% uptime    ││ │ │ DigestAgent  ○  ││ │ │                 ││   │
│  │ └─────────────────┘│ │ └─────────────────┘│ │ │ Knowledge added ││   │
│  │                    │ │                    │ │ │ 10:38 AM        ││   │
│  │ CPU: ████░░ 45%    │ │ 2/3 Active        │ │ └─────────────────┘│   │
│  │ MEM: ███░░░ 62%    │ │                    │ │                    │   │
│  │ DISK: ██░░░ 34%    │ │ [MANAGE AGENTS]   │ │ [VIEW ALL]        │   │
│  └─────────────────────┘ └─────────────────────┘ └─────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ QUICK STATS                                                         │   │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │   │
│  │ │  247    │ │  1,523  │ │  89     │ │  12     │ │  98.5%  │      │   │
│  │ │ EMAILS  │ │ DOCS    │ │ TASKS   │ │ ERRORS  │ │ SUCCESS │      │   │
│  │ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Terminal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ BLUELABEL AIOS                                          [_][□][X] │
├─────────────────────────────────────────────────────────────────────────────┤
│ DASHBOARD  INBOX  AGENTS  KNOWLEDGE  LOGS  ┌──────────┐                     │
│                                           │ TERMINAL │                     │
│                                           └──────────┘                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ ╔═══════════════════════════════════════════════════════════════════════╗ │
│ ║ TERMINAL                                                              ║ │
│ ╠═══════════════════════════════════════════════════════════════════════╣ │
│ ║ > system initialization complete                                      ║ │
│ ║ > loading agent modules...                                           ║ │
│ ║ > ready for input                                                    ║ │
│ ║                                                                       ║ │
│ ║ > status                                                             ║ │
│ ║ SYSTEM STATUS: ONLINE                                                 ║ │
│ ║                                                                       ║ │
│ ║ content_mind    [OK]                                                  ║ │
│ ║ email_gateway   [OK]                                                  ║ │
│ ║ model_router    [OK]                                                  ║ │
│ ║ redis          [OK]                                                  ║ │
│ ║                                                                       ║ │
│ ║ > agent list                                                         ║ │
│ ║ ContentMind     [ONLINE]  Content analysis and summarization         ║ │
│ ║ WebFetcher      [ONLINE]  Web content extraction                     ║ │
│ ║ DigestAgent     [OFFLINE] Daily digest creation                      ║ │
│ ║                                                                       ║ │
│ ║ > run ContentMind --input "analyze Q1 report"                        ║ │
│ ║ [10:42:15] Starting ContentMind agent...                             ║ │
│ ║ [10:42:15] Processing input: "analyze Q1 report"                     ║ │
│ ║ [10:42:17] Analysis complete.                                        ║ │
│ ║                                                                       ║ │
│ ║ SUMMARY:                                                             ║ │
│ ║ ────────                                                             ║ │
│ ║ Q1 showed strong revenue growth of 23% YoY...                        ║ │
│ ║                                                                       ║ │
│ ║ > _                                                                  ║ │
│ ╚═══════════════════════════════════════════════════════════════════════╝ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Inbox

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ BLUELABEL AIOS                                          [_][□][X] │
├─────────────────────────────────────────────────────────────────────────────┤
│ DASHBOARD  ┌───────┐ AGENTS  KNOWLEDGE  LOGS  TERMINAL                      │
│           │ INBOX │                                                        │
│           └───────┘                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FILTERS: [ALL ▼] [UNPROCESSED ▼] [EMAIL ▼]           🔍 Search...         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ID    FROM              SUBJECT              TIME    STATUS  ACTION │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ E047  john@example.com  [process] Q1 Report  10:42   ✓      [VIEW] │   │
│  │       "Please analyze the attached quarterly report..."           │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ W046  +1234567890      Meeting tomorrow?     10:38   ✓      [VIEW] │   │
│  │       "Can we meet at 3pm to discuss the project?"               │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ E045  sarah@company.com [analyze] Budget doc  10:30   ⚡     [RUN]  │   │
│  │       "Need analysis of the budget spreadsheet attached"          │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ E044  client@xyz.com    Contract review      10:15   ○      [RUN]  │   │
│  │       "Please review this contract for any issues"                │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ W043  +9876543210      [urgent] Call me       09:45   ✓      [VIEW] │   │
│  │       "Need to discuss urgent matter"                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LEGEND: ✓ Processed  ⚡ Processing  ○ Pending  ⚠ Error                    │
│                                                                             │
│  [MARK AS READ] [PROCESS SELECTED] [ARCHIVE] [DELETE]                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Knowledge Repository

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ BLUELABEL AIOS                                          [_][□][X] │
├─────────────────────────────────────────────────────────────────────────────┤
│ DASHBOARD  INBOX  AGENTS  ┌───────────┐ LOGS  TERMINAL                      │
│                          │ KNOWLEDGE │                                     │
│                          └───────────┘                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🔍 Search knowledge base...                    [+ ADD NEW] [↓ EXPORT]      │
│                                                                             │
│  FILTERS: [ALL TYPES ▼] [ALL SOURCES ▼] [DATE: LAST 30 DAYS ▼]            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐        │   │
│  │ │ Q1 Financial    │ │ Marketing Plan  │ │ Tech Stack Doc  │        │   │
│  │ │ Summary        │ │ 2024           │ │                │        │   │
│  │ │                │ │                │ │                │        │   │
│  │ │ 📄 PDF         │ │ 📝 MARKDOWN    │ │ 📊 SPREADSHEET │        │   │
│  │ │ Finance, Q1    │ │ Marketing      │ │ Technical      │        │   │
│  │ │ Mar 15, 2024   │ │ Mar 10, 2024   │ │ Mar 8, 2024    │        │   │
│  │ └─────────────────┘ └─────────────────┘ └─────────────────┘        │   │
│  │                                                                     │   │
│  │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐        │   │
│  │ │ Meeting Notes   │ │ Research: AI    │ │ Competitor     │        │   │
│  │ │ Board Meeting  │ │ Trends         │ │ Analysis       │        │   │
│  │ │                │ │                │ │                │        │   │
│  │ │ 📝 NOTES       │ │ 🔗 WEB         │ │ 📄 PDF         │        │   │
│  │ │ Meeting, Board │ │ AI, Research   │ │ Analysis       │        │   │
│  │ │ Mar 5, 2024    │ │ Mar 1, 2024    │ │ Feb 28, 2024   │        │   │
│  │ └─────────────────┘ └─────────────────┘ └─────────────────┘        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Showing 6 of 1,523 documents                              [1] 2 3 ... 254  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Agent Management

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ BLUELABEL AIOS                                          [_][□][X] │
├─────────────────────────────────────────────────────────────────────────────┤
│ DASHBOARD  INBOX  ┌────────┐ KNOWLEDGE  LOGS  TERMINAL                      │
│                  │ AGENTS │                                               │
│                  └────────┘                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AGENT MANAGEMENT                                    [+ CREATE] [⚙ CONFIG]  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ┌───────────────────────────────────────┐                           │   │
│  │ │ ContentMind                          │ STATUS: ONLINE ⚡         │   │
│  │ │                                      │ UPTIME: 99.8%            │   │
│  │ │ Content analysis and summarization   │ AVG TIME: 2.3s          │   │
│  │ │                                      │ SUCCESS: 98.5%          │   │
│  │ │ Provider: Ollama                     │                         │   │
│  │ │ Model: llama3                        │ Last Run: 2 min ago     │   │
│  │ │ Temperature: 0.7                     │                         │   │
│  │ │                                      │ [CONFIGURE] [LOGS]      │   │
│  │ └───────────────────────────────────────┘                           │   │
│  │                                                                     │   │
│  │ ┌───────────────────────────────────────┐                           │   │
│  │ │ WebFetcher                           │ STATUS: ONLINE ✓         │   │
│  │ │                                      │ UPTIME: 99.9%            │   │
│  │ │ Web content extraction and parsing   │ AVG TIME: 1.2s          │   │
│  │ │                                      │ SUCCESS: 99.5%          │   │
│  │ │ Provider: Local                      │                         │   │
│  │ │ Model: N/A                           │ Last Run: 5 min ago     │   │
│  │ │ Timeout: 30s                         │                         │   │
│  │ │                                      │ [CONFIGURE] [LOGS]      │   │
│  │ └───────────────────────────────────────┘                           │   │
│  │                                                                     │   │
│  │ ┌───────────────────────────────────────┐                           │   │
│  │ │ DigestAgent                          │ STATUS: OFFLINE ○        │   │
│  │ │                                      │ UPTIME: --               │   │
│  │ │ Daily digest creation and delivery   │ AVG TIME: --            │   │
│  │ │                                      │ SUCCESS: --             │   │
│  │ │ Provider: OpenAI                     │                         │   │
│  │ │ Model: gpt-4                         │ Last Run: Never         │   │
│  │ │ Schedule: Daily @ 9am                │                         │   │
│  │ │                                      │ [CONFIGURE] [ACTIVATE]  │   │
│  │ └───────────────────────────────────────┘                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Logs Viewer

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ BLUELABEL AIOS                                          [_][□][X] │
├─────────────────────────────────────────────────────────────────────────────┤
│ DASHBOARD  INBOX  AGENTS  KNOWLEDGE  ┌──────┐ TERMINAL                      │
│                                     │ LOGS │                              │
│                                     └──────┘                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SYSTEM LOGS                                                               │
│                                                                             │
│  LEVEL: [ALL ▼] [INFO ▼] [WARN ▼] [ERROR ▼]    🔍 Filter...  [↓ EXPORT]   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ [10:45:23] [INFO]  ContentMind: Starting analysis for doc K2451     │   │
│  │ [10:45:24] [INFO]  API: Request from 192.168.1.101 /api/v1/agents  │   │
│  │ [10:45:25] [INFO]  ContentMind: Analysis complete (2.3s)           │   │
│  │ [10:45:26] [WARN]  Redis: Connection pool at 80% capacity          │   │
│  │ [10:45:27] [INFO]  Knowledge: Document K2451 saved successfully    │   │
│  │ [10:45:28] [ERROR] EmailGateway: Failed to connect to SMTP server  │   │
│  │   Error Details: Connection timeout after 30s                      │   │
│  │   Stack Trace: at EmailGateway.connect (line 245)                 │   │
│  │ [10:45:29] [INFO]  EmailGateway: Retrying connection...           │   │
│  │ [10:45:30] [INFO]  EmailGateway: Connection established           │   │
│  │ [10:45:31] [INFO]  System: Scheduled maintenance in 2 hours       │   │
│  │ [10:45:32] [INFO]  WebFetcher: Processing URL https://example.com │   │
│  │ [10:45:33] [INFO]  WebFetcher: Content extracted successfully     │   │
│  │ [10:45:34] [WARN]  ModelRouter: Fallback to secondary provider    │   │
│  │ [10:45:35] [INFO]  DigestAgent: Daily digest scheduled for 9am    │   │
│  │ [10:45:36] [INFO]  System: Health check passed                    │   │
│  │ [10:45:37] [INFO]  API: 247 requests processed in last hour       │   │
│  │                                                                    │▼  │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [⏸ PAUSE] [🔄 REFRESH] [📊 STATS] [⚙ SETTINGS]                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Modal Examples

### Knowledge Detail Modal

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DOCUMENT DETAILS                         [X]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Title: Q1 Financial Summary 2024                                   │
│  Type: PDF Document                                                 │
│  Size: 2.4 MB                                                       │
│  Created: March 15, 2024 10:42 AM                                  │
│  Source: Email (john@example.com)                                   │
│  Tags: finance, quarterly, report, 2024                            │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ SUMMARY                                                       │ │
│  │                                                               │ │
│  │ The Q1 2024 financial report shows strong performance across  │ │
│  │ all business units with revenue growth of 23% year-over-year. │ │
│  │ Key highlights include successful product launches and        │ │
│  │ expansion into new markets...                                 │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  KEY ENTITIES:                                                      │
│  • Revenue: $45.2M                                                  │
│  • Growth: 23% YoY                                                  │
│  • New Markets: APAC, LATAM                                        │
│  • Products: CloudSync Pro, DataVault                              │
│                                                                     │
│  [📄 VIEW FULL] [📥 DOWNLOAD] [✏️ EDIT] [🗑️ DELETE]               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### File Upload Modal

```
┌─────────────────────────────────────────────────────────────────────┐
│                        UPLOAD FILES                          [X]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                                                               │ │
│  │                     ┌─────────────────┐                       │ │
│  │                     │                 │                       │ │
│  │                     │   📁 DROP HERE  │                       │ │
│  │                     │                 │                       │ │
│  │                     └─────────────────┘                       │ │
│  │                                                               │ │
│  │              Drag files here or click to browse               │ │
│  │                                                               │ │
│  │            Supported: PDF, TXT, MD, CSV, JSON, DOC            │ │
│  │                    Maximum size: 10MB                         │ │
│  │                                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  SELECTED FILES:                                                    │
│  • report.pdf (2.4 MB)                                             │
│  • notes.txt (124 KB)                                              │
│  • data.csv (892 KB)                                               │
│                                                                     │
│  Tags: [finance] [quarterly] [+ADD TAG]                            │
│                                                                     │
│  [UPLOAD] [CANCEL]                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Mobile Responsive View (Future)

```
┌─────────────────────┐
│ BLUELABEL AIOS  ☰  │
├─────────────────────┤
│ ┌─────────────────┐ │
│ │ SYSTEM: ONLINE  │ │
│ │ ████████ 98.5%  │ │
│ └─────────────────┘ │
│                     │
│ RECENT ACTIVITY     │
│ ┌─────────────────┐ │
│ │ Email processed │ │
│ │ 10:42 AM       │ │
│ ├─────────────────┤ │
│ │ Doc added       │ │
│ │ 10:38 AM       │ │
│ └─────────────────┘ │
│                     │
│ QUICK ACTIONS       │
│ [📧 INBOX]          │
│ [⚡ RUN AGENT]      │
│ [📚 KNOWLEDGE]      │
│ [💻 TERMINAL]       │
│                     │
└─────────────────────┘
```

---

Last Updated: January 2025
Version: 1.0.0