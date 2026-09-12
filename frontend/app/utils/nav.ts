import type { NavItem } from '~/types'
import {
  House,
  SquareCheck,
  Bot,
  Inbox,
  FileText,
  Network,
  BarChart3
} from '@lucide/vue'

export const navItems: NavItem[] = [
  { href: '/', icon: House, label: 'Overview', matchRoutes: ['/'] },
  { href: '/tasks', icon: SquareCheck, label: 'Tasks', matchRoutes: ['/tasks', '/evaluations', '/benchmark'] },
  { href: '/agents', icon: Bot, label: 'Agents', matchRoutes: ['/agents'] },
  { href: '/inbox', icon: Inbox, label: 'Inbox', matchRoutes: ['/inbox'] },
  { href: '/results', icon: FileText, label: 'Results', matchRoutes: ['/results', '/logs'] },
  { href: '/connections', icon: Network, label: 'Connections', matchRoutes: ['/connections', '/pipeline', '/mcp'] },
  { href: '/analytics', icon: BarChart3, label: 'Analytics', matchRoutes: ['/analytics', '/monitoring'] }
]
