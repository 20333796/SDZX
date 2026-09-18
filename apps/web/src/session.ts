import { computed, ref } from 'vue'

// Who is looking at the platform. The header used to hard-code 访客, which read as an account menu that
// nobody could be behind: the homepage showed a user chip with a dropdown arrow while there was no way
// to become a user at all. The chip is the *signed-in* state; the signed-out state is the 登录/注册
// entry beside it. This module holds the one piece of state both headers read, so the homepage header
// and the column header cannot drift apart the way the two 访客 chips had already started to.
//
// The API already expects a real identity: apps/api/app/identity.py verifies an OIDC access token
// against the school's JWKS and resolves it to a principal with learner/teacher/admin roles, and
// `oidc_enabled` is false until the school issuer and audience are configured. The roles below are the
// same three values, so a token obtained from the school later maps onto this shape without a rewrite.
export type SessionRole = 'learner' | 'teacher' | 'admin'

export const ROLE_LABELS: Record<SessionRole, string> = {
  learner: '学生',
  teacher: '教师',
  admin: '管理员'
}

export interface SessionPrincipal {
  subject: string
  name: string
  roles: SessionRole[]
}

const GEOCHAT_TOKEN_KEY = 'user_token'
const LEGACY_PORTAL_SESSION_KEY = 'deepgeology.session'

const principal = ref<SessionPrincipal | null>(null)

const isAuthenticated = computed(() => principal.value !== null)
const displayName = computed(() => principal.value?.name ?? '')
const initial = computed(() => principal.value?.name.slice(0, 1) || '')
const roleLabel = computed(() => {
  const role = principal.value?.roles[0]
  return role ? ROLE_LABELS[role] : ''
})

function signIn(next: Omit<SessionPrincipal, 'roles'> & { roles?: SessionRole[] }) {
  principal.value = { subject: next.subject, name: next.name, roles: next.roles?.length ? next.roles : ['learner'] }
}

function signOut() {
  principal.value = null
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(GEOCHAT_TOKEN_KEY)
    window.localStorage.removeItem(LEGACY_PORTAL_SESSION_KEY)
  }
}

async function restoreGeoChatSession(): Promise<boolean> {
  if (typeof window === 'undefined' || principal.value) return Boolean(principal.value)
  const token = window.localStorage.getItem(GEOCHAT_TOKEN_KEY)
  if (!token) return false

  try {
    const response = await fetch('/geochat/api/auth/me', {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (!response.ok) return false
    const user = await response.json() as { uid?: unknown; username?: unknown; role?: unknown }
    if (typeof user.uid !== 'string' || !user.uid || typeof user.username !== 'string' || !user.username) return false
    signIn({
      subject: user.uid,
      name: user.username,
      roles: user.role === 'admin' || user.role === 'superadmin' ? ['admin'] : ['learner']
    })
    return true
  } catch {
    return false
  }
}

export const session = {
  principal,
  isAuthenticated,
  displayName,
  initial,
  roleLabel,
  signIn,
  signOut,
  restoreGeoChatSession
}
