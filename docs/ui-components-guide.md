# UI Components Guide

This guide documents all the reusable UI components in the Bluelabel AIOS frontend, including usage examples and customization options.

## Component Library Overview

The Bluelabel AIOS uses a custom retro/cyberpunk design system with ASCII art borders, terminal-style interfaces, and neon color schemes.

## Core Components

### RetroButton

A styled button component with ASCII borders and glow effects.

**Props:**
- `variant`: 'primary' | 'secondary' | 'danger' | 'success'
- `size`: 'sm' | 'md' | 'lg'
- `onClick`: Click handler
- `disabled`: Boolean
- `children`: Button content

**Usage:**
```tsx
import { RetroButton } from '@/components/UI/RetroButton';

<RetroButton 
  variant="primary" 
  onClick={handleClick}
>
  EXECUTE
</RetroButton>
```

**Styling Classes:**
- `.retro-button-glow` - Neon glow effect
- `.retro-button-pulse` - Pulsing animation
- `.retro-button-disabled` - Disabled state

### RetroCard

Container component with ASCII art borders and optional glow effects.

**Props:**
- `title`: Optional header title
- `variant`: 'default' | 'info' | 'warning' | 'error'
- `padding`: 'none' | 'sm' | 'md' | 'lg'
- `children`: Card content

**Usage:**
```tsx
import { RetroCard } from '@/components/UI/RetroCard';

<RetroCard title="SYSTEM STATUS" variant="info">
  <p>All systems operational</p>
</RetroCard>
```

**Features:**
- ASCII corner decorations
- Animated border effects
- Customizable header styles

### Terminal

Full-featured terminal emulator component.

**Props:**
- `height`: Terminal height (CSS value)
- `initialCommands`: Array of commands to pre-populate
- `onCommand`: Command execution callback

**Usage:**
```tsx
import { Terminal } from '@/components/Terminal/Terminal';

<Terminal 
  height="600px"
  onCommand={handleCommand}
/>
```

**Sub-components:**
- `CommandInput` - Input field with prompt
- `OutputLine` - Styled output display

### PixelLogo

Retro-style animated logo component.

**Props:**
- `size`: 'sm' | 'md' | 'lg' | 'xl'
- `animated`: Boolean
- `glitch`: Boolean - Enable glitch effect

**Usage:**
```tsx
import { PixelLogo } from '@/components/UI/PixelLogo';

<PixelLogo size="lg" animated glitch />
```

### RainbowStripe

Decorative header stripe with animated rainbow gradient.

**Props:**
- `height`: Stripe height
- `speed`: Animation speed (1-10)

**Usage:**
```tsx
import { RainbowStripe } from '@/components/UI/RainbowStripe';

<RainbowStripe height="4px" speed={5} />
```

### RetroLoader

Loading spinner with retro aesthetics.

**Props:**
- `size`: 'sm' | 'md' | 'lg'
- `color`: 'primary' | 'secondary' | 'success'
- `text`: Optional loading text

**Usage:**
```tsx
import { RetroLoader } from '@/components/UI/RetroLoader';

<RetroLoader size="md" text="PROCESSING..." />
```

**Variants:**
- Spinning ASCII characters
- Matrix-style cascade
- Terminal cursor blink

### StartupSequence

Boot animation component for app initialization.

**Props:**
- `duration`: Animation duration in ms
- `onComplete`: Completion callback
- `steps`: Array of boot messages

**Usage:**
```tsx
import { StartupSequence } from '@/components/UI/StartupSequence';

<StartupSequence 
  duration={3000}
  onComplete={() => setReady(true)}
  steps={[
    "INITIALIZING SYSTEM...",
    "LOADING AGENTS...",
    "ESTABLISHING CONNECTIONS...",
    "SYSTEM READY"
  ]}
/>
```

## Modal Components

### KnowledgeDetailModal

Modal for displaying knowledge base entries.

**Props:**
- `isOpen`: Boolean
- `onClose`: Close handler
- `entry`: Knowledge entry object

