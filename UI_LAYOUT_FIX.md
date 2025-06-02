# UI Layout Fix Instructions

## The Problem

The new navigation system is conflicting with the existing layout. The sidebar is overlapping the main content, and the responsive layout isn't working properly.

## Quick Fix

1. **Check if Tailwind classes are loading properly**
   - The navigation uses new custom CSS variables that may not be defined
   - The responsive classes may be conflicting

2. **Verify navigation wrapper integration**
   - The NavigationWrapper should wrap the content properly
   - Main content needs proper margin/padding to account for sidebar

## Immediate Actions Needed

### 1. Add missing CSS classes to index.css
The navigation components use classes like `bg-nav-bg`, `border-nav-border` etc. that need to be defined.

### 2. Fix the layout structure in App.tsx
The current structure has the NavigationWrapper wrapping content, but the padding/margins aren't accounting for the sidebar width.

### 3. Add z-index layering
The sidebar needs proper z-index to not overlap incorrectly.

## Temporary Workaround

To see the content while we fix the layout, you can:

1. **Collapse the sidebar**: Look for a collapse button or try pressing `Ctrl+B`
2. **Close mobile menu**: If on mobile view, try clicking outside the sidebar
3. **Use Command Palette**: Press `Ctrl+K` to navigate without the sidebar

## Root Cause

The issue appears to be:
1. CSS custom properties for navigation colors may not be loading
2. The sidebar is positioned fixed but the main content doesn't have proper margin offset
3. Possible Tailwind purging of dynamic classes

## Next Steps

CA needs to:
1. Verify all CSS is loading correctly
2. Check that Tailwind isn't purging the navigation classes
3. Ensure proper layout spacing between sidebar and content
4. Test on different viewport sizes