import { test, expect, Page } from '@playwright/test';
import navigationData from '../fixtures/navigation-test-data.json';

test.describe('Breadcrumbs Navigation', () => {
  let page: Page;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display correct breadcrumbs for each route', async () => {
    // Test each breadcrumb scenario
    for (const breadcrumbTest of navigationData.breadcrumbTests) {
      await page.goto(breadcrumbTest.path);
      await page.waitForLoadState('networkidle');

      const breadcrumbsContainer = page.locator('[data-testid="breadcrumbs"]');
      await expect(breadcrumbsContainer).toBeVisible();

      // Verify each breadcrumb item
      for (let i = 0; i < breadcrumbTest.expected.length; i++) {
        const expectedCrumb = breadcrumbTest.expected[i];
        const breadcrumbItem = page.locator(`[data-testid="breadcrumb-${i}"]`);
        
        await expect(breadcrumbItem).toBeVisible();
        await expect(breadcrumbItem).toContainText(expectedCrumb.label);
        
        // Last item should not be clickable (current page)
        if (i === breadcrumbTest.expected.length - 1) {
          await expect(breadcrumbItem).toHaveAttribute('data-current', 'true');
        } else {
          await expect(breadcrumbItem).not.toHaveAttribute('data-current', 'true');
        }
      }

      // Verify correct number of breadcrumbs
      const breadcrumbItems = page.locator('[data-testid^="breadcrumb-"]');
      await expect(breadcrumbItems).toHaveCount(breadcrumbTest.expected.length);
    }
  });

  test('should navigate when clicking breadcrumb items', async () => {
    // Navigate to a deep route
    await page.goto('/agents/contentmind');
    await page.waitForLoadState('networkidle');

    // Click on "Agents" breadcrumb
    const agentsBreadcrumb = page.locator('[data-testid="breadcrumb-1"]');
    await agentsBreadcrumb.click();

    // Verify navigation to agents page
    await page.waitForURL('**/agents');
    expect(page.url()).toContain('/agents');

    // Verify breadcrumbs updated
    const breadcrumbItems = page.locator('[data-testid^="breadcrumb-"]');
    await expect(breadcrumbItems).toHaveCount(2); // Dashboard + Agents
  });

  test('should show separators between breadcrumb items', async () => {
    await page.goto('/agents/contentmind');
    await page.waitForLoadState('networkidle');

    // Verify separators are present
    const separators = page.locator('[data-testid="breadcrumb-separator"]');
    await expect(separators).toHaveCount(2); // Should have n-1 separators for n items

    // Verify separator content
    await expect(separators.first()).toContainText('/');
  });

  test('should handle long breadcrumb paths with truncation', async () => {
    // Mock a very long path
    await page.route('**/api/breadcrumbs**', route => {
      route.fulfill({
        json: [
          { label: 'Dashboard', path: '/' },
          { label: 'Very Long Category Name That Should Be Truncated', path: '/long-category' },
          { label: 'Another Very Long Subcategory Name', path: '/long-category/long-subcategory' },
          { label: 'Final Very Long Page Name That Exceeds Normal Length', path: '/long-category/long-subcategory/final' }
        ]
      });
    });

    await page.goto('/long-category/long-subcategory/final');
    await page.waitForLoadState('networkidle');

    const breadcrumbsContainer = page.locator('[data-testid="breadcrumbs"]');
    
    // Verify container doesn't overflow
    const containerWidth = await breadcrumbsContainer.evaluate(el => el.scrollWidth);
    const viewportWidth = await page.viewportSize();
    expect(containerWidth).toBeLessThanOrEqual(viewportWidth!.width);

    // Verify truncation indicators
    const truncatedItems = page.locator('[data-testid^="breadcrumb-"][data-truncated="true"]');
    await expect(truncatedItems.first()).toBeVisible();
  });

  test('should support keyboard navigation', async () => {
    await page.goto('/agents/contentmind');
    await page.waitForLoadState('networkidle');

    // Tab to first breadcrumb
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab'); // Skip sidebar toggle, etc.
    
    const firstBreadcrumb = page.locator('[data-testid="breadcrumb-0"]');
    await expect(firstBreadcrumb).toBeFocused();

    // Navigate with arrow keys
    await page.keyboard.press('ArrowRight');
    const secondBreadcrumb = page.locator('[data-testid="breadcrumb-1"]');
    await expect(secondBreadcrumb).toBeFocused();

    // Navigate back
    await page.keyboard.press('ArrowLeft');
    await expect(firstBreadcrumb).toBeFocused();

    // Press Enter to navigate
    await page.keyboard.press('Enter');
    await page.waitForURL('**/');
    expect(page.url()).toContain('/');
  });

  test('should show tooltips for truncated breadcrumbs', async () => {
    // Create a scenario with long breadcrumb text
    await page.goto('/agents/contentmind');
    await page.waitForLoadState('networkidle');

    // Mock truncated breadcrumb
    await page.evaluate(() => {
      const breadcrumb = document.querySelector('[data-testid="breadcrumb-1"]');
      if (breadcrumb) {
        breadcrumb.setAttribute('data-truncated', 'true');
        breadcrumb.setAttribute('title', 'Full breadcrumb text that was truncated');
      }
    });

    const truncatedBreadcrumb = page.locator('[data-testid="breadcrumb-1"][data-truncated="true"]');
    
    // Hover to show tooltip
    await truncatedBreadcrumb.hover();
    
    // Verify tooltip appears
    const tooltip = page.locator('[data-testid="breadcrumb-tooltip"]');
    await expect(tooltip).toBeVisible();
    await expect(tooltip).toContainText('Full breadcrumb text that was truncated');
  });

  test('should update on route changes', async () => {
    // Start at root
    await page.goto('/');
    let breadcrumbItems = page.locator('[data-testid^="breadcrumb-"]');
    await expect(breadcrumbItems).toHaveCount(1);

    // Navigate to agents
    await page.goto('/agents');
    await page.waitForLoadState('networkidle');
    breadcrumbItems = page.locator('[data-testid^="breadcrumb-"]');
    await expect(breadcrumbItems).toHaveCount(2);

    // Navigate to contentmind
    await page.goto('/agents/contentmind');
    await page.waitForLoadState('networkidle');
    breadcrumbItems = page.locator('[data-testid^="breadcrumb-"]');
    await expect(breadcrumbItems).toHaveCount(3);

    // Navigate back to root
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    breadcrumbItems = page.locator('[data-testid^="breadcrumb-"]');
    await expect(breadcrumbItems).toHaveCount(1);
  });

  test('should handle special characters in breadcrumb paths', async () => {
    // Mock paths with special characters
    const specialPaths = [
      { path: '/agents/content-mind', label: 'Content-Mind' },
      { path: '/workflows/roi%20analysis', label: 'ROI Analysis' },
      { path: '/data/user_profiles', label: 'User Profiles' }
    ];

    for (const specialPath of specialPaths) {
      await page.goto(specialPath.path);
      await page.waitForLoadState('networkidle');

      const breadcrumbItems = page.locator('[data-testid^="breadcrumb-"]');
      const lastBreadcrumb = breadcrumbItems.last();
      
      await expect(lastBreadcrumb).toContainText(specialPath.label);
    }
  });

  test('should be responsive on mobile devices', async () => {
    // Set mobile viewport
    await page.setViewportSize(navigationData.responsiveBreakpoints.find(b => b.name === 'mobile')!);

    await page.goto('/agents/contentmind');
    await page.waitForLoadState('networkidle');

    const breadcrumbsContainer = page.locator('[data-testid="breadcrumbs"]');
    await expect(breadcrumbsContainer).toBeVisible();

    // On mobile, breadcrumbs should stack or scroll horizontally
    const containerHeight = await breadcrumbsContainer.evaluate(el => el.getBoundingClientRect().height);
    expect(containerHeight).toBeGreaterThan(0);

    // Verify breadcrumbs are still functional
    const firstBreadcrumb = page.locator('[data-testid="breadcrumb-0"]');
    await firstBreadcrumb.click();
    await page.waitForURL('**/');
  });

  test('should show home icon for root breadcrumb', async () => {
    await page.goto('/agents/contentmind');
    await page.waitForLoadState('networkidle');

    const homeBreadcrumb = page.locator('[data-testid="breadcrumb-0"]');
    const homeIcon = homeBreadcrumb.locator('[data-testid="home-icon"]');
    
    await expect(homeIcon).toBeVisible();
    await expect(homeBreadcrumb).toContainText('Dashboard');
  });

  test('should handle rapid navigation changes', async () => {
    // Navigate rapidly between routes
    const routes = ['/agents', '/knowledge', '/roi-workflow', '/inbox'];
    
    for (const route of routes) {
      await page.goto(route);
      // Don't wait for full load to test rapid changes
      await page.waitForTimeout(100);
    }

    // Wait for final navigation to complete
    await page.waitForLoadState('networkidle');

    // Verify final breadcrumbs are correct
    const breadcrumbItems = page.locator('[data-testid^="breadcrumb-"]');
    const lastBreadcrumb = breadcrumbItems.last();
    await expect(lastBreadcrumb).toContainText('Inbox');
  });

  test('should highlight current page in breadcrumbs', async () => {
    await page.goto('/agents/contentmind');
    await page.waitForLoadState('networkidle');

    // Current page (last breadcrumb) should be highlighted
    const currentBreadcrumb = page.locator('[data-testid^="breadcrumb-"]').last();
    await expect(currentBreadcrumb).toHaveAttribute('data-current', 'true');
    
    // Previous breadcrumbs should not be highlighted
    const previousBreadcrumbs = page.locator('[data-testid^="breadcrumb-"]:not(:last-child)');
    const count = await previousBreadcrumbs.count();
    
    for (let i = 0; i < count; i++) {
      const breadcrumb = previousBreadcrumbs.nth(i);
      await expect(breadcrumb).toHaveAttribute('data-current', 'false');
    }
  });

  test('should handle empty or invalid paths gracefully', async () => {
    // Test various edge cases
    const edgeCases = ['', '//double-slash', '/non-existent-route'];
    
    for (const edgeCase of edgeCases) {
      await page.goto(edgeCase || '/');
      await page.waitForLoadState('networkidle');

      // Should always show at least the home breadcrumb
      const breadcrumbItems = page.locator('[data-testid^="breadcrumb-"]');
      await expect(breadcrumbItems).toHaveCount({ min: 1 });
      
      const firstBreadcrumb = breadcrumbItems.first();
      await expect(firstBreadcrumb).toContainText('Dashboard');
    }
  });
});