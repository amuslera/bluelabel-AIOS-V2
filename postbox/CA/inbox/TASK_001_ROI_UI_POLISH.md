# Task 001: ROI Workflow UI Polish

## Priority: URGENT
## From: ARCH
## Status: SINGLE FOCUSED TASK

**IMPORTANT**: Please ignore all previous task assignments. This is your ONLY current task.

## 🎯 Single Objective

Polish the ROI Workflow UI to make it beautiful and user-friendly.

## 📁 Files to Modify

1. `apps/ui/src/components/ROIWorkflow/AudioUploader.tsx`
2. `apps/ui/src/components/ROIWorkflow/ResultsTable.tsx`
3. `apps/ui/src/components/ROIWorkflow/WorkflowProgress.tsx`
4. `apps/ui/src/components/ROIWorkflow/ROIWorkflowContainer.tsx`

## 🔧 Specific Improvements Required

### 1. AudioUploader.tsx
```typescript
// Add these improvements:
- Smooth hover transitions on buttons (transition-all duration-200)
- Visual feedback during recording (pulsing red dot)
- Better spacing between elements (use gap-4)
- Rounded corners on all buttons (rounded-lg)
- Success animation when file uploads
```

### 2. ResultsTable.tsx
```typescript
// Enhance the table:
- Add zebra striping (even:bg-gray-50)
- Hover effects on rows (hover:bg-blue-50)
- Smooth transitions on all interactions
- Better padding (px-6 py-4)
- Sticky header for long lists
```

### 3. WorkflowProgress.tsx
```typescript
// Improve progress indicators:
- Animated progress bar
- Smooth step transitions
- Better visual hierarchy
- Success checkmarks with animation
- Clearer status messages
```

### 4. Global Improvements
- Consistent spacing (use multiples of 4px)
- Subtle shadows instead of borders
- Smooth color transitions
- Loading skeletons instead of spinners

## ✅ Definition of Done

1. All buttons have hover states
2. All transitions are smooth (200-300ms)
3. Consistent spacing throughout
4. Mobile responsive (test at 375px width)
5. No accessibility violations

## 📤 Deliverable

Update your outbox.json with:
- Task completion status
- List of files modified
- Any issues encountered
- Screenshots of the polished UI

## ⏰ Timeline

Expected completion: 4-6 hours

Please begin immediately and update your outbox when complete. Do NOT start any other tasks until this is done.