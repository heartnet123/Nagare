import type { Component } from 'vue'

export interface NavItem {
  href: string
  icon: Component
  label: string
  badge?: string | number
  matchRoutes?: string[]
}

export interface NavGroup {
  title?: string
  items: NavItem[]
}
