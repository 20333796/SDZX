const configuredUrl = String(import.meta.env.VITE_GEOCHAT_WEB_URL ?? '').trim()

export function getGeoChatUrl() {
  return (configuredUrl || `${window.location.origin}/geochat`).replace(/\/+$/, '')
}

export function buildGeoChatAgentUrl(question = '', mode = 'conversation') {
  const url = new URL('agent', `${getGeoChatUrl()}/`)
  if (question.trim()) url.searchParams.set('portal_question', question.trim())
  if (mode.trim()) url.searchParams.set('portal_mode', mode.trim())
  url.searchParams.set('portal_return', window.location.origin)
  return url.toString()
}

export function buildGeoChatLoginUrl(returnPath = '/') {
  const portalReturn = new URL(returnPath, window.location.origin)
  const url = new URL('login', `${getGeoChatUrl()}/`)
  url.searchParams.set('portal_return', portalReturn.toString())
  return url.toString()
}

export function buildGeoChatRegistrationUrl(returnPath = '/') {
  const portalReturn = new URL(returnPath, window.location.origin)
  const url = new URL('login', `${getGeoChatUrl()}/`)
  url.searchParams.set('mode', 'register')
  url.searchParams.set('portal_return', portalReturn.toString())
  return url.toString()
}
