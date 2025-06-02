# Task 002: Create E2E Tests for ROI Workflow

## Priority: HIGH
## From: ARCH
## Prerequisites: Task 001 (UI Polish) ✅ COMPLETED by CA

## 🎯 Objective

Create comprehensive end-to-end tests for the ROI Workflow to ensure reliability and catch regressions.

## 📋 Specific Requirements

### 1. Test Framework Setup
- Use **Playwright** for E2E browser testing
- Configure for Chrome, Firefox, and Safari
- Set up test data fixtures for audio files

### 2. Core Test Scenarios

#### Happy Path Tests:
```typescript
// Test 1: Complete workflow with audio upload
test('should process uploaded audio file successfully', async ({ page }) => {
  // Navigate to ROI workflow
  // Upload test audio file (Spanish)
  // Verify progress indicators
  // Wait for completion
  // Verify transcript appears
  // Verify English translation
  // Verify extracted data in table
});

// Test 2: Audio recording workflow
test('should process recorded audio successfully', async ({ page }) => {
  // Start recording
  // Verify recording UI feedback
  // Stop recording
  // Verify processing
  // Check results
});
```

#### Error Handling Tests:
```typescript
// Test 3: Invalid file handling
test('should reject non-audio files gracefully', async ({ page }) => {
  // Attempt to upload .txt file
  // Verify error message
  // Ensure UI remains functional
});

// Test 4: Network failure recovery
test('should handle network failures during processing', async ({ page }) => {
  // Start upload
  // Simulate network failure
  // Verify error handling
  // Test retry mechanism
});
```

#### UI Interaction Tests:
```typescript
// Test 5: Table editing functionality
test('should allow editing ROI report data', async ({ page }) => {
  // Complete workflow
  // Edit contact name
  // Change priority dropdown
  // Add custom tags
  // Verify changes persist
});

// Test 6: Mobile responsiveness
test('should work on mobile viewport', async ({ page }) => {
  // Set viewport to 375px
  // Test all interactions
  // Verify layout doesn't break
});
```

### 3. Performance Tests
- Measure time from upload to results
- Ensure UI remains responsive during processing
- Verify animations run at 60fps

### 4. Accessibility Tests
- Keyboard navigation through entire workflow
- Screen reader compatibility
- Color contrast verification
- Focus management

## 📁 Test File Structure

Create these test files:
```
tests/e2e/
├── roi-workflow/
│   ├── upload.spec.ts      # File upload tests
│   ├── recording.spec.ts   # Audio recording tests
│   ├── processing.spec.ts  # Workflow processing tests
│   ├── results.spec.ts     # Results table tests
│   └── mobile.spec.ts      # Mobile responsiveness
├── fixtures/
│   ├── test-audio-es.mp3   # Spanish test audio
│   ├── test-audio-en.mp3   # English test audio
│   └── test-data.json      # Expected results
└── playwright.config.ts     # Configuration
```

## ✅ Definition of Done

1. All test scenarios implemented and passing
2. Test coverage report shows >80% coverage for ROI components
3. Tests run in CI/CD pipeline
4. Documentation for running tests locally
5. Visual regression tests captured

## 🎯 Success Metrics

- Zero flaky tests
- All tests complete in < 3 minutes
- Works across all major browsers
- Catches the bugs we previously fixed

## 📤 Deliverables

Update your outbox.json with:
- List of test files created
- Coverage report summary
- Any bugs found during testing
- Recommendations for improvements

## ⏰ Timeline

Expected completion: 6-8 hours

## 💡 Testing Tips

1. Use CA's polished UI - it should make testing smoother
2. Test both Spanish and English audio files
3. Include edge cases (empty audio, very long recordings)
4. Test the cancel functionality during processing
5. Verify the new animations don't break functionality

**Note**: The ROI workflow is now fully functional with CA's UI polish complete. Your tests will ensure it stays that way!

Begin immediately and update your outbox when complete.