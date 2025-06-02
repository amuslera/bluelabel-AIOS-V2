# ROI Workflow E2E Test Suite

Comprehensive end-to-end tests for the ROI Workflow feature built with Playwright.

## Overview

This test suite ensures the ROI Workflow functions correctly across all scenarios:
- File upload and audio recording
- Processing pipeline (transcription, translation, extraction)
- Results display and interaction
- Error handling and edge cases
- Mobile responsiveness
- Accessibility compliance

## Test Structure

```
tests/e2e/roi-workflow/
├── upload.spec.ts          # File upload functionality
├── recording.spec.ts       # Audio recording features
├── processing.spec.ts      # Workflow processing stages
├── results.spec.ts         # Results table interactions
├── mobile.spec.ts          # Mobile/tablet responsiveness
├── error-handling.spec.ts  # Error scenarios & edge cases
└── accessibility.spec.ts   # WCAG compliance tests
```

## Running Tests

### Prerequisites
1. Ensure the API server is running: `uvicorn apps.api.main:app --reload`
2. Install dependencies: `cd apps/ui && npm install`

### Test Commands

```bash
# Run all E2E tests
npm run test:e2e

# Run tests with browser visible
npm run test:e2e:headed

# Debug specific test
npm run test:e2e:debug

# Run only accessibility tests
npm run test:a11y

# Run only mobile tests
npm run test:mobile

# Run comprehensive test suite with reporting
./scripts/run_e2e_tests.sh
```

## Test Coverage

### Core Functionality Tests
- ✅ File upload with validation
- ✅ Audio recording with permissions
- ✅ Processing workflow stages
- ✅ Real-time progress updates
- ✅ Results table display and editing
- ✅ Export functionality (CSV, JSON)

### Error Handling Tests
- ✅ Network failures and retries
- ✅ Invalid file formats
- ✅ Service unavailability
- ✅ Session timeout
- ✅ Rate limiting
- ✅ Corrupted files

### Mobile & Accessibility Tests
- ✅ Responsive layouts (mobile, tablet)
- ✅ Touch interactions
- ✅ WCAG 2.1 AA compliance
- ✅ Keyboard navigation
- ✅ Screen reader support
- ✅ High contrast mode

## Test Data

### Audio Files Used
- `test_real_audio.mp3` - Spanish audio for translation testing
- `test_meeting.wav` - English audio for processing
- `test_real.wav` - General testing file

### Expected Results
Test fixtures in `fixtures/test-data.json` define expected outcomes for:
- Transcript content
- Translation results
- Extracted contact information
- Data structure validation

## Browser Coverage

Tests run across:
- **Desktop**: Chrome, Firefox, Safari
- **Mobile**: iOS Safari, Android Chrome
- **Tablet**: iPad Pro

## Performance Metrics

Tests verify:
- Upload completion < 5 seconds
- Processing completion < 60 seconds
- UI responsiveness during operations
- Animation performance (60fps)

## Accessibility Standards

Compliance with:
- WCAG 2.1 Level AA
- Section 508
- Keyboard navigation requirements
- Screen reader compatibility

## CI/CD Integration

Tests are configured for:
- Headless execution in CI
- Screenshot capture on failures
- Video recording for debugging
- HTML reports generation

## Debugging

### Failed Tests
1. Check HTML report: `npx playwright show-report`
2. View screenshots in `test-results/`
3. Watch recorded videos for complex interactions

### Common Issues
- **Network timeouts**: Increase timeout in `playwright.config.ts`
- **File upload failures**: Verify file paths in test specs
- **Mobile tests failing**: Check viewport settings
- **Accessibility violations**: Review axe-core output

## Contributing

When adding new tests:
1. Follow existing naming conventions
2. Use page object model patterns
3. Include both happy path and error scenarios
4. Verify mobile responsiveness
5. Test accessibility compliance
6. Add appropriate test data fixtures

## Reports

Test results include:
- **HTML Report**: Visual test results with screenshots
- **JUnit XML**: For CI/CD integration  
- **JSON Report**: Raw test data for analysis
- **Coverage Report**: Feature coverage metrics

## Maintenance

Regular tasks:
- Update test data as features evolve
- Refresh browser installations
- Review and update timeout values
- Validate test assertions against UI changes