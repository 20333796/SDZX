import { fileURLToPath, URL } from 'node:url'
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

  return {
    plugins: [vue()],
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
      proxy: {
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
    }
  }
})
