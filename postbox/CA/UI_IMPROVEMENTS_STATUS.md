# ROI Workflow UI Improvements Status

## Completed Tasks ✅

### 1. Make Contact Type & Priority Editable
- Added `EditableSelectCell` component to `ResultsTable.tsx`
- Contact Type: dropdown with "prospective" | "existing" options
- Priority: dropdown with "high" | "medium" | "low" options
- Maintains consistent styling with existing color-coded badges

### 2. Increased Font Size Globally
- Updated `tailwind.config.js` font sizes:
  - Base: 18px → 20px
  - Large: 20px → 24px
  - XL: 24px → 28px
  - And proportional increases for all sizes
- All pages now have larger, more readable text
- Retro terminal aesthetic preserved

## Next Priority Tasks 🚀

### 3. Audio Recording UI (Most Requested)
Need to update `AudioUploader.tsx` to add:
- "Record Audio" button alongside "Select File"
- Browser MediaRecorder API integration
- Recording timer and waveform visualization
- Voice template display during recording

### 4. Multi-File Workflow Support
Update `ROIWorkflowContainer.tsx` for:
- "Upload Another" button after first upload
- Multiple transcript display
- Append results to existing table
- "Clear All" button

### 5. Batch Upload with Drag-and-Drop
- Accept multiple files in dropzone
- Show progress for each file
- Display results as they complete

## Backend Requirements
CB is working on:
- `/roi/upload-batch` endpoint
- `/roi/record` endpoint
- `/roi/workflows/merge` endpoint
- `/roi/recording-template` endpoint

Would you like me to proceed with Task 3 (Audio Recording UI)?