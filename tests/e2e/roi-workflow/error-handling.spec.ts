import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('ROI Workflow - Error Handling & Edge Cases', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/roi-workflow');
    await page.waitForLoadState('networkidle');
  });

  test('should handle file upload errors gracefully', async ({ page }) => {
    // Mock upload failure
    await page.route('**/api/roi-workflow/upload', async route => {
      await route.fulfill({
        status: 500,
        json: { error: 'Upload failed due to server error' }
      });
    });

    const audioFile = path.join(__dirname, '../../../test_real_audio.mp3');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Verify error message displayed
    await expect(page.getByText(/Upload failed due to server error/i)).toBeVisible();
    
    // Verify retry option
    await expect(page.getByRole('button', { name: /Retry/i })).toBeVisible();
    
    // Verify user can return to upload state
    await expect(page.getByRole('button', { name: /Start Recording/i })).toBeVisible();
  });

  test('should handle transcription service failures', async ({ page }) => {
    // Mock transcription failure
    await page.route('**/api/roi-workflow/*/status', async route => {
      const response = {
        workflow_id: 'test-123',
        status: 'error',
        current_stage: 'transcription',
        error: 'Transcription service temporarily unavailable'
      };
      await route.fulfill({ json: response });
    });

    const audioFile = path.join(__dirname, '../../../test_meeting.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Wait for error state
    await expect(page.getByText(/Transcription service temporarily unavailable/i)).toBeVisible({ timeout: 20000 });
    
    // Verify error actions
    await expect(page.getByRole('button', { name: /Try Again/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Start Over/i })).toBeVisible();
  });

  test('should handle translation service failures', async ({ page }) => {
    // Mock partial success (transcription works, translation fails)
    let callCount = 0;
    await page.route('**/api/roi-workflow/*/status', async route => {
      callCount++;
      if (callCount <= 2) {
        await route.fulfill({
          json: {
            status: 'processing',
            current_stage: 'transcription',
            transcript: 'Hola, esta es una prueba'
          }
        });
      } else {
        await route.fulfill({
          json: {
            status: 'error',
            current_stage: 'translation',
            transcript: 'Hola, esta es una prueba',
            error: 'Translation service error'
          }
        });
      }
    });

    const audioFile = path.join(__dirname, '../../../test_real.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Should show partial results with error
    await expect(page.getByText(/Translation service error/i)).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(/Hola, esta es una prueba/i)).toBeVisible();
    
    // Should offer option to continue without translation
    await expect(page.getByRole('button', { name: /Continue without translation/i })).toBeVisible();
  });

  test('should handle extremely large files', async ({ page }) => {
    // Mock file size validation
    await page.evaluate(() => {
      // Override file validation
      const originalValidation = window.FileReader;
      window.FileReader = class extends originalValidation {
        readAsArrayBuffer(file: any) {
          if (file.size > 100 * 1024 * 1024) { // 100MB limit
            const error = new Error('File too large');
            setTimeout(() => this.onerror(error), 100);
            return;
          }
          super.readAsArrayBuffer(file);
        }
      };
    });

    // Try to upload oversized file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'huge_file.mp3',
      mimeType: 'audio/mp3',
      buffer: Buffer.alloc(150 * 1024 * 1024) // 150MB
    });

    // Should show size error
    await expect(page.getByText(/File size exceeds maximum limit/i)).toBeVisible();
    await expect(page.getByText(/Please choose a smaller file/i)).toBeVisible();
  });

  test('should handle corrupted audio files', async ({ page }) => {
    // Mock corrupted file response
    await page.route('**/api/roi-workflow/upload', async route => {
      await route.fulfill({
        status: 400,
        json: { error: 'Invalid audio format or corrupted file' }
      });
    });

    // Create a fake corrupted file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'corrupted.mp3',
      mimeType: 'audio/mp3',
      buffer: Buffer.from('not-actually-audio-data')
    });

    await page.getByRole('button', { name: /Process Audio/i }).click();

    // Should show appropriate error
    await expect(page.getByText(/Invalid audio format or corrupted file/i)).toBeVisible();
    await expect(page.getByText(/Please try a different audio file/i)).toBeVisible();
  });

  test('should handle empty or silent audio files', async ({ page }) => {
    // Mock silent audio processing
    await page.route('**/api/roi-workflow/*/status', async route => {
      const response = {
        status: 'completed',
        transcript: '',
        transcript_english: null,
        results: [],
        warning: 'No speech detected in audio file'
      };
      await route.fulfill({ json: response });
    });

    const audioFile = path.join(__dirname, '../../../test_meeting.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Should show warning about silent audio
    await expect(page.getByText(/No speech detected in audio file/i)).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(/No contacts were extracted/i)).toBeVisible();
    
    // Should offer to try again
    await expect(page.getByRole('button', { name: /Try with different audio/i })).toBeVisible();
  });

  test('should handle session timeout during processing', async ({ page }) => {
    // Mock session timeout
    let requestCount = 0;
    await page.route('**/api/roi-workflow/*/status', async route => {
      requestCount++;
      if (requestCount > 3) {
        await route.fulfill({
          status: 401,
          json: { error: 'Session expired' }
        });
      } else {
        await route.fulfill({
          json: {
            status: 'processing',
            current_stage: 'transcription'
          }
        });
      }
    });

    const audioFile = path.join(__dirname, '../../../test_real_audio.mp3');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Should detect session timeout and redirect to login
    await expect(page.getByText(/Session expired/i)).toBeVisible({ timeout: 30000 });
    await expect(page.getByRole('button', { name: /Sign In Again/i })).toBeVisible();
  });

  test('should handle rate limiting gracefully', async ({ page }) => {
    // Mock rate limiting response
    await page.route('**/api/roi-workflow/upload', async route => {
      await route.fulfill({
        status: 429,
        headers: { 'Retry-After': '60' },
        json: { error: 'Rate limit exceeded. Please try again in 1 minute.' }
      });
    });

    const audioFile = path.join(__dirname, '../../../test_real.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Should show rate limit message with countdown
    await expect(page.getByText(/Rate limit exceeded/i)).toBeVisible();
    await expect(page.getByText(/Please try again in 1 minute/i)).toBeVisible();
    
    // Should show countdown timer
    await expect(page.locator('[data-testid="retry-countdown"]')).toBeVisible();
  });

  test('should handle browser compatibility issues', async ({ page }) => {
    // Mock missing Web Audio API
    await page.evaluate(() => {
      // @ts-ignore
      delete window.AudioContext;
      // @ts-ignore
      delete window.webkitAudioContext;
    });

    // Try to start recording
    await page.getByRole('button', { name: /Start Recording/i }).click();
    
    // Should show compatibility error
    await expect(page.getByText(/Your browser doesn't support audio recording/i)).toBeVisible();
    await expect(page.getByText(/Please try using Chrome, Firefox, or Safari/i)).toBeVisible();
  });

  test('should handle network connectivity issues', async ({ page }) => {
    const audioFile = path.join(__dirname, '../../../test_meeting.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    // Mock network failure after starting processing
    let callCount = 0;
    await page.route('**/api/roi-workflow/**', async route => {
      callCount++;
      if (callCount === 1) {
        // First call succeeds (upload)
        await route.continue();
      } else {
        // Subsequent calls fail (network issue)
        await route.abort('failed');
      }
    });

    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Should detect network issue
    await expect(page.getByText(/Connection lost/i)).toBeVisible({ timeout: 20000 });
    await expect(page.getByText(/Trying to reconnect/i)).toBeVisible();
    
    // Should show retry button
    await expect(page.getByRole('button', { name: /Retry Connection/i })).toBeVisible();
  });

  test('should handle unsupported audio formats', async ({ page }) => {
    // Try to upload unsupported format
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'audio.flac',
      mimeType: 'audio/flac',
      buffer: Buffer.from('flac-data')
    });

    // Should show format error immediately
    await expect(page.getByText(/Unsupported audio format/i)).toBeVisible();
    await expect(page.getByText(/Please use MP3, WAV, or WEBM/i)).toBeVisible();
    
    // Process button should remain disabled
    await expect(page.getByRole('button', { name: /Process Audio/i })).toBeDisabled();
  });

  test('should handle concurrent workflow attempts', async ({ page }) => {
    // Mock conflict response
    await page.route('**/api/roi-workflow/upload', async route => {
      await route.fulfill({
        status: 409,
        json: { error: 'Another workflow is already in progress' }
      });
    });

    const audioFile = path.join(__dirname, '../../../test_real_audio.mp3');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Should show conflict message
    await expect(page.getByText(/Another workflow is already in progress/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /Cancel Previous Workflow/i })).toBeVisible();
  });

  test('should handle malformed API responses', async ({ page }) => {
    // Mock malformed JSON response
    await page.route('**/api/roi-workflow/*/status', async route => {
      await route.fulfill({
        status: 200,
        body: 'invalid-json-response'
      });
    });

    const audioFile = path.join(__dirname, '../../../test_meeting.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Should handle parsing error gracefully
    await expect(page.getByText(/Unable to process server response/i)).toBeVisible({ timeout: 20000 });
    await expect(page.getByRole('button', { name: /Report Issue/i })).toBeVisible();
  });

  test('should preserve data during page refresh in error state', async ({ page }) => {
    // Start processing
    const audioFile = path.join(__dirname, '../../../test_real.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Mock error during processing
    await page.route('**/api/roi-workflow/*/status', async route => {
      await route.fulfill({
        json: {
          status: 'error',
          error: 'Processing interrupted'
        }
      });
    });

    // Wait for error state
    await expect(page.getByText(/Processing interrupted/i)).toBeVisible({ timeout: 20000 });
    
    // Refresh page
    await page.reload();
    
    // Should restore error state with recovery options
    await expect(page.getByText(/Previous workflow encountered an error/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /Resume/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Start New/i })).toBeVisible();
  });
});