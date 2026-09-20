import { fileURLToPath, URL } from 'node:url'
import { readFileSync } from 'node:fs'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  // loadEnv so .env.local actually feeds the proxy targets: plain `process.env` never saw
  // dotenv files, so a dev server launched without shell exports silently fell back to the
  // old default — which pointed at THIS server (5173), self-looping every /geochat request
  // back into the SPA fallback: the sign-in URL rendered the portal homepage, and
  // /login-bg.jpg looped until Vite killed it with a 500.
  const env = loadEnv(mode, process.cwd(), '')
  const apiProxyTarget = env.VITE_API_PROXY_TARGET ?? 'http://localhost:8000'
  // yuxi (geochat) web dev server. Standard startup:
  //   cd services/yuxi/web && npm run dev -- --port 5177 --strictPort
  // Do NOT point this at 5173: that port belongs to the geochat web container when the compose
  // stack is up, and pointing a vite dev server at itself (the old default) self-loops /geochat.
  const geoChatProxyTarget = env.VITE_GEOCHAT_PROXY_TARGET ?? 'http://127.0.0.1:5177'

  // 站点根 `/` 与 `/landing/` 都应呈现桌面“郭网页”静态首页（public/landing/index.html）。
  // 但 Vite 的 SPA history fallback 会把目录请求 `/landing/` 改写成根 index.html（即平台本身），
  // 导致落地页永远上不来。这里在中间件栈最前插入一个只认 `/landing` 与 `/landing/` 的处理器，
  // 直接吐出静态落地页；其余路径放行给 Vite 默认逻辑。不碰 base，public 资源（/cupb-logo.png 等）路径不受影响。
  const landingHtml = readFileSync(new URL('./public/landing/index.html', import.meta.url), 'utf-8')
  const serveLanding = (req, res, next) => {
    if (req.url === '/landing' || req.url === '/landing/') {
      res.statusCode = 200
      res.setHeader('Content-Type', 'text/html; charset=utf-8')
      res.end(landingHtml)
      return
    }
    next()
  }

  // 站点根 `/` 落地页（public/landing，即桌面“郭网页”静态首页）与平台（/platform/）的跳转
  // 在前端路由里用 location.replace 处理：根路径整页换到落地页，避免与 Vite 的 base 重定向排序打架。
  // 这里保持默认 base（'/'），public 资源（/cupb-logo.png、/images/...）路径不受影响。
  // dev 与 preview 共用同一套代理：首页“AI应用中心”整页跳 /geochat/agent（真实 GeoChat
  // 智能体工作台），preview 若不代理 /geochat，请求会落进 SPA fallback 被送回平台首页。
  const sharedProxy = {
    /* The geochat app runs with VITE_BASE_PATH=/geochat/ (same as its compose build), so the
       prefix must be PRESERVED end-to-end: page, assets and /geochat/api all resolve inside
       yuxi itself. Stripping the prefix here (the old rewrite) left the browser URL at
       /geochat/login while the app routed on / — the router's catch-all swallowed the path
       and the sign-in URL rendered the geochat home instead of the form. */
    '/geochat': {
      target: geoChatProxyTarget,
      changeOrigin: true,
      ws: true
    },
    /* Legacy passthrough: an organization.login_bg set to a root-absolute /login-bg.jpg in
       the DB escapes the /geochat prefix. Only needed while that setting is actually used. */
    '/login-bg.jpg': { target: geoChatProxyTarget, changeOrigin: true },
    '/api': apiProxyTarget
  }

  return {
    plugins: [
      vue(),
      {
        // 把 `/landing` 与 `/landing/` 直接吐出静态落地页（public/landing/index.html）。
        // 必须作为插件钩子注册：configureServer 不是合法的顶层配置项，写成顶层键会被 Vite 直接忽略。
        name: 'serve-landing',
        configureServer(server) {
          server.middlewares.use(serveLanding)
        },
        configurePreviewServer(server) {
          server.middlewares.use(serveLanding)
        }
      }
    ],
    /* 本环境的文件删除有批量安全守卫：Vite 运行中发现新依赖会重建 deps_temp（>50 个文件）并
       尝试 rm，守卫直接抛错杀死 dev server（曾因 ol/Overlay 被动态发现而崩）。把已知条目
       预先列在这里可避免运行中再优化；新增 import 后若 dev server 意外退出，优先想到这里。 */
    optimizeDeps: {
      include: ['ol/Overlay']
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      /* 每次重建 dist 都会把旧包 mv 成 dist-prevN-<日期> 留作备份，累积到十几个目录后
         Vite 的文件监听会一直扫这些构建产物：改一次 styles.css 就触发 "page reload
         dist-prevXX/index.html"，白白重载页面、还白耗 CPU。这里把构建产物目录全部排除。 */
      watch: {
        ignored: ['**/dist/**', '**/dist-*/**', '**/node_modules/**', '**/.git/**']
      },
      proxy: sharedProxy
    },
    preview: {
      proxy: sharedProxy
    }
  }
})
