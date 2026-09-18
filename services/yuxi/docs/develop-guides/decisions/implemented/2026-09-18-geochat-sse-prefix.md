# GeoChat SSE 前缀

状态：implemented
类型：bug-fix
Owner：web/src/apis/base.js、web/src/apis/agent_api.js、scripts/start-platform.ps1

## 问题

深地智学将 GeoChat 挂载在 `/geochat/` 下。普通 API 请求已使用挂载前缀，但请求队列与 Agent Run 的 SSE 请求绕过了该机制，向门户的 `/api/` 发起请求并得到 404。

## 决策

SSE 请求复用 `withApiBasePath`。独立部署继续请求 `/api/...`；挂载部署由构建时 `VITE_API_BASE_PATH=/geochat` 生成 `/geochat/api/...`，再由门户网关转发到 GeoChat API。统一启动脚本在传入 `-Build` 时强制重建服务容器，确保新镜像会成为实际运行版本。

## 替代方案

- 在门户网关截获所有 `/api/agent/` 请求：会使门户与 GeoChat 路由职责交叉。
- 为 SSE 单独拼接挂载路径：会复制既有 API 基路径规则。

## 后果

请求队列和运行事件流沿用与普通接口相同的部署路径。后端的 `/api/agent/...` 契约保持不变。
`-Build` 会替换正在运行的统一平台容器，适用于源代码或镜像变更后的发布。
`-Deploy` 复用已经构建完成的镜像并强制替换统一平台容器，适用于将已构建镜像激活到本机服务。

## 验证

在构建产物中确认两类 SSE URL 均带有 `/geochat` 前缀，并在统一 Docker 服务中完成真实对话的请求与流式响应检查。
