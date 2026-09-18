# GeoChat 平台桥接

GeoChat 以独立的上游源码目录保留在 `services/yuxi`，由根级平台启动器统一编排。浏览器只使用平台入口 `http://localhost:8080`：门户保留在根路径，GeoChat 工作台通过同域 `/geochat/` 转发。门户的 `/assistant` 路由将问题、模式和返回地址传给 `/geochat/agent`，不会复制工作台或聊天协议。

## 启动与管理

1. 使用一条命令启动全部平台服务。首次运行会自动从 `.env.example` 生成本地 `.env`；生产部署前应替换其中的默认密码。

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-platform.ps1 -Build
```

2. 打开 `http://localhost:8080`。提交问题后会进入同域 GeoChat 工作台；未登录时，GeoChat 原生认证流程接管并在成功后恢复预填问题。

启动命令会等待门户 API、GeoChat API、门户网页和同源工作台网关全部就绪。停止服务使用 `powershell -ExecutionPolicy Bypass -File scripts/start-platform.ps1 -Down`；重启使用 `-Restart`，查看状态使用 `-Status`，查看两组最近日志使用 `-Logs`，单独执行健康检查使用 `-Health`。调试 API 可访问 `http://127.0.0.1:5050/api/system/ready`，但日常使用不需要访问独立端口。

## 验证

- GeoChat 前端：`cd services/yuxi/web; pnpm install --frozen-lockfile; pnpm run test:unit; pnpm run build`。
- GeoChat 后端在 Linux 容器中测试：`docker compose --project-directory services/yuxi exec api uv run --group test pytest test/unit -m "not slow"`。
- 门户：`cd apps/web; npm run build`。
- 手工访问 `/assistant?q=油气成藏条件&mode=conversation`，确认跳转为同域 `/geochat/agent`、登录后输入框预填问题、工作台的返回链接回到门户。
