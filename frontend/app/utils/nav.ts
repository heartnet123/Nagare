import {
  BarChart2,
  Database,
  Target,
  FileText,
  Workflow,
  Bot,
  Activity,
  Box,
  BookOpen,
  Settings,
  Cpu
} from '@lucide/vue'

export const navGroups = [
  {
    title: 'EVALUATIONS',
    items: [
      { href: '/evaluations', icon: BarChart2, label: 'Evaluations' },
      { href: '/datasets', icon: Database, label: 'Datasets' },
      { href: '/benchmark', icon: Target, label: 'Benchmark' },
      { href: '/logs', icon: FileText, label: 'Logs' }
    ]
  },
  {
    title: 'SYSTEM OS',
    items: [
      { href: '/pipeline', icon: Workflow, label: 'Pipeline' },
      { href: '/agents', icon: Bot, label: 'Agents' },
      { href: '/monitoring', icon: Activity, label: 'Monitoring' },
      { href: '/analytics', icon: BarChart2, label: 'Analytics' }
    ]
  },
  {
    title: 'CONFIGURATION',
    items: [
      { href: '/models', icon: Box, label: 'Models' },
      { href: '/knowledge', icon: BookOpen, label: 'Knowledge' },
      { href: '/mcp', icon: Cpu, label: 'MCP Servers' },
      { href: '/settings', icon: Settings, label: 'Settings' }
    ]
  }
]

