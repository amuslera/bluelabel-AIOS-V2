# 🎤 ROI Report Automation – Voice-to-Table Workflow

## 🎯 Goal

Transform voice notes recorded after client meetings into structured ROI reports by extracting key metadata and exporting the results as a CSV file and an on-screen table.

---

## 🔁 Workflow Overview

### 1. Audio Recording (User Input)
- The user records a short voice memo right after a meeting.
- The memo follows a simple, natural template:
  - In English:  
    *“I just met with [Name] from [Company], who is their [Position]. We discussed [Discussion]. This is a [prospective/existing] client, and the priority is [high/medium/low]. The action items are: [Action Items].”*
  - In Spanish:  
    *“Acabo de reunirme con [Nombre] de [Empresa], que es su [Puesto]. Hablamos sobre [Temas tratados]. Es un/a [cliente actual/potencial] y lo/la considero de prioridad [alta/media/baja]. Los próximos pasos son: [Acciones].”*

### 2. File Delivery
- The audio file is received (e.g., via WhatsApp or email).
- The file is manually uploaded into the **Bluelabel AIOS** agent interface.

### 3. Agent Processing Pipeline
- A specialized agent (or sequence of agents) performs the following:

#### a. Transcription Agent
- Uses OpenAI Whisper or similar.
- Detects and transcribes both Spanish and English audio.

#### b. Parsing Agent
- Extracts the following metadata from the transcript:
  - `Name`
  - `Company`
  - `Position`
  - `Discussion`
  - `Contact Type` (Prospective or Existing)
  - `Priority Level` (High / Medium / Low)
  - `Action Items`

### 4. Output
- A table is rendered on-screen with the extracted information.
- A `.csv` file is generated for download or further processing (e.g., syncing to Google Sheets or CRM).

---

## 🌍 Language Support

- Fully supports **Spanish and English**.
- Auto-detects language and adjusts parsing accordingly.

---

## 📋 Implementation Status & Bug Fixes

### ✅ Current Status (v1.0.1 - January 2025)
The ROI workflow automation is **fully functional** with the following capabilities:
- ✅ Audio upload via web interface (supports .mp3, .wav, .webm, etc.)
- ✅ Real-time transcription using OpenAI Whisper API
- ✅ Spanish-to-English translation for non-English audio
- ✅ Structured data extraction into contact fields
- ✅ Interactive table display with editable cells
- ✅ Custom Contact Type and Priority tags
- ✅ Support for multiple contacts per recording
- ✅ Audio recording directly from browser

### 🐛 Recent Bug Fixes (v1.0.1)

#### Critical Translation Bug (Fixed)
**Issue**: Spanish audio was not being translated to English - both "Original" and "English Translation" fields showed the same Spanish text.

**Root Cause**: The extraction step was overwriting the `extracted_data` field that contained the English translation from the translation step.

**Fix**: Implemented proper data merging in the extraction step to preserve translation data:
```python
# Before (Bug):
workflow.extracted_data = result["extracted_data"]  # Overwrote translation!

# After (Fixed):
merged_data = workflow.extracted_data.copy()
merged_data.update(result["extracted_data"])  # Preserves translation
workflow.extracted_data = merged_data
```

#### Empty Table Fields Bug (Fixed)
**Issue**: Contact information fields (Name, Company, Position, etc.) were appearing as "Not specified" despite successful extraction.

**Root Cause**: SQLAlchemy was not properly tracking changes to JSONB fields when using in-place dictionary updates.

**Fix**: Changed from in-place updates to proper object reassignment for SQLAlchemy change tracking.

#### Background Processing Issues (Fixed)
**Issue**: Workflows were completing immediately without proper processing due to database session management issues in async background tasks.

**Fix**: Implemented proper database session handling for background workflow processing.

### 🧪 Validated Functionality
- [x] Spanish audio → English translation → Structured data
- [x] English audio → Direct processing → Structured data  
- [x] Multi-step workflow pipeline (transcription → translation → extraction)
- [x] Real-time status updates and progress tracking
- [x] All contact fields populating correctly
- [x] Custom tags and editable table cells
- [x] Audio recording and file upload

---

## 🧱 Future Enhancements

- Auto-ingestion from WhatsApp or email inbox.
- Direct integration with Notion or CRM systems.
- Semantic tagging by topic or legal area.
- Email draft generation based on action items.

