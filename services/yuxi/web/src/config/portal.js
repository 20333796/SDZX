const configuredPortalUrl = String(import.meta.env.VITE_PORTAL_URL || '').trim()

export const portalUrl = (configuredPortalUrl || window.location.origin).replace(/\/+$/, '')

export function portalLink(path = '/') {
  const suffix = path.startsWith('/') ? path : `/${path}`
  return `${portalUrl}${suffix}`
}
