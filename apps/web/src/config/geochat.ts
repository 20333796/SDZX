const configuredUrl = String(import.meta.env.VITE_GEOCHAT_WEB_URL ?? '').trim()

export function getGeoChatUrl() {
  return (configuredUrl || `${window.location.origin}/geochat`).replace(/\/+$/, '')
}

export function buildGeoChatWorkbenchUrl(question = '') {
  // 真实 GeoChat 智能体工作台：yuxi 应用以 /geochat/ 为 base path，工作台路由是 /agent，
  // 即 /geochat/agent（dev/preview 由 vite 代理转发，生产由 nginx 把 /geochat 指向 geochat 容器）。
  const url = new URL('agent', new URL(`${getGeoChatUrl()}/`, window.location.origin))
  if (question.trim()) url.searchParams.set('portal_question', question.trim())
  return url.toString()
}

export function buildGeoChatLoginUrl(returnPath = '/platform/') {
  const portalReturn = new URL(returnPath, window.location.origin)
  const url = new URL('login', `${getGeoChatUrl()}/`)
  // Never send the portal's former assistant route as the post-login destination. That route is
  // only a compatibility bridge now; GeoChat's own login should land in its working interface.
  if (!portalReturn.pathname.startsWith('/platform/assistant') && !portalReturn.pathname.startsWith('/platform/geochat')) {
    url.searchParams.set('portal_return', portalReturn.toString())
  }
  return url.toString()
}

export function buildGeoChatRegistrationUrl(returnPath = '/platform/') {
  const portalReturn = new URL(returnPath, window.location.origin)
  const url = new URL('login', `${getGeoChatUrl()}/`)
  url.searchParams.set('mode', 'register')
  if (!portalReturn.pathname.startsWith('/platform/assistant') && !portalReturn.pathname.startsWith('/platform/geochat')) {
    url.searchParams.set('portal_return', portalReturn.toString())
  }
  return url.toString()
}
