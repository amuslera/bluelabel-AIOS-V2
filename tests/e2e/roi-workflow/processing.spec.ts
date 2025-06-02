import { test, expect } from '@playwright/test';
import path from 'path';
import testData from '../fixtures/test-data.json';

test.describe('ROI Workflow - Processing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/roi-workflow');
    await page.waitForLoadState('networkidle');
  });

  test('should show all processing stages with progress', async ({ page }) => {
    // Upload file
    const audioFile = path.join(__dirname, '../../../test_real_audio.mp3');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    // Start processing
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Verify each processing stage appears in order
    const stages = [
      'Uploading audio file',
      'Transcribing audio',
      'Detecting language',
      'Translating to English',
      'Extracting key information',
      'Generating ROI report'
    ];
    
    for (const stage of stages) {
      await expect(page.getByText(stage)).toBeVisible({ timeout: 30000 });
    }
    
    // Verify completion
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ 
      timeout: testData.timeouts.processing 
    });
  });

  test('should show real-time progress updates', async ({ page }) => {
    const audioFile = path.join(__dirname, '../../../test_meeting.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Check for progress bar
    const progressBar = page.locator('[data-testid="progress-bar"]');
    await expect(progressBar).toBeVisible();
    
    // Verify progress increases
    const initialProgress = await progressBar.getAttribute('aria-valuenow');
    await page.waitForTimeout(2000);
    const updatedProgress = await progressBar.getAttribute('aria-valuenow');
    
    expect(Number(updatedProgress)).toBeGreaterThan(Number(initialProgress));
  });

  test('should handle Spanish audio with translation', async ({ page }) => {
    const audioFile = path.join(__dirname, '../../../test_real_audio.mp3');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Wait for language detection
    await expect(page.getByText(/Spanish detected/i)).toBeVisible({ timeout: 20000 });
    
    // Verify translation step
    await expect(page.getByText(/Translating to English/i)).toBeVisible();
    
    // Wait for completion
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ 
      timeout: testData.timeouts.processing 
    });
    
    // Verify both transcripts are shown
    await expect(page.getByText(/Original Transcript \(Spanish\)/i)).toBeVisible();
    await expect(page.getByText(/English Translation/i)).toBeVisible();
  });

  test('should handle English audio without translation', async ({ page }) => {
    // Mock English audio response
    await page.route('**/api/roi-workflow/*/status', async route => {
      const response = {
        workflow_id: 'test-123',
        status: 'completed',
        current_stage: 'completed',
        language: 'en',
        transcript: 'This is English audio content',
        transcript_english: null,
        results: [{
          contactName: 'Test Person',
          role: 'Manager',
          organization: 'Test Corp',
          priority: 'HIGH',
          nextSteps: 'Follow up next week',
          tags: ['meeting', 'important']
        }]
      };
      await route.fulfill({ json: response });
    });
    
    const audioFile = path.join(__dirname, '../../../test_meeting.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Wait for completion
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ 
      timeout: testData.timeouts.processing 
    });
    
    // Verify no translation section
    await expect(page.getByText(/English Translation/i)).not.toBeVisible();
    await expect(page.getByText(/Transcript/i)).toBeVisible();
  });

  test('should handle network interruption during processing', async ({ page }) => {
    const audioFile = path.join(__dirname, '../../../test_real.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    // Intercept status polling and fail after 2 successful calls
    let callCount = 0;
    await page.route('**/api/roi-workflow/*/status', async route => {
      callCount++;
      if (callCount > 2 && callCount < 5) {
        await route.abort('failed');
      } else {
        await route.continue();
      }
    });
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Should show retry message
    await expect(page.getByText(/Retrying connection/i)).toBeVisible({ timeout: 15000 });
    
    // Should eventually complete
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ 
      timeout: testData.timeouts.processing 
    });
  });

  test('should allow cancellation during processing', async ({ page }) => {
    const audioFile = path.join(__dirname, '../../../test_real_audio.mp3');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    // Mock slow processing
    await page.route('**/api/roi-workflow/*/status', async route => {
      await page.waitForTimeout(5000);
      await route.continue();
    });
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Wait for processing to start
    await expect(page.locator('[data-testid="workflow-progress"]')).toBeVisible();
    
    // Cancel processing
    await page.getByRole('button', { name: /Cancel/i }).click();
    
    // Confirm cancellation
    await page.getByRole('button', { name: /Yes, cancel/i }).click();
    
    // Should return to upload state
    await expect(page.getByRole('button', { name: /Start Recording/i })).toBeVisible();
  });

  test('should display estimated time remaining', async ({ page }) => {
    const audioFile = path.join(__dirname, '../../../test_meeting.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Check for time estimate
    await expect(page.getByText(/Estimated time remaining/i)).toBeVisible();
    await expect(page.locator('[data-testid="time-remaining"]')).toBeVisible();
  });

  test('should handle very long audio files with appropriate messaging', async ({ page }) => {
    // Mock file info for large file
    await page.evaluate(() => {
      // Override file size check
      window.MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB
    });
    
    const audioFile = path.join(__dirname, '../../../test_real_audio.mp3');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    // Mock duration display
    await page.evaluate(() => {
      const durationElement = document.querySelector('[data-testid="file-duration"]');
      if (durationElement) {
        durationElement.textContent = 'Duration: 45:30';
      }
    });
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Should show warning about long processing time
    await expect(page.getByText(/This may take several minutes/i)).toBeVisible();
  });

  test('should maintain state on page refresh during processing', async ({ page }) => {
    const audioFile = path.join(__dirname, '../../../test_real.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Wait for processing to start
    await expect(page.locator('[data-testid="workflow-progress"]')).toBeVisible();
    
    // Get workflow ID from page
    const workflowId = await page.evaluate(() => {
      return window.localStorage.getItem('current-workflow-id');
    });
    
    // Refresh page
    await page.reload();
    
    // Should restore processing state
    await expect(page.locator('[data-testid="workflow-progress"]')).toBeVisible();
    
    // Verify same workflow ID
    const restoredWorkflowId = await page.evaluate(() => {
      return window.localStorage.getItem('current-workflow-id');
    });
    
    expect(restoredWorkflowId).toBe(workflowId);
  });
});