**Usage:**
```tsx
import { KnowledgeDetailModal } from '@/components/UI/KnowledgeDetailModal';

<KnowledgeDetailModal 
  isOpen={showModal}
  onClose={() => setShowModal(false)}
  entry={selectedEntry}
/>
```

### FileUploadModal

Drag-and-drop file upload interface.

**Props:**
- `isOpen`: Boolean
- `onClose`: Close handler
- `onUpload`: File upload callback
- `acceptedTypes`: Array of file types

**Usage:**
```tsx
import { FileUploadModal } from '@/components/UI/FileUploadModal';

<FileUploadModal 
  isOpen={uploadOpen}
  onClose={() => setUploadOpen(false)}
  onUpload={handleFileUpload}
  acceptedTypes={['.pdf', '.txt', '.md']}
/>
```

## Layout Components

### SidebarNav

Main navigation sidebar component.

**Props:**
- `items`: Array of navigation items
- `activeItem`: Currently active route
- `collapsed`: Boolean for collapsed state

**Usage:**
```tsx
import { SidebarNav } from '@/components/Layout/SidebarNav';

<SidebarNav 
  items={navItems}
  activeItem={currentPath}
  collapsed={isCollapsed}
/>
```

**Features:**
- Animated expand/collapse
- Active item highlighting
- Icon support
- Nested navigation

## Styling Guidelines

### Color Variables

```css
:root {
  --terminal-green: #00ff41;
  --terminal-amber: #ffb000;
  --terminal-cyan: #00bcd4;
  --terminal-red: #ff0040;
  --bg-dark: #0a0e1b;
  --bg-card: #101828;
  --border-primary: #00ff41;
}
```

### Common CSS Classes

```css
.ascii-border - ASCII art borders
.terminal-glow - Neon glow effect
.scanline - CRT scanline effect
.glitch-text - Glitch text animation
.matrix-bg - Matrix rain background
```

### Animation Utilities

```css
.pulse - Pulsing animation
.flicker - Flickering effect
.slide-in - Slide in animation
.fade-in - Fade in effect
.typewriter - Typewriter text effect
```

## Best Practices

### Component Usage

1. Always provide ARIA labels for accessibility
2. Use semantic HTML elements
3. Include loading states for async operations
4. Handle error states gracefully
5. Implement keyboard navigation where appropriate

### Performance

1. Use React.memo for expensive components
2. Implement virtual scrolling for long lists
3. Lazy load heavy components
4. Optimize re-renders with proper key usage
5. Use CSS animations over JS when possible

### Accessibility

1. Maintain proper color contrast ratios
2. Provide keyboard navigation
3. Include screen reader support
4. Add focus indicators
5. Support reduced motion preferences

## Customization

### Theming

Components support theme customization through CSS variables:

```tsx
// Theme provider setup
<ThemeProvider theme={customTheme}>
  <App />
</ThemeProvider>

// Custom theme
const customTheme = {
  colors: {
    primary: '#00ff41',
    secondary: '#ffb000',
    background: '#0a0e1b'
  },
  fonts: {
    mono: "'Berkeley Mono', monospace"
  }
};
```

### Component Extensions

Create custom variants by extending base components:

```tsx
// Custom button variant
export const GlitchButton = styled(RetroButton)`
  animation: glitch 2s infinite;
  
  &:hover {
    animation-duration: 0.5s;
  }
`;
```

## Component Playground

Test components in isolation:

```bash
npm run storybook
```

View component documentation and examples at:
```
http://localhost:6006
```

## Future Components

### Planned for Phase 2

1. **ChartDisplay** - Data visualization with retro styling
2. **NotificationToast** - System notifications
3. **ContextMenu** - Right-click menus
4. **TreeView** - Hierarchical data display
5. **DragDropZone** - Advanced file handling

### Planned for Phase 3

1. **VirtualTerminal** - Advanced terminal features
2. **GraphViewer** - Knowledge graph visualization
3. **TimelineView** - Event timeline display
4. **CodeEditor** - Syntax highlighted editor
5. **MetricsChart** - Real-time metrics display

---

Last Updated: January 2025
Version: 1.0.0