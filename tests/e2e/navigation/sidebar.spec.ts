import { test, expect, Page } from '@playwright/test';
import navigationData from '../fixtures/navigation-test-data.json';

test.describe('Sidebar Navigation', () => {
  let page: Page;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display sidebar with all navigation items', async () => {
    // Verify sidebar is visible
    const sidebar = page.locator('[data-testid="sidebar"]');
    await expect(sidebar).toBeVisible();

    // Verify main navigation items are present
    for (const route of navigationData.routes.filter(r => r.category === 'main')) {
      const navItem = page.locator(`[data-testid="nav-item-${route.path.replace('/', '')}"]`);
      await expect(navItem).toBeVisible();
      await expect(navItem).toContainText(route.label);
    }
  });

  test('should collapse and expand sidebar on desktop', async () => {
    // Ensure we're on desktop viewport
    await page.setViewportSize({ width: 1440, height: 900 });

    const sidebar = page.locator('[data-testid="sidebar"]');
    const toggleButton = page.locator('[data-testid="sidebar-toggle"]');

    // Verify sidebar starts expanded
    await expect(sidebar).toHaveAttribute('data-expanded', 'true');

    // Click toggle to collapse
    await toggleButton.click();
    
    // Verify sidebar is collapsed
    await expect(sidebar).toHaveAttribute('data-expanded', 'false');
    
    // Verify animation completes
    await page.waitForTimeout(navigationData.animations.sidebar.collapse.duration + 50);

    // Click toggle to expand
    await toggleButton.click();
    
    // Verify sidebar is expanded
    await expect(sidebar).toHaveAttribute('data-expanded', 'true');
    
    // Verify animation completes
    await page.waitForTimeout(navigationData.animations.sidebar.expand.duration + 50);
  });

  test('should persist sidebar state in localStorage', async () => {
    const toggleButton = page.locator('[data-testid="sidebar-toggle"]');

    // Collapse sidebar
    await toggleButton.click();
    await page.waitForTimeout(300);

    // Check localStorage
    const isCollapsed = await page.evaluate(() => {
      return localStorage.getItem('sidebar-collapsed') === 'true';
    });
    expect(isCollapsed).toBe(true);

    // Refresh page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify sidebar state persisted
    const sidebar = page.locator('[data-testid="sidebar"]');
    await expect(sidebar).toHaveAttribute('data-expanded', 'false');
  });

  test('should switch to overlay mode on tablet', async () => {
    // Set tablet viewport
    await page.setViewportSize(navigationData.responsiveBreakpoints.find(b => b.name === 'tablet')!);

    const sidebar = page.locator('[data-testid="sidebar"]');
    const overlay = page.locator('[data-testid="sidebar-overlay"]');

    // On tablet, sidebar should be hidden initially
    await expect(sidebar).toHaveAttribute('data-mode', 'overlay');
    await expect(sidebar).toHaveAttribute('data-visible', 'false');

    // Open sidebar via toggle
    const toggleButton = page.locator('[data-testid="sidebar-toggle"]');
    await toggleButton.click();

    // Verify overlay mode
    await expect(sidebar).toHaveAttribute('data-visible', 'true');
    await expect(overlay).toBeVisible();

    // Click overlay to close
    await overlay.click();
    
    // Verify sidebar closes
    await expect(sidebar).toHaveAttribute('data-visible', 'false');
    await expect(overlay).not.toBeVisible();
  });

  test('should show bottom navigation on mobile', async () => {
    // Set mobile viewport
    await page.setViewportSize(navigationData.responsiveBreakpoints.find(b => b.name === 'mobile')!);

    // Verify bottom navigation appears
    const bottomNav = page.locator('[data-testid="bottom-navigation"]');
    await expect(bottomNav).toBeVisible();

    // Verify main items are in bottom nav
    const mainRoutes = navigationData.routes.filter(r => r.category === 'main').slice(0, 4);
    for (const route of mainRoutes) {
      const bottomNavItem = page.locator(`[data-testid="bottom-nav-${route.path.replace('/', '')}"]`);
      await expect(bottomNavItem).toBeVisible();
    }

    // Verify sidebar is hidden on mobile
    const sidebar = page.locator('[data-testid="sidebar"]');
    await expect(sidebar).not.toBeVisible();
  });

  test('should highlight active navigation item', async () => {
    // Navigate to different pages and verify active state
    for (const route of navigationData.routes.slice(0, 3)) {
      await page.goto(route.path);
      await page.waitForLoadState('networkidle');

      const navItem = page.locator(`[data-testid="nav-item-${route.path.replace('/', '')}"]`);
      await expect(navItem).toHaveAttribute('data-active', 'true');
      
      // Verify only one item is active
      const activeItems = page.locator('[data-testid^="nav-item-"][data-active="true"]');
      await expect(activeItems).toHaveCount(1);
    }
  });

  test('should display icons and labels correctly', async () => {
    const sidebar = page.locator('[data-testid="sidebar"]');
    
    // Verify expanded state shows both icons and labels
    await expect(sidebar).toHaveAttribute('data-expanded', 'true');
    
    for (const route of navigationData.routes.filter(r => r.category === 'main')) {
      const navItem = page.locator(`[data-testid="nav-item-${route.path.replace('/', '')}"]`);
      
      // Check icon is present
      const icon = navItem.locator('[data-testid="nav-icon"]');
      await expect(icon).toBeVisible();
      
      // Check label is present and visible
      const label = navItem.locator('[data-testid="nav-label"]');
      await expect(label).toBeVisible();
      await expect(label).toContainText(route.label);
    }

    // Collapse sidebar and verify only icons visible
    const toggleButton = page.locator('[data-testid="sidebar-toggle"]');
    await toggleButton.click();
    await page.waitForTimeout(250);

    for (const route of navigationData.routes.filter(r => r.category === 'main')) {
      const navItem = page.locator(`[data-testid="nav-item-${route.path.replace('/', '')}"]`);
      
      // Icon should still be visible
      const icon = navItem.locator('[data-testid="nav-icon"]');
      await expect(icon).toBeVisible();
      
      // Label should be hidden in collapsed state
      const label = navItem.locator('[data-testid="nav-label"]');
      await expect(label).not.toBeVisible();
    }
  });

  test('should support keyboard navigation', async () => {
    // Focus on first navigation item
    await page.keyboard.press('Tab');
    
    const firstNavItem = page.locator('[data-testid^="nav-item-"]').first();
    await expect(firstNavItem).toBeFocused();

    // Navigate through items with arrow keys
    await page.keyboard.press('ArrowDown');
    const secondNavItem = page.locator('[data-testid^="nav-item-"]').nth(1);
    await expect(secondNavItem).toBeFocused();

    // Navigate up
    await page.keyboard.press('ArrowUp');
    await expect(firstNavItem).toBeFocused();

    // Press Enter to navigate
    await page.keyboard.press('Enter');
    
    // Verify navigation occurred
    const currentUrl = page.url();
    expect(currentUrl).toContain(navigationData.routes[0].path);
  });

  test('should show tooltips on hover in collapsed state', async () => {
    // Collapse sidebar
    const toggleButton = page.locator('[data-testid="sidebar-toggle"]');
    await toggleButton.click();
    await page.waitForTimeout(250);

    // Hover over navigation item
    const navItem = page.locator('[data-testid^="nav-item-"]').first();
    await navItem.hover();

    // Verify tooltip appears
    const tooltip = page.locator('[data-testid="nav-tooltip"]');
    await expect(tooltip).toBeVisible();
    await expect(tooltip).toContainText(navigationData.routes[0].label);

    // Move away and verify tooltip disappears
    await page.locator('body').hover();
    await expect(tooltip).not.toBeVisible();
  });

  test('should handle nested navigation items', async () => {
    // Navigate to agents page
    await page.goto('/agents');
    await page.waitForLoadState('networkidle');

    // Verify agents parent item is active
    const agentsItem = page.locator('[data-testid="nav-item-agents"]');
    await expect(agentsItem).toHaveAttribute('data-active', 'true');

    // Verify sub-navigation appears
    const subNav = page.locator('[data-testid="agents-subnav"]');
    await expect(subNav).toBeVisible();

    // Navigate to ContentMind
    await page.goto('/agents/contentmind');
    await page.waitForLoadState('networkidle');

    // Verify both parent and child are highlighted
    await expect(agentsItem).toHaveAttribute('data-active', 'true');
    const contentMindItem = page.locator('[data-testid="nav-item-contentmind"]');
    await expect(contentMindItem).toHaveAttribute('data-active', 'true');
  });

  test('should animate smoothly during state changes', async () => {
    const sidebar = page.locator('[data-testid="sidebar"]');
    const toggleButton = page.locator('[data-testid="sidebar-toggle"]');

    // Measure initial width
    const initialWidth = await sidebar.evaluate(el => el.getBoundingClientRect().width);

    // Start collapse animation
    await toggleButton.click();

    // Check that animation is in progress (width should be changing)
    await page.waitForTimeout(50); // Small delay to ensure animation started
    const midWidth = await sidebar.evaluate(el => el.getBoundingClientRect().width);
    expect(midWidth).toBeLessThan(initialWidth);

    // Wait for animation to complete
    await page.waitForTimeout(navigationData.animations.sidebar.collapse.duration);
    
    const finalWidth = await sidebar.evaluate(el => el.getBoundingClientRect().width);
    expect(finalWidth).toBeLessThan(initialWidth);
  });
});