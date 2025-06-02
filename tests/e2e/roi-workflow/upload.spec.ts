import { test, expect } from '@playwright/test';
import path from 'path';
import testData from '../fixtures/test-data.json';

test.describe('ROI Workflow - File Upload', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to ROI workflow page
    await page.goto('/roi-workflow');
    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');
  });

  test('should display upload interface on initial load', async ({ page }) => {
    // Check for upload container
    await expect(page.locator('[data-testid="audio-uploader"]')).toBeVisible();
    
    // Check for upload button and drag-drop area
    await expect(page.getByText(/Upload Audio File/i)).toBeVisible();
    await expect(page.getByText(/drag and drop your audio file here/i)).toBeVisible();
    
    // Check for recording button
    await expect(page.getByRole('button', { name: /Start Recording/i })).toBeVisible();
  });

  test('should process uploaded audio file successfully', async ({ page }) => {
    // Path to test audio file
    const audioFile = path.join(__dirname, '../../../test_real_audio.mp3');
    
    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    // Wait for file to be selected
    await expect(page.getByText(/test_real_audio.mp3/)).toBeVisible();
    
    // Click process button
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Verify progress indicators appear
    await expect(page.locator('[data-testid="workflow-progress"]')).toBeVisible();
    
    // Wait for transcription step
    await expect(page.getByText(/Transcribing audio/i)).toBeVisible({ timeout: 10000 });
    
    // Wait for processing to complete (with extended timeout for real processing)
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ 
      timeout: testData.timeouts.processing 
    });
    
    // Verify results table appears
    await expect(page.locator('[data-testid="results-table"]')).toBeVisible();
    
    // Verify transcript section
    await expect(page.getByText(/Transcript/i)).toBeVisible();
    await expect(page.locator('[data-testid="transcript-text"]')).toBeVisible();
    
    // Verify extracted data in table
    await expect(page.locator('table')).toBeVisible();
    await expect(page.locator('table tbody tr')).toHaveCount({ min: 1 });
  });

  test('should show file size and duration after selection', async ({ page }) => {
    const audioFile = path.join(__dirname, '../../../test_meeting.wav');
    
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    // Check file info is displayed
    await expect(page.getByText(/test_meeting.wav/)).toBeVisible();
    await expect(page.getByText(/Size:/)).toBeVisible();
    await expect(page.getByText(/Duration:/)).toBeVisible();
  });

  test('should handle multiple file uploads sequentially', async ({ page }) => {
    // First upload
    const audioFile1 = path.join(__dirname, '../../../test_real_audio.mp3');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile1);
    
    // Process first file
    await page.getByRole('button', { name: /Process Audio/i }).click();
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ 
      timeout: testData.timeouts.processing 
    });
    
    // Start new workflow
    await page.getByRole('button', { name: /New Recording/i }).click();
    
    // Second upload
    const audioFile2 = path.join(__dirname, '../../../test_meeting.wav');
    await fileInput.setInputFiles(audioFile2);
    
    // Verify new file is selected
    await expect(page.getByText(/test_meeting.wav/)).toBeVisible();
  });

  test('should clear file selection on cancel', async ({ page }) => {
    const audioFile = path.join(__dirname, '../../../test_real.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    // Verify file is selected
    await expect(page.getByText(/test_real.wav/)).toBeVisible();
    
    // Click cancel/clear button
    await page.getByRole('button', { name: /Clear|Cancel|Remove/i }).click();
    
    // Verify file is no longer selected
    await expect(page.getByText(/test_real.wav/)).not.toBeVisible();
    await expect(page.getByText(/drag and drop your audio file here/i)).toBeVisible();
  });

  test('should reject non-audio files gracefully', async ({ page }) => {
    // Create a temporary text file
    const textContent = 'This is not an audio file';
    const fileName = 'test-document.txt';
    
    // Attempt to upload non-audio file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: fileName,
      mimeType: 'text/plain',
      buffer: Buffer.from(textContent)
    });
    
    // Verify error message
    await expect(page.getByText(/Please upload a valid audio file/i)).toBeVisible();
    
    // Verify file is not accepted
    await expect(page.getByRole('button', { name: /Process Audio/i })).toBeDisabled();
  });

  test('should handle drag and drop upload', async ({ page }) => {
    const audioFile = path.join(__dirname, '../../../test_real_audio.mp3');
    
    // Create a data transfer for drag and drop
    const dataTransfer = await page.evaluateHandle(() => new DataTransfer());
    
    // Read file and add to data transfer
    const buffer = await page.evaluate(async (filePath) => {
      const response = await fetch(filePath);
      const arrayBuffer = await response.arrayBuffer();
      return Array.from(new Uint8Array(arrayBuffer));
    }, `file://${audioFile}`);
    
    await page.evaluate(({ dataTransfer, fileName, buffer }) => {
      const file = new File([new Uint8Array(buffer)], fileName, { type: 'audio/mp3' });
      dataTransfer.items.add(file);
    }, { dataTransfer, fileName: 'test_real_audio.mp3', buffer });
    
    // Perform drag and drop
    const dropZone = page.locator('[data-testid="drop-zone"]');
    await dropZone.dispatchEvent('drop', { dataTransfer });
    
    // Verify file is uploaded
    await expect(page.getByText(/test_real_audio.mp3/)).toBeVisible();
  });

  test('should display upload progress indicator', async ({ page }) => {
    const audioFile = path.join(__dirname, '../../../test_meeting.wav');
    
    // Mock slow upload to see progress
    await page.route('**/api/roi-workflow/upload', async route => {
      await page.waitForTimeout(2000); // Simulate slow upload
      await route.continue();
    });
    
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Check for upload progress indicator
    await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible();
    await expect(page.getByText(/Uploading/i)).toBeVisible();
  });
});