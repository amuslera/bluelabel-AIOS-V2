import { test, expect, devices } from '@playwright/test';
import path from 'path';

// Test on mobile devices
test.use({ ...devices['iPhone 13'] });

test.describe('ROI Workflow - Mobile Responsiveness', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/roi-workflow');
    await page.waitForLoadState('networkidle');
  });

  test('should adapt layout for mobile viewport', async ({ page }) => {
    // Verify mobile layout
    await expect(page.locator('[data-testid="mobile-layout"]')).toBeVisible();
    
    // Check that desktop-only elements are hidden
    await expect(page.locator('[data-testid="desktop-sidebar"]')).not.toBeVisible();
    
    // Verify mobile-optimized buttons are visible
    await expect(page.getByRole('button', { name: /Start Recording/i })).toBeVisible();
    await expect(page.getByText(/Tap to upload/i)).toBeVisible();
  });

  test('should handle touch interactions for file upload', async ({ page }) => {
    // Tap upload area
    await page.locator('[data-testid="upload-area"]').tap();
    
    // Verify file input triggered
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeFocused();
  });

  test('should use native recording interface on mobile', async ({ page, context }) => {
    await context.grantPermissions(['microphone']);
    
    // Tap recording button
    await page.getByRole('button', { name: /Start Recording/i }).tap();
    
    // Verify mobile recording UI
    await expect(page.locator('[data-testid="mobile-recording-ui"]')).toBeVisible();
    
    // Check for larger touch targets
    const stopButton = page.getByRole('button', { name: /Stop Recording/i });
    const buttonSize = await stopButton.boundingBox();
    expect(buttonSize?.height).toBeGreaterThan(44); // iOS touch target minimum
  });

  test('should optimize table display for mobile', async ({ page }) => {
    // Mock completed workflow
    await page.route('**/api/roi-workflow/*/status', async route => {
      const response = {
        status: 'completed',
        results: [{
          contactName: 'John Doe',
          role: 'Manager',
          organization: 'ACME Corp',
          priority: 'HIGH',
          nextSteps: 'Follow up next week',
          tags: ['meeting', 'important']
        }]
      };
      await route.fulfill({ json: response });
    });
    
    const audioFile = path.join(__dirname, '../../../test_real_audio.mp3');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    await page.getByRole('button', { name: /Process Audio/i }).tap();
    
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ timeout: 30000 });
    
    // Verify mobile table layout (cards instead of table)
    await expect(page.locator('[data-testid="mobile-cards-view"]')).toBeVisible();
    await expect(page.locator('table')).not.toBeVisible();
    
    // Verify swipe gestures work on cards
    const firstCard = page.locator('[data-testid="contact-card"]').first();
    await firstCard.swipe('left');
    
    // Verify action menu appears
    await expect(page.locator('[data-testid="card-actions"]')).toBeVisible();
  });

  test('should handle orientation changes', async ({ page }) => {
    // Start in portrait
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Verify portrait layout
    await expect(page.locator('[data-testid="portrait-layout"]')).toBeVisible();
    
    // Change to landscape
    await page.setViewportSize({ width: 667, height: 375 });
    
    // Verify landscape layout adapts
    await expect(page.locator('[data-testid="landscape-layout"]')).toBeVisible();
    
    // Verify recording UI adjusts
    const recordButton = page.getByRole('button', { name: /Start Recording/i });
    const buttonBox = await recordButton.boundingBox();
    expect(buttonBox?.y).toBeLessThan(200); // Button should move up in landscape
  });

  test('should optimize progress display for mobile', async ({ page }) => {
    const audioFile = path.join(__dirname, '../../../test_meeting.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).tap();
    
    // Verify mobile progress layout
    await expect(page.locator('[data-testid="mobile-progress"]')).toBeVisible();
    
    // Check that progress steps stack vertically
    const progressSteps = page.locator('[data-testid="progress-step"]');
    const firstStep = progressSteps.first();
    const secondStep = progressSteps.nth(1);
    
    const firstBox = await firstStep.boundingBox();
    const secondBox = await secondStep.boundingBox();
    
    // Steps should be stacked vertically (second step below first)
    expect(secondBox?.y).toBeGreaterThan(firstBox?.y);
  });

  test('should handle long text content on mobile', async ({ page }) => {
    // Mock long transcript
    await page.route('**/api/roi-workflow/*/status', async route => {
      const longTranscript = 'This is a very long transcript that should wrap properly on mobile devices and not cause horizontal scrolling issues. '.repeat(20);
      
      const response = {
        status: 'completed',
        transcript: longTranscript,
        results: [{
          contactName: 'John Doe with a Very Long Name That Should Wrap',
          role: 'Senior Vice President of Operations and Strategy',
          organization: 'ACME Corporation International Holdings LLC',
          priority: 'HIGH',
          nextSteps: 'Schedule a comprehensive follow-up meeting to discuss the strategic implementation of the proposed solutions',
          tags: ['strategic-planning', 'high-priority', 'follow-up-required']
        }]
      };
      await route.fulfill({ json: response });
    });
    
    const audioFile = path.join(__dirname, '../../../test_real.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    await page.getByRole('button', { name: /Process Audio/i }).tap();
    
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ timeout: 30000 });
    
    // Verify no horizontal scrolling
    const bodyScrollWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);
    expect(bodyScrollWidth).toBeLessThanOrEqual(viewportWidth + 1); // Allow 1px tolerance
    
    // Verify text wraps properly
    const transcriptElement = page.locator('[data-testid="transcript-text"]');
    const transcriptBox = await transcriptElement.boundingBox();
    expect(transcriptBox?.width).toBeLessThan(viewportWidth);
  });

  test('should provide touch-friendly export options', async ({ page }) => {
    // Complete workflow first
    const audioFile = path.join(__dirname, '../../../test_real_audio.mp3');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    await page.getByRole('button', { name: /Process Audio/i }).tap();
    
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ timeout: 30000 });
    
    // Tap export button
    await page.getByRole('button', { name: /Export/i }).tap();
    
    // Verify mobile export menu
    await expect(page.locator('[data-testid="mobile-export-menu"]')).toBeVisible();
    
    // Check touch target sizes
    const exportOptions = page.locator('[data-testid="export-option"]');
    const optionCount = await exportOptions.count();
    
    for (let i = 0; i < optionCount; i++) {
      const option = exportOptions.nth(i);
      const box = await option.boundingBox();
      expect(box?.height).toBeGreaterThan(44); // Minimum touch target
    }
  });

  test('should handle pinch-to-zoom on results', async ({ page }) => {
    // Complete workflow
    const audioFile = path.join(__dirname, '../../../test_meeting.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    await page.getByRole('button', { name: /Process Audio/i }).tap();
    
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ timeout: 30000 });
    
    // Simulate pinch-to-zoom on transcript
    const transcript = page.locator('[data-testid="transcript-text"]');
    
    // Get initial font size
    const initialFontSize = await transcript.evaluate(el => 
      window.getComputedStyle(el).fontSize
    );
    
    // Simulate zoom in
    await page.touchscreen.tap(200, 300);
    await page.keyboard.press('Meta+='); // Zoom in command
    
    // Font should scale appropriately
    const newFontSize = await transcript.evaluate(el => 
      window.getComputedStyle(el).fontSize
    );
    
    // Content should remain accessible at different zoom levels
    await expect(transcript).toBeVisible();
  });

  test('should handle mobile keyboard interactions', async ({ page, context }) => {
    await context.grantPermissions(['microphone']);
    
    // Complete workflow to get to results
    const audioFile = path.join(__dirname, '../../../test_real.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    await page.getByRole('button', { name: /Process Audio/i }).tap();
    
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ timeout: 30000 });
    
    // Tap edit button
    await page.locator('[data-testid="edit-button"]').first().tap();
    
    // Verify mobile keyboard optimization
    const nameInput = page.locator('input[name="contactName"]');
    await nameInput.tap();
    
    // Check input is properly focused and visible when keyboard appears
    await expect(nameInput).toBeFocused();
    
    // Type and verify text appears
    await nameInput.fill('Mobile Test Name');
    await expect(nameInput).toHaveValue('Mobile Test Name');
    
    // Verify save button is accessible above keyboard
    const saveButton = page.getByRole('button', { name: /Save/i });
    const saveBox = await saveButton.boundingBox();
    expect(saveBox?.y).toBeLessThan(400); // Should be in upper half of screen
  });
});

