import { create } from 'zustand'

type Theme = 'light' | 'dark' | 'system'

interface AppState {
  theme: Theme
  sidebarCollapsed: boolean
  setTheme: (theme: Theme) => void
  toggleSidebar: () => void
}

export const useAppStore = create<AppState>((set) => ({
  theme: 'dark',
  sidebarCollapsed: false,
  setTheme: (theme) => set({ theme }),
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
}))
