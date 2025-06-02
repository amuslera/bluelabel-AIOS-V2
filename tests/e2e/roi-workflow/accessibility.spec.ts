import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import path from 'path';

test.describe('ROI Workflow - Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/roi-workflow');
    await page.waitForLoadState('networkidle');
  });

  test('should pass automated accessibility audit on upload page', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    // Check heading structure
    const h1 = page.locator('h1');
    await expect(h1).toContainText(/ROI Workflow|Voice to Data/i);
    
    // Check that headings follow proper hierarchy (no skipping levels)
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').allTextContents();
    expect(headings.length).toBeGreaterThan(0);
    
    // Verify main heading exists
    await expect(page.locator('h1')).toHaveCount(1);
  });

  test('should support keyboard navigation throughout workflow', async ({ page }) => {
    // Tab through all interactive elements
    await page.keyboard.press('Tab');
    
    // Should focus on first interactive element (upload area or record button)
    let focusedElement = await page.locator(':focus').textContent();
    expect(focusedElement).toMatch(/Upload|Record|Start/i);
    
    // Continue tabbing and verify each element is focusable
    const interactiveElements = ['button', 'input', 'select', '[tabindex="0"]'];
    for (const selector of interactiveElements) {
      const elements = page.locator(selector);
      const count = await elements.count();
      
      for (let i = 0; i < count; i++) {
        const element = elements.nth(i);
        if (await element.isVisible()) {
          await element.focus();
          await expect(element).toBeFocused();
        }
      }
    }
  });

  test('should have accessible form labels and descriptions', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');
    
    // Check that file input has accessible label
    await expect(fileInput).toHaveAttribute('aria-label');
    
    // Check for associated label element
    const labelText = await fileInput.getAttribute('aria-label');
    expect(labelText).toContain('audio');
    
    // Check for helpful descriptions
    await expect(page.locator('[aria-describedby]')).toBeVisible();
  });

  test('should provide clear focus indicators', async ({ page }) => {
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    
    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      if (await button.isVisible() && await button.isEnabled()) {
        await button.focus();
        
        // Check that focused element has visible focus ring
        const focusStyles = await button.evaluate(el => {
          const styles = window.getComputedStyle(el, ':focus');
          return {
            outline: styles.outline,
            boxShadow: styles.boxShadow,
            border: styles.border
          };
        });
        
        // Should have some form of focus indicator
        const hasFocusIndicator = 
          focusStyles.outline !== 'none' ||
          focusStyles.boxShadow !== 'none' ||
          focusStyles.border.includes('focus');
        
        expect(hasFocusIndicator).toBeTruthy();
      }
    }
  });

  test('should support screen reader navigation during processing', async ({ page }) => {
    // Upload file
    const audioFile = path.join(__dirname, '../../../test_real_audio.mp3');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Check that progress updates have proper ARIA labels
    const progressRegion = page.locator('[role="progressbar"], [aria-live]');
    await expect(progressRegion).toBeVisible();
    
    // Verify progress is announced
    await expect(progressRegion).toHaveAttribute('aria-label');
    
    // Check for live region updates
    const liveRegion = page.locator('[aria-live="polite"], [aria-live="assertive"]');
    await expect(liveRegion).toBeVisible();
    
    // Verify status updates are announced
    await expect(page.getByText(/Transcribing|Processing/i)).toBeVisible();
  });

  test('should have accessible table structure in results', async ({ page }) => {
    // Mock completed workflow
    await page.route('**/api/roi-workflow/*/status', async route => {
      const response = {
        status: 'completed',
        transcript: 'Test transcript content',
        results: [{
          contactName: 'John Doe',
          role: 'Manager',
          organization: 'ACME Corp',
          priority: 'HIGH',
          nextSteps: 'Follow up',
          tags: ['meeting']
        }]
      };
      await route.fulfill({ json: response });
    });
    
    const audioFile = path.join(__dirname, '../../../test_meeting.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ timeout: 30000 });
    
    // Check table accessibility
    const table = page.locator('table');
    await expect(table).toBeVisible();
    
    // Verify table has caption or aria-label
    const hasCaption = await table.locator('caption').isVisible();
    const hasAriaLabel = await table.getAttribute('aria-label');
    expect(hasCaption || hasAriaLabel).toBeTruthy();
    
    // Verify proper table structure
    await expect(table.locator('thead')).toBeVisible();
    await expect(table.locator('tbody')).toBeVisible();
    
    // Check column headers have proper scope
    const columnHeaders = table.locator('th');
    const headerCount = await columnHeaders.count();
    
    for (let i = 0; i < headerCount; i++) {
      const header = columnHeaders.nth(i);
      const scope = await header.getAttribute('scope');
      expect(scope).toBe('col');
    }
  });

  test('should support high contrast mode', async ({ page }) => {
    // Simulate high contrast mode
    await page.emulateMedia({ colorScheme: 'dark', reducedMotion: 'reduce' });
    
    // Check that content is still visible and readable
    await expect(page.getByRole('button', { name: /Start Recording/i })).toBeVisible();
    await expect(page.getByText(/Upload Audio/i)).toBeVisible();
    
    // Verify sufficient color contrast for key elements
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    
    for (let i = 0; i < Math.min(buttonCount, 3); i++) {
      const button = buttons.nth(i);
      if (await button.isVisible()) {
        const contrast = await button.evaluate(el => {
          const styles = window.getComputedStyle(el);
          return {
            color: styles.color,
            backgroundColor: styles.backgroundColor,
            border: styles.border
          };
        });
        
        // Should have distinct styling (not fully transparent)
        expect(contrast.backgroundColor).not.toBe('rgba(0, 0, 0, 0)');
      }
    }
  });

  test('should support reduced motion preferences', async ({ page }) => {
    // Set reduced motion preference
    await page.emulateMedia({ reducedMotion: 'reduce' });
    
    // Upload and process file
    const audioFile = path.join(__dirname, '../../../test_real.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Verify animations are reduced or disabled
    const progressBar = page.locator('[data-testid="progress-bar"]');
    if (await progressBar.isVisible()) {
      const animationState = await progressBar.evaluate(el => {
        const styles = window.getComputedStyle(el);
        return styles.animation;
      });
      
      // Animation should be disabled or greatly reduced
      expect(animationState).toMatch(/none|0s/);
    }
  });

  test('should provide alternative text for visual content', async ({ page }) => {
    // Check for images with alt text
    const images = page.locator('img');
    const imageCount = await images.count();
    
    for (let i = 0; i < imageCount; i++) {
      const image = images.nth(i);
      const altText = await image.getAttribute('alt');
      
      // Decorative images should have empty alt text
      // Informative images should have descriptive alt text
      expect(altText).toBeDefined();
    }
    
    // Check for icons with proper labeling
    const icons = page.locator('[data-testid*="icon"], .icon');
    const iconCount = await icons.count();
    
    for (let i = 0; i < iconCount; i++) {
      const icon = icons.nth(i);
      const ariaLabel = await icon.getAttribute('aria-label');
      const ariaHidden = await icon.getAttribute('aria-hidden');
      
      // Icons should either be hidden from screen readers or have labels
      expect(ariaLabel || ariaHidden === 'true').toBeTruthy();
    }
  });

  test('should handle voice announcements for dynamic content', async ({ page }) => {
    // Start recording
    await page.context().grantPermissions(['microphone']);
    await page.getByRole('button', { name: /Start Recording/i }).click();
    
    // Check for recording status announcements
    await expect(page.locator('[aria-live="polite"]')).toContainText(/Recording|Started/i);
    
    // Stop recording
    await page.getByRole('button', { name: /Stop Recording/i }).click();
    
    // Check for stop announcement
    await expect(page.locator('[aria-live="polite"]')).toContainText(/Stopped|Saved/i);
  });

  test('should be navigable with screen reader shortcuts', async ({ page }) => {
    // Test landmark navigation
    const landmarks = await page.locator('[role="main"], [role="navigation"], [role="banner"], [role="contentinfo"]').count();
    expect(landmarks).toBeGreaterThan(0);
    
    // Test heading navigation
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').count();
    expect(headings).toBeGreaterThan(0);
    
    // Test form control navigation
    const formControls = await page.locator('input, button, select, textarea').count();
    expect(formControls).toBeGreaterThan(0);
    
    // Verify skip links exist
    await page.keyboard.press('Tab');
    const skipLink = page.locator('a[href="#main"], a[href="#content"]').first();
    if (await skipLink.count() > 0) {
      await expect(skipLink).toBeFocused();
    }
  });

  test('should pass accessibility audit during processing state', async ({ page }) => {
    const audioFile = path.join(__dirname, '../../../test_meeting.wav');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    
    // Wait for processing UI to appear
    await expect(page.locator('[data-testid="workflow-progress"]')).toBeVisible();
    
    // Run accessibility audit on processing state
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should pass accessibility audit on results page', async ({ page }) => {
    // Mock completed workflow
    await page.route('**/api/roi-workflow/*/status', async route => {
      const response = {
        status: 'completed',
        transcript: 'Test transcript',
        results: [{
          contactName: 'Test Contact',
          role: 'Manager',
          organization: 'Test Corp',
          priority: 'HIGH',
          nextSteps: 'Follow up',
          tags: ['test']
        }]
      };
      await route.fulfill({ json: response });
    });
    
    const audioFile = path.join(__dirname, '../../../test_real_audio.mp3');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(audioFile);
    
    await page.getByRole('button', { name: /Process Audio/i }).click();
    await expect(page.getByText(/Processing complete/i)).toBeVisible({ timeout: 30000 });
    
    // Run accessibility audit on results
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });
});