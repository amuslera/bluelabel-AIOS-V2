import { test, expect, Page } from '@playwright/test';
import testData from '../fixtures/test-data.json';

test.describe('ROI Workflow - Audio Recording', () => {
  // Helper to grant microphone permissions
  async function grantMicrophonePermission(page: Page) {
    await page.context().grantPermissions(['microphone']);
  }

  test.beforeEach(async ({ page }) => {
    await grantMicrophonePermission(page);
    await page.goto('/roi-workflow');
    await page.waitForLoadState('networkidle');
  });

  test('should display recording interface', async ({ page }) => {
    // Check recording button is visible
    await expect(page.getByRole('button', { name: /Start Recording/i })).toBeVisible();
    
    // Check for recording guide
    await expect(page.getByText(/Click the microphone button/i)).toBeVisible();
  });

  test('should start and stop recording with UI feedback', async ({ page }) => {
    // Click start recording
    await page.getByRole('button', { name: /Start Recording/i }).click();
    
    // Verify recording UI state
    await expect(page.getByRole('button', { name: /Stop Recording/i })).toBeVisible();
    await expect(page.locator('[data-testid="recording-indicator"]')).toBeVisible();
    await expect(page.getByText(/Recording.../i)).toBeVisible();
    
    // Check for timer
    await expect(page.locator('[data-testid="recording-timer"]')).toBeVisible();
    
    // Wait a bit to record
    await page.waitForTimeout(2000);
    
    // Stop recording
    await page.getByRole('button', { name: /Stop Recording/i }).click();
    
    // Verify recording stopped
    await expect(page.getByRole('button', { name: /Process Audio/i })).toBeVisible();
    await expect(page.getByText(/Recording saved/i)).toBeVisible();
  });

  test('should show recording duration while recording', async ({ page }) => {
    await page.getByRole('button', { name: /Start Recording/i }).click();
    
    // Check initial timer
    await expect(page.locator('[data-testid="recording-timer"]')).toContainText('0:00');
    
    // Wait and check timer updates
    await page.waitForTimeout(3000);
    await expect(page.locator('[data-testid="recording-timer"]')).toContainText(/0:0[2-3]/);
    
    await page.getByRole('button', { name: /Stop Recording/i }).click();
  });

  test('should handle recording cancellation', async ({ page }) => {
    // Start recording
    await page.getByRole('button', { name: /Start Recording/i }).click();
    await page.waitForTimeout(1000);
    
    // Cancel recording
    await page.getByRole('button', { name: /Cancel/i }).click();
    
    // Verify back to initial state
    await expect(page.getByRole('button', { name: /Start Recording/i })).toBeVisible();
    await expect(page.getByText(/Recording.../i)).not.toBeVisible();
  });

  test('should process recorded audio successfully', async ({ page }) => {
    // Start recording
    await page.getByRole('button', { name: /Start Recording/i }).click();
    
    // Record for 3 seconds
    await page.waitForTimeout(3000);
    
    // Stop recording
    await page.getByRole('button', { name: /Stop Recording/i }).click();
    
    // Process the recording
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Verify processing starts
    await expect(page.locator('[data-testid="workflow-progress"]')).toBeVisible();
    
    // Wait for completion (mocked in tests)
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ 
      timeout: testData.timeouts.processing 
    });
    
    // Verify results
    await expect(page.locator('[data-testid="results-table"]')).toBeVisible();
  });

  test('should handle microphone permission denial', async ({ page, context }) => {
    // Revoke microphone permission
    await context.clearPermissions();
    
    // Try to start recording
    await page.getByRole('button', { name: /Start Recording/i }).click();
    
    // Check for permission error message
    await expect(page.getByText(/Microphone access is required/i)).toBeVisible();
  });

  test('should prevent recording while processing', async ({ page }) => {
    // Start first recording
    await page.getByRole('button', { name: /Start Recording/i }).click();
    await page.waitForTimeout(2000);
    await page.getByRole('button', { name: /Stop Recording/i }).click();
    
    // Start processing
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Verify recording button is disabled during processing
    await expect(page.getByRole('button', { name: /Start Recording/i })).toBeDisabled();
  });

  test('should show visual feedback for audio levels', async ({ page }) => {
    // Start recording
    await page.getByRole('button', { name: /Start Recording/i }).click();
    
    // Check for audio level indicator
    await expect(page.locator('[data-testid="audio-level-indicator"]')).toBeVisible();
    
    // Verify it's animating (has changing values)
    const initialLevel = await page.locator('[data-testid="audio-level-indicator"]').getAttribute('data-level');
    await page.waitForTimeout(500);
    const updatedLevel = await page.locator('[data-testid="audio-level-indicator"]').getAttribute('data-level');
    
    expect(initialLevel).not.toBe(updatedLevel);
    
    await page.getByRole('button', { name: /Stop Recording/i }).click();
  });

  test('should handle maximum recording duration', async ({ page }) => {
    // Start recording
    await page.getByRole('button', { name: /Start Recording/i }).click();
    
    // Mock reaching max duration (e.g., 5 minutes)
    await page.evaluate(() => {
      // Trigger max duration event
      window.dispatchEvent(new CustomEvent('recording-max-duration'));
    });
    
    // Verify auto-stop
    await expect(page.getByRole('button', { name: /Process Audio/i })).toBeVisible();
    await expect(page.getByText(/Maximum recording duration reached/i)).toBeVisible();
  });

  test('should maintain recording state on accidental navigation', async ({ page }) => {
    // Start recording
    await page.getByRole('button', { name: /Start Recording/i }).click();
    await page.waitForTimeout(1000);
    
    // Try to navigate away
    page.on('dialog', dialog => {
      expect(dialog.message()).toContain('recording in progress');
      dialog.dismiss(); // Cancel navigation
    });
    
    // Attempt navigation
    await page.getByRole('link', { name: /Dashboard/i }).click();
    
    // Verify still on same page and recording
    await expect(page.locator('[data-testid="recording-indicator"]')).toBeVisible();
  });
});