const configuredUrl = String(import.meta.env.VITE_GEOCHAT_WEB_URL ?? '').trim()

export function getGeoChatUrl() {
  return (configuredUrl || `${window.location.origin}/geochat`).replace(/\/+$/, '')
}

export function buildGeoChatAgentUrl(question = '', mode = 'conversation') {
  // 保留对外约定的 GeoChat 地址，但由门户路由承载新版智能问答。
  // 登录仍使用 getGeoChatUrl()，避免把认证请求混入问答页面。
  const url = new URL('/platform/geochat/agent', window.location.origin)
  if (question.trim()) url.searchParams.set('q', question.trim())
  if (mode.trim()) url.searchParams.set('mode', mode.trim())
  return url.toString()
}

export function buildGeoChatWorkbenchUrl() {
  // 真实 GeoChat 智能体工作台：yuxi 应用以 /geochat/ 为 base path，工作台路由是 /agent，
  // 即 /geochat/agent（dev/preview 由 vite 代理转发，生产由 nginx 把 /geochat 指向 geochat 容器）。
  // 首页“AI应用中心”入口跳这里；buildGeoChatAgentUrl 的 /platform/geochat/agent 是门户内置
  // 的轻量问答页，两者是不同的页面，不要混用。
  return `${getGeoChatUrl()}/agent`
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
