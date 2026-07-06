import { createHashRouter } from 'react-router-dom'
import { AppShell } from '@/components/layout/app-shell'
import { CalendarScreen } from '@/screens/calendar-screen'
import { ChatScreen } from '@/screens/chat-screen'
import { HomeScreen } from '@/screens/home-screen'
import { KnowledgeGraphScreen } from '@/screens/knowledge-graph-screen'
import { MemoryScreen } from '@/screens/memory-screen'
import { ProductsScreen } from '@/screens/products-screen'
import { SettingsScreen } from '@/screens/settings-screen'
import { SpendingScreen } from '@/screens/spending-screen'
import { TasksScreen } from '@/screens/tasks-screen'

export const router = createHashRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <HomeScreen /> },
      { path: 'chat', element: <ChatScreen /> },
      { path: 'memory', element: <MemoryScreen /> },
      { path: 'knowledge-graph', element: <KnowledgeGraphScreen /> },
      { path: 'calendar', element: <CalendarScreen /> },
      { path: 'tasks', element: <TasksScreen /> },
      { path: 'spending', element: <SpendingScreen /> },
      { path: 'products', element: <ProductsScreen /> },
      { path: 'settings', element: <SettingsScreen /> },
    ],
  },
])