// Additional tests for tablet viewport
test.describe('ROI Workflow - Tablet Responsiveness', () => {
  test.use({ ...devices['iPad Pro'] });

  test('should use tablet-optimized layout', async ({ page }) => {
    await page.goto('/roi-workflow');
    await page.waitForLoadState('networkidle');
    
    // Verify tablet layout elements
    await expect(page.locator('[data-testid="tablet-layout"]')).toBeVisible();
    
    // Should show both upload and recording options side by side
    const uploadSection = page.locator('[data-testid="upload-section"]');
    const recordingSection = page.locator('[data-testid="recording-section"]');
    
    const uploadBox = await uploadSection.boundingBox();
    const recordingBox = await recordingSection.boundingBox();
    
    // Should be side by side (same y position)
    expect(Math.abs(uploadBox?.y - recordingBox?.y)).toBeLessThan(50);
  });

  test('should display table in hybrid view on tablet', async ({ page }) => {
    await page.goto('/roi-workflow');
    
    // Complete workflow
    const audioFile = path.join(__dirname, '../../../test_real_audio.mp3');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ timeout: 30000 });
    
    // Verify tablet table view (condensed table, not cards)
    await expect(page.locator('[data-testid="tablet-table-view"]')).toBeVisible();
    await expect(page.locator('table')).toBeVisible();
    
    // But with optimized column widths
    const table = page.locator('table');
    const tableWidth = await table.evaluate(el => el.offsetWidth);
    const viewportWidth = await page.viewportSize();
    
    expect(tableWidth).toBeLessThanOrEqual(viewportWidth?.width || 1024);
  });
});