export type ResourceCategory = 'courses' | 'knowledge' | 'practice'
export type ResourceStatus = 'active' | 'pending'

export interface ExternalResource {
  id: string
  title: string
  provider: string
  category: ResourceCategory
  course_level: string
  audience: string
  credits?: number | null
  language: string
  status: ResourceStatus
  url?: string | null
  cover_asset?: string | null
  description: string
  sort_order: number
}

export interface Citation {
  document_id: string
  title: string
  course_name?: string | null
  source_locator?: string | null
  excerpt: string
  score: number
}

export interface ChatResourceReference {
  id: string
  title: string
  category: 'courses' | 'practice' | 'mentor'
  provider?: string | null
  description: string
  url?: string | null
  embedded_url?: string | null
  route?: string | null
}

export interface PortalNavigationLink {
  label: string
  target: string
  category?: ResourceCategory | null
}

export interface PortalNavigationGroup {
  title: string
  links: PortalNavigationLink[]
}

export interface PortalStat {
  value: string
  label: string
}

export interface PortalConfig {
  navigation: PortalNavigationGroup[]
  stats: PortalStat[]
}

export interface LearningTask {
  id: string
  title: string
  summary: string
  course_name: string
  objective: string
  instructions: string[]
  estimated_minutes: number
  difficulty: string
  status: 'draft' | 'published'
  sort_order: number
}
