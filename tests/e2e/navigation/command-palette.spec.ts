import { test, expect, Page } from '@playwright/test';
import navigationData from '../fixtures/navigation-test-data.json';

test.describe('Command Palette', () => {
  let page: Page;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should open with Ctrl+K keyboard shortcut', async () => {
    const commandPalette = page.locator('[data-testid="command-palette"]');
    
    // Verify command palette is hidden initially
    await expect(commandPalette).not.toBeVisible();

    // Open with keyboard shortcut
    await page.keyboard.press('Control+k');
    
    // Verify command palette opens
    await expect(commandPalette).toBeVisible();
    
    // Verify search input is focused
    const searchInput = page.locator('[data-testid="command-search-input"]');
    await expect(searchInput).toBeFocused();
  });

  test('should open with Cmd+K on macOS', async () => {
    // Simulate macOS
    await page.evaluate(() => {
      Object.defineProperty(navigator, 'platform', {
        value: 'MacIntel',
        writable: true
      });
    });

    const commandPalette = page.locator('[data-testid="command-palette"]');
    
    // Open with Mac keyboard shortcut
    await page.keyboard.press('Meta+k');
    
    // Verify command palette opens
    await expect(commandPalette).toBeVisible();
  });

  test('should close with Escape key', async () => {
    const commandPalette = page.locator('[data-testid="command-palette"]');
    
    // Open command palette
    await page.keyboard.press('Control+k');
    await expect(commandPalette).toBeVisible();

    // Close with Escape
    await page.keyboard.press('Escape');
    
    // Verify command palette closes
    await expect(commandPalette).not.toBeVisible();
  });

  test('should close when clicking outside', async () => {
    const commandPalette = page.locator('[data-testid="command-palette"]');
    const overlay = page.locator('[data-testid="command-palette-overlay"]');
    
    // Open command palette
    await page.keyboard.press('Control+k');
    await expect(commandPalette).toBeVisible();

    // Click outside (on overlay)
    await overlay.click();
    
    // Verify command palette closes
    await expect(commandPalette).not.toBeVisible();
  });

  test('should display all available commands initially', async () => {
    // Open command palette
    await page.keyboard.press('Control+k');
    
    const commandsList = page.locator('[data-testid="commands-list"]');
    await expect(commandsList).toBeVisible();

    // Verify some default commands are visible
    for (const command of navigationData.commands.slice(0, 5)) {
      const commandItem = page.locator(`[data-testid="command-${command.id}"]`);
      await expect(commandItem).toBeVisible();
      await expect(commandItem).toContainText(command.label);
    }
  });

  test('should perform fuzzy search correctly', async () => {
    // Open command palette
    await page.keyboard.press('Control+k');
    const searchInput = page.locator('[data-testid="command-search-input"]');

    // Test each search query
    for (const searchTest of navigationData.searchQueries) {
      // Clear and type search query
      await searchInput.clear();
      await searchInput.type(searchTest.query);
      
      // Wait for search results
      await page.waitForTimeout(100);

      if (searchTest.expected.length > 0) {
        // Verify expected results appear
        for (const expectedResult of searchTest.expected) {
          const resultItem = page.locator('[data-testid^="command-"]', { hasText: expectedResult });
          await expect(resultItem).toBeVisible();
        }
      } else {
        // Verify no results message for empty results
        const noResults = page.locator('[data-testid="no-results"]');
        await expect(noResults).toBeVisible();
      }
    }
  });

  test('should highlight search matches', async () => {
    // Open command palette
    await page.keyboard.press('Control+k');
    const searchInput = page.locator('[data-testid="command-search-input"]');

    // Search for "dash"
    await searchInput.type('dash');
    await page.waitForTimeout(100);

    // Verify search highlights
    const dashboardCommand = page.locator('[data-testid^="command-"]', { hasText: 'Dashboard' });
    const highlight = dashboardCommand.locator('.search-highlight');
    await expect(highlight).toBeVisible();
    await expect(highlight).toContainText('Dash');
  });

  test('should navigate results with keyboard', async () => {
    // Open command palette
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(100);

    const firstCommand = page.locator('[data-testid^="command-"]').first();
    const secondCommand = page.locator('[data-testid^="command-"]').nth(1);

    // First item should be highlighted by default
    await expect(firstCommand).toHaveAttribute('data-highlighted', 'true');

    // Navigate down
    await page.keyboard.press('ArrowDown');
    await expect(secondCommand).toHaveAttribute('data-highlighted', 'true');
    await expect(firstCommand).toHaveAttribute('data-highlighted', 'false');

    // Navigate back up
    await page.keyboard.press('ArrowUp');
    await expect(firstCommand).toHaveAttribute('data-highlighted', 'true');
    await expect(secondCommand).toHaveAttribute('data-highlighted', 'false');
  });

  test('should execute navigation commands with Enter', async () => {
    // Open command palette
    await page.keyboard.press('Control+k');
    const searchInput = page.locator('[data-testid="command-search-input"]');

    // Search for agents
    await searchInput.type('agents');
    await page.waitForTimeout(100);

    // Execute with Enter
    await page.keyboard.press('Enter');

    // Verify navigation occurred
    await page.waitForURL('**/agents');
    expect(page.url()).toContain('/agents');

    // Verify command palette closed
    const commandPalette = page.locator('[data-testid="command-palette"]');
    await expect(commandPalette).not.toBeVisible();
  });

  test('should execute action commands', async () => {
    // Open command palette
    await page.keyboard.press('Control+k');
    const searchInput = page.locator('[data-testid="command-search-input"]');

    // Search for toggle sidebar
    await searchInput.type('toggle sidebar');
    await page.waitForTimeout(100);

    const sidebar = page.locator('[data-testid="sidebar"]');
    const initialState = await sidebar.getAttribute('data-expanded');

    // Execute command
    await page.keyboard.press('Enter');

    // Verify sidebar state changed
    await page.waitForTimeout(250);
    const newState = await sidebar.getAttribute('data-expanded');
    expect(newState).not.toBe(initialState);
  });

  test('should show command categories', async () => {
    // Open command palette
    await page.keyboard.press('Control+k');
    
    // Verify category headers are visible
    const navigationCategory = page.locator('[data-testid="category-navigation"]');
    const actionCategory = page.locator('[data-testid="category-action"]');
    
    await expect(navigationCategory).toBeVisible();
    await expect(actionCategory).toBeVisible();
  });

  test('should show recent commands', async () => {
    // Navigate to a few pages to create history
    await page.goto('/agents');
    await page.goto('/knowledge');
    await page.goto('/');

    // Open command palette
    await page.keyboard.press('Control+k');
    
    // Verify recent section appears
    const recentSection = page.locator('[data-testid="recent-commands"]');
    await expect(recentSection).toBeVisible();

    // Verify recent items are listed
    const recentItems = page.locator('[data-testid^="recent-"]');
    await expect(recentItems).toHaveCount({ min: 2 });
  });

  test('should handle mouse interactions', async () => {
    // Open command palette
    await page.keyboard.press('Control+k');
    
    const firstCommand = page.locator('[data-testid^="command-"]').first();
    
    // Hover to highlight
    await firstCommand.hover();
    await expect(firstCommand).toHaveAttribute('data-highlighted', 'true');

    // Click to execute
    await firstCommand.click();

    // Verify command palette closes
    const commandPalette = page.locator('[data-testid="command-palette"]');
    await expect(commandPalette).not.toBeVisible();
  });

  test('should debounce search input', async () => {
    // Open command palette
    await page.keyboard.press('Control+k');
    const searchInput = page.locator('[data-testid="command-search-input"]');

    // Track search requests
    let searchCount = 0;
    await page.route('**/api/search**', route => {
      searchCount++;
      route.continue();
    });

    // Type quickly
    await searchInput.type('dashboard', { delay: 50 });
    
    // Wait for debounce period
    await page.waitForTimeout(300);

    // Should have made fewer requests than characters typed
    expect(searchCount).toBeLessThan(9);
  });

  test('should handle special characters in search', async () => {
    // Open command palette
    await page.keyboard.press('Control+k');
    const searchInput = page.locator('[data-testid="command-search-input"]');

    // Test special characters
    const specialQueries = ['@agent', '#roi', '$workflow', '%test'];
    
    for (const query of specialQueries) {
      await searchInput.clear();
      await searchInput.type(query);
      await page.waitForTimeout(100);

      // Should not crash and should show appropriate results or no results
      const commandsList = page.locator('[data-testid="commands-list"]');
      await expect(commandsList).toBeVisible();
    }
  });

  test('should show keyboard shortcuts in commands', async () => {
    // Open command palette
    await page.keyboard.press('Control+k');
    
    // Look for commands with keyboard shortcuts
    const toggleSidebarCommand = page.locator('[data-testid^="command-"]', { hasText: 'Toggle Sidebar' });
    const shortcut = toggleSidebarCommand.locator('[data-testid="command-shortcut"]');
    
    await expect(shortcut).toBeVisible();
    await expect(shortcut).toContainText('Ctrl+B');
  });

  test('should maintain focus within command palette', async () => {
    // Open command palette
    await page.keyboard.press('Control+k');
    const searchInput = page.locator('[data-testid="command-search-input"]');
    
    // Try to tab outside - focus should stay within
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Focus should cycle back to search input or stay within palette
    const focusedElement = page.locator(':focus');
    const paletteElements = page.locator('[data-testid="command-palette"] *');
    
    const isFocusWithinPalette = await focusedElement.evaluate((focused, paletteContainer) => {
      return paletteContainer.contains(focused);
    }, await paletteElements.first().elementHandle());
    
    expect(isFocusWithinPalette).toBe(true);
  });

  test('should animate open and close transitions', async () => {
    const commandPalette = page.locator('[data-testid="command-palette"]');
    
    // Open command palette and check animation
    await page.keyboard.press('Control+k');
    
    // Should start with scale/opacity animation
    const initialTransform = await commandPalette.evaluate(el => 
      window.getComputedStyle(el).transform
    );
    
    // Wait for animation to complete
    await page.waitForTimeout(navigationData.animations.commandPalette.open.duration);
    
    const finalTransform = await commandPalette.evaluate(el => 
      window.getComputedStyle(el).transform
    );
    
    // Transforms should be different (animation occurred)
    expect(finalTransform).not.toBe(initialTransform);
  });
});