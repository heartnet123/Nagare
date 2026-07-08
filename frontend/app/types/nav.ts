export interface NavItem {
  href: string
  icon: any
  label: string
}

export interface NavGroup {
  title: string
  items: NavItem[]
}
