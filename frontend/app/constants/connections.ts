import type { Connection } from '~/types/connection'

export const CONNECTION_CATEGORIES = [
  'All',
  'Active',
  'Recommended',
  'Data',
  'Docs',
  'Communication',
  'Dev Tools'
] as const

export const INITIAL_CONNECTIONS: Connection[] = [
  {
    id: 'slack',
    name: 'Slack',
    category: 'Communication',
    description: 'Team communication and notifications',
    longDescription: 'Keep your team in the loop and let agents take action in Slack.',
    status: 'connected',
    recommended: true,
    lastSync: '2 minutes ago',
    permissions: 'Read channels, send messages',
    dataTypes: 'Messages, users, channels',
    connectedBy: 'Alex Chen',
    connectedOn: 'Apr 14, 2025',
    workspace: 'NagareOS',
    accessType: 'OAuth 2.0',
    syncHistory: [
      { id: '1', title: 'Synced 128 messages', time: '2 minutes ago' },
      { id: '2', title: 'Synced 42 users', time: '15 minutes ago' },
      { id: '3', title: 'Synced 18 channels', time: '1 hour ago' },
      { id: '4', title: 'Synced 320 messages', time: 'Apr 27, 6:12 PM' },
      { id: '5', title: 'Synced 12 files', time: 'Apr 26, 3:51 PM' }
    ],
    capabilities: [
      { id: 'c1', title: 'Read messages', description: 'Access channel messages and threads', enabled: true, icon: 'target' },
      { id: 'c2', title: 'Send messages', description: 'Post notifications and responses', enabled: true, icon: 'send' },
      { id: 'c3', title: 'Read users', description: 'Access team member information', enabled: true, icon: 'user' },
      { id: 'c4', title: 'Read channels', description: 'List and view channel details', enabled: true, icon: 'grid' },
      { id: 'c5', title: 'Access files', description: 'View shared files and links', enabled: true, icon: 'file' }
    ]
  },
  {
    id: 'notion',
    name: 'Notion',
    category: 'Docs',
    description: 'Docs, wikis and knowledge bases',
    longDescription: 'Connect Notion workspaces to read, create, and organize team documentation.',
    status: 'connected',
    recommended: true,
    lastSync: '12 minutes ago',
    permissions: 'Read pages, create pages',
    dataTypes: 'Pages, databases, comments',
    connectedBy: 'Alex Chen',
    connectedOn: 'Apr 12, 2025',
    workspace: 'NagareOS',
    accessType: 'OAuth 2.0',
    syncHistory: [
      { id: '1', title: 'Synced 54 pages', time: '12 minutes ago' },
      { id: '2', title: 'Synced 8 databases', time: '1 hour ago' },
      { id: '3', title: 'Synced 190 blocks', time: 'Apr 27, 4:20 PM' }
    ],
    capabilities: [
      { id: 'c1', title: 'Read pages', description: 'Access workspace documents and wikis', enabled: true, icon: 'file' },
      { id: 'c2', title: 'Create pages', description: 'Generate and publish new documentation', enabled: true, icon: 'send' },
      { id: 'c3', title: 'Query databases', description: 'Read and filter Notion database rows', enabled: true, icon: 'grid' }
    ]
  },
  {
    id: 'googledrive',
    name: 'Google Drive',
    category: 'Docs',
    description: 'Files and document storage',
    longDescription: 'Access shared Google Drive files, spreadsheets, and presentations.',
    status: 'connected',
    recommended: true,
    lastSync: '1 hour ago',
    permissions: 'Read files, manage metadata',
    dataTypes: 'Files, folders, permissions',
    connectedBy: 'Alex Chen',
    connectedOn: 'Apr 10, 2025',
    workspace: 'NagareOS',
    accessType: 'OAuth 2.0',
    syncHistory: [
      { id: '1', title: 'Synced 86 documents', time: '1 hour ago' },
      { id: '2', title: 'Synced 14 shared folders', time: '6 hours ago' }
    ],
    capabilities: [
      { id: 'c1', title: 'Read documents', description: 'Index and extract document text', enabled: true, icon: 'file' },
      { id: 'c2', title: 'Manage files', description: 'Organize folders and metadata', enabled: true, icon: 'grid' }
    ]
  },
  {
    id: 'jira',
    name: 'Jira',
    category: 'Dev Tools',
    description: 'Issue tracking and project management',
    longDescription: 'Track engineering tasks, sprints, and project tickets across Jira boards.',
    status: 'connected',
    lastSync: '3 hours ago',
    permissions: 'Read issues, comments',
    dataTypes: 'Issues, projects, users',
    connectedBy: 'Alex Chen',
    connectedOn: 'Apr 08, 2025',
    workspace: 'NagareOS',
    accessType: 'OAuth 2.0',
    syncHistory: [
      { id: '1', title: 'Synced 64 issues', time: '3 hours ago' },
      { id: '2', title: 'Synced 12 active sprints', time: '12 hours ago' }
    ],
    capabilities: [
      { id: 'c1', title: 'Read issues', description: 'Fetch ticket status and descriptions', enabled: true, icon: 'target' },
      { id: 'c2', title: 'Create comments', description: 'Post updates directly to tickets', enabled: true, icon: 'send' }
    ]
  },
  {
    id: 'github',
    name: 'GitHub',
    category: 'Dev Tools',
    description: 'Code repositories and development',
    longDescription: 'Access source repositories, pull requests, commits, and code discussions.',
    status: 'connected',
    recommended: true,
    lastSync: '5 hours ago',
    permissions: 'Read repos, issues, pull requests',
    dataTypes: 'Repos, issues, PRs, commits',
    connectedBy: 'Alex Chen',
    connectedOn: 'Apr 05, 2025',
    workspace: 'NagareOS',
    accessType: 'Personal Access Token',
    syncHistory: [
      { id: '1', title: 'Synced 32 pull requests', time: '5 hours ago' },
      { id: '2', title: 'Synced 18 repositories', time: '1 day ago' }
    ],
    capabilities: [
      { id: 'c1', title: 'Read repositories', description: 'Inspect branch trees and code files', enabled: true, icon: 'file' },
      { id: 'c2', title: 'Inspect PRs', description: 'Review diffs and discussions', enabled: true, icon: 'grid' }
    ]
  },
  {
    id: 'linear',
    name: 'Linear',
    category: 'Dev Tools',
    description: 'Modern issue tracking for product teams',
    longDescription: 'Modern issue tracking built for high-performing product engineering teams.',
    status: 'available',
    lastSync: '—',
    permissions: 'Read issues, create issues',
    dataTypes: 'Issues, cycles, teams',
    syncHistory: [],
    capabilities: [
      { id: 'c1', title: 'Read issues', description: 'View assigned issues and team roadmaps', enabled: false, icon: 'target' },
      { id: 'c2', title: 'Update cycles', description: 'Track sprint cycles and projects', enabled: false, icon: 'grid' }
    ]
  },
  {
    id: 'figma',
    name: 'Figma',
    category: 'Dev Tools',
    description: 'Design files and collaboration',
    longDescription: 'Inspect design systems, component specs, and collaborate on design files.',
    status: 'available',
    lastSync: '—',
    permissions: 'Read files, comments',
    dataTypes: 'Files, designs, comments',
    syncHistory: [],
    capabilities: [
      { id: 'c1', title: 'Inspect files', description: 'Read frames and component libraries', enabled: false, icon: 'file' },
      { id: 'c2', title: 'Read comments', description: 'Follow design feedback threads', enabled: false, icon: 'target' }
    ]
  },
  {
    id: 'hubspot',
    name: 'HubSpot',
    category: 'Communication',
    description: 'CRM and marketing automation',
    longDescription: 'Manage customer contacts, leads, deals, and automated email workflows.',
    status: 'available',
    lastSync: '—',
    permissions: 'Read contacts, companies',
    dataTypes: 'Contacts, companies, deals',
    syncHistory: [],
    capabilities: [
      { id: 'c1', title: 'Read contacts', description: 'Access CRM contact records and companies', enabled: false, icon: 'user' },
      { id: 'c2', title: 'Read deals', description: 'View pipeline status and stage progression', enabled: false, icon: 'grid' }
    ]
  },
  {
    id: 'postgresql',
    name: 'PostgreSQL',
    category: 'Data',
    description: 'Relational database connection',
    longDescription: 'Direct connection to PostgreSQL databases for schemas, tables, and queries.',
    status: 'available',
    lastSync: '—',
    permissions: 'Read data (select)',
    dataTypes: 'Tables, views, custom queries',
    syncHistory: [],
    capabilities: [
      { id: 'c1', title: 'Query tables', description: 'Execute read-only SQL queries on tables', enabled: false, icon: 'grid' },
      { id: 'c2', title: 'Inspect schema', description: 'Extract table columns and relationships', enabled: false, icon: 'file' }
    ]
  }
]
