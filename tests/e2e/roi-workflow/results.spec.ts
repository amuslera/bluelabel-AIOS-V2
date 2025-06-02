import { test, expect } from '@playwright/test';
import path from 'path';
import testData from '../fixtures/test-data.json';

test.describe('ROI Workflow - Results Table', () => {
  // Helper to get to results state
  async function uploadAndProcess(page: any) {
    const audioFile = path.join(__dirname, '../../../test_real_audio.mp3');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    await page.getByRole('button', { name: /Process Audio/i }).click();
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ 
      timeout: testData.timeouts.processing 
    });
  }

  test.beforeEach(async ({ page }) => {
    await page.goto('/roi-workflow');
    await page.waitForLoadState('networkidle');
  });

  test('should display results table with all columns', async ({ page }) => {
    await uploadAndProcess(page);
    
    // Check table is visible
    const table = page.locator('[data-testid="results-table"] table');
    await expect(table).toBeVisible();
    
    // Verify all column headers
    const expectedColumns = [
      'Contact Name',
      'Role',
      'Organization', 
      'Priority',
      'Next Steps',
      'Tags',
      'Actions'
    ];
    
    for (const column of expectedColumns) {
      await expect(table.locator('th', { hasText: column })).toBeVisible();
    }
  });

  test('should allow inline editing of contact information', async ({ page }) => {
    await uploadAndProcess(page);
    
    // Click edit button for first row
    await page.locator('[data-testid="edit-button"]').first().click();
    
    // Edit contact name
    const contactNameInput = page.locator('input[name="contactName"]');
    await contactNameInput.clear();
    await contactNameInput.fill('Updated Contact Name');
    
    // Edit role
    const roleInput = page.locator('input[name="role"]');
    await roleInput.clear();
    await roleInput.fill('Updated Role');
    
    // Save changes
    await page.getByRole('button', { name: /Save/i }).click();
    
    // Verify changes persisted
    await expect(page.getByText('Updated Contact Name')).toBeVisible();
    await expect(page.getByText('Updated Role')).toBeVisible();
  });

  test('should allow changing priority with dropdown', async ({ page }) => {
    await uploadAndProcess(page);
    
    // Click priority dropdown
    const priorityCell = page.locator('td[data-field="priority"]').first();
    await priorityCell.click();
    
    // Select new priority
    await page.getByRole('option', { name: 'LOW' }).click();
    
    // Verify change
    await expect(priorityCell).toContainText('LOW');
    
    // Verify visual indicator updated
    await expect(priorityCell.locator('.priority-indicator')).toHaveClass(/priority-low/);
  });

  test('should allow adding and removing tags', async ({ page }) => {
    await uploadAndProcess(page);
    
    // Click edit for tags
    await page.locator('[data-testid="edit-tags-button"]').first().click();
    
    // Add new tag
    const tagInput = page.locator('input[placeholder="Add tag"]');
    await tagInput.fill('new-tag');
    await tagInput.press('Enter');
    
    // Verify tag added
    await expect(page.locator('.tag-chip', { hasText: 'new-tag' })).toBeVisible();
    
    // Remove a tag
    await page.locator('.tag-chip', { hasText: 'new-tag' }).locator('.remove-tag').click();
    
    // Verify tag removed
    await expect(page.locator('.tag-chip', { hasText: 'new-tag' })).not.toBeVisible();
  });

  test('should display transcript sections correctly', async ({ page }) => {
    await uploadAndProcess(page);
    
    // Check transcript section
    await expect(page.getByText(/Transcript/i)).toBeVisible();
    const transcriptSection = page.locator('[data-testid="transcript-section"]');
    await expect(transcriptSection).toBeVisible();
    
    // For Spanish audio, check both transcripts
    await expect(page.getByText(/Original Transcript/i)).toBeVisible();
    await expect(page.getByText(/English Translation/i)).toBeVisible();
    
    // Verify transcript content is displayed
    await expect(transcriptSection.locator('[data-testid="transcript-text"]')).not.toBeEmpty();
  });

  test('should allow copying transcript to clipboard', async ({ page, context }) => {
    // Grant clipboard permissions
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    
    await uploadAndProcess(page);
    
    // Click copy button
    await page.getByRole('button', { name: /Copy transcript/i }).click();
    
    // Verify success message
    await expect(page.getByText(/Copied to clipboard/i)).toBeVisible();
    
    // Verify clipboard content
    const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
    expect(clipboardText).toBeTruthy();
  });

  test('should export results to CSV', async ({ page }) => {
    await uploadAndProcess(page);
    
    // Set up download promise before clicking
    const downloadPromise = page.waitForEvent('download');
    
    // Click export button
    await page.getByRole('button', { name: /Export/i }).click();
    await page.getByRole('menuitem', { name: /CSV/i }).click();
    
    // Wait for download
    const download = await downloadPromise;
    
    // Verify download
    expect(download.suggestedFilename()).toMatch(/roi-report.*\.csv/);
  });

  test('should export results to JSON', async ({ page }) => {
    await uploadAndProcess(page);
    
    const downloadPromise = page.waitForEvent('download');
    
    await page.getByRole('button', { name: /Export/i }).click();
    await page.getByRole('menuitem', { name: /JSON/i }).click();
    
    const download = await downloadPromise;
    
    expect(download.suggestedFilename()).toMatch(/roi-report.*\.json/);
  });

  test('should filter results by priority', async ({ page }) => {
    // Mock multiple results
    await page.route('**/api/roi-workflow/*/status', async route => {
      const response = {
        status: 'completed',
        results: [
          { contactName: 'High Priority', priority: 'HIGH', role: 'CEO' },
          { contactName: 'Medium Priority', priority: 'MEDIUM', role: 'Manager' },
          { contactName: 'Low Priority', priority: 'LOW', role: 'Assistant' }
        ]
      };
      await route.fulfill({ json: response });
    });
    
    await uploadAndProcess(page);
    
    // Apply HIGH priority filter
    await page.getByRole('button', { name: /Filter/i }).click();
    await page.getByRole('checkbox', { name: /HIGH/i }).check();
    await page.getByRole('button', { name: /Apply/i }).click();
    
    // Verify only HIGH priority items shown
    await expect(page.getByText('High Priority')).toBeVisible();
    await expect(page.getByText('Medium Priority')).not.toBeVisible();
    await expect(page.getByText('Low Priority')).not.toBeVisible();
  });

  test('should sort results by column', async ({ page }) => {
    await uploadAndProcess(page);
    
    // Click on Contact Name header to sort
    await page.locator('th', { hasText: 'Contact Name' }).click();
    
    // Verify sort indicator appears
    await expect(page.locator('th', { hasText: 'Contact Name' }).locator('.sort-indicator')).toBeVisible();
    
    // Click again to reverse sort
    await page.locator('th', { hasText: 'Contact Name' }).click();
    
    // Verify sort direction changed
    await expect(page.locator('th', { hasText: 'Contact Name' }).locator('.sort-indicator.desc')).toBeVisible();
  });

  test('should handle empty results gracefully', async ({ page }) => {
    // Mock empty results
    await page.route('**/api/roi-workflow/*/status', async route => {
      const response = {
        status: 'completed',
        transcript: 'Audio processed but no contacts found',
        results: []
      };
      await route.fulfill({ json: response });
    });
    
    await uploadAndProcess(page);
    
    // Should show empty state message
    await expect(page.getByText(/No contacts were extracted/i)).toBeVisible();
    
    // Should still show transcript
    await expect(page.locator('[data-testid="transcript-section"]')).toBeVisible();
  });

  test('should start new workflow from results', async ({ page }) => {
    await uploadAndProcess(page);
    
    // Click new recording button
    await page.getByRole('button', { name: /New Recording/i }).click();
    
    // Should return to upload state
    await expect(page.getByRole('button', { name: /Start Recording/i })).toBeVisible();
    await expect(page.locator('[data-testid="results-table"]')).not.toBeVisible();
  });
});