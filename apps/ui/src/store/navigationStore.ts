import { create } from 'zustand';

export interface Breadcrumb {
  label: string;
  path: string;
  isActive?: boolean;
}

interface NavigationStore {
  // State
  isCollapsed: boolean;
  isMobileMenuOpen: boolean;
  isCommandPaletteOpen: boolean;
  activeRoute: string;
  breadcrumbs: Breadcrumb[];
  
  // Actions
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleMobileMenu: () => void;
  setMobileMenuOpen: (open: boolean) => void;
  toggleCommandPalette: () => void;
  setActiveRoute: (route: string) => void;
  updateBreadcrumbs: (crumbs: Breadcrumb[]) => void;
}

export const useNavigationStore = create<NavigationStore>((set, get) => ({
  // Initial state
  isCollapsed: false,
  isMobileMenuOpen: false,
  isCommandPaletteOpen: false,
  activeRoute: '/',
  breadcrumbs: [{ label: 'Dashboard', path: '/', isActive: true }],
  
  // Actions
  toggleSidebar: () => set((state) => ({ isCollapsed: !state.isCollapsed })),
  
  setSidebarCollapsed: (collapsed: boolean) => set({ isCollapsed: collapsed }),
  
  toggleMobileMenu: () => set((state) => ({ isMobileMenuOpen: !state.isMobileMenuOpen })),
  
  setMobileMenuOpen: (open: boolean) => set({ isMobileMenuOpen: open }),
  
  toggleCommandPalette: () => set((state) => ({ isCommandPaletteOpen: !state.isCommandPaletteOpen })),
  
  setActiveRoute: (route: string) => set({ activeRoute: route }),
  
  updateBreadcrumbs: (crumbs: Breadcrumb[]) => set({ breadcrumbs: crumbs }),
}));

// Helper function to generate breadcrumbs from route
export const generateBreadcrumbs = (pathname: string): Breadcrumb[] => {
  const routes: { [key: string]: string } = {
    '/': 'Dashboard',
    '/inbox': 'Inbox',
    '/knowledge': 'Knowledge',
    '/agents': 'Agents',
    '/terminal': 'Terminal',
    '/logs': 'Logs',
    '/settings': 'Settings',
    '/roi-workflow': 'ROI Workflow',
  };

  if (pathname === '/') {
    return [{ label: 'Dashboard', path: '/', isActive: true }];
  }

  const segments = pathname.split('/').filter(Boolean);
  const breadcrumbs: Breadcrumb[] = [
    { label: 'Dashboard', path: '/', isActive: false }
  ];

  let currentPath = '';
  segments.forEach((segment, index) => {
    currentPath += `/${segment}`;
    const label = routes[currentPath] || segment.charAt(0).toUpperCase() + segment.slice(1);
    const isActive = index === segments.length - 1;
    
    breadcrumbs.push({
      label,
      path: currentPath,
      isActive
    });
  });

  return breadcrumbs;
}; 