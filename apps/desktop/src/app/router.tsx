import { createHashRouter, Navigate } from 'react-router-dom'
import { AppShell } from '@/components/layout/app-shell'
import { FinanceLayout } from '@/components/finance/finance-layout'
import { CalendarScreen } from '@/screens/calendar-screen'
import { ChatScreen } from '@/screens/chat-screen'
import { FinanceAccountsScreen } from '@/screens/finance/finance-accounts-screen'
import { FinanceCashbackScreen } from '@/screens/finance/finance-cashback-screen'
import { FinanceCreditCardsScreen } from '@/screens/finance/finance-credit-cards-screen'
import { FinanceDashboardScreen } from '@/screens/finance/finance-dashboard-screen'
import { FinanceRewardsScreen } from '@/screens/finance/finance-rewards-screen'
import { FinanceStatementsScreen } from '@/screens/finance/finance-statements-screen'
import { FinanceTransactionsScreen } from '@/screens/finance/finance-transactions-screen'
import { HomeScreen } from '@/screens/home-screen'
import { KnowledgeGraphScreen } from '@/screens/knowledge-graph-screen'
import { MemoryScreen } from '@/screens/memory-screen'
import { ProductsScreen } from '@/screens/products-screen'
import { SettingsScreen } from '@/screens/settings-screen'
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
      { path: 'spending', element: <Navigate to="/finance/transactions" replace /> },
      {
        path: 'finance',
        element: <FinanceLayout />,
        children: [
          { index: true, element: <FinanceDashboardScreen /> },
          { path: 'accounts', element: <FinanceAccountsScreen /> },
          { path: 'credit-cards', element: <FinanceCreditCardsScreen /> },
          { path: 'statements', element: <FinanceStatementsScreen /> },
          { path: 'transactions', element: <FinanceTransactionsScreen /> },
          { path: 'rewards', element: <FinanceRewardsScreen /> },
          { path: 'cashback', element: <FinanceCashbackScreen /> },
        ],
      },
      { path: 'products', element: <ProductsScreen /> },
      { path: 'settings', element: <SettingsScreen /> },
    ],
  },
])
