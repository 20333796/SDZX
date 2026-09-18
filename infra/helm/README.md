# Kubernetes 部署入口

`deep-geology/` 是生产部署 Chart，部署双副本 `web`、双副本 `api`、独立 Worker、数据库迁移 Hook Job、Service、Ingress 和 API HPA。每个 Service 都以 Helm Release 名称命名，避免同一命名空间中的不同部署互相冲突。PostgreSQL/pgvector、Redis 和 MinIO 使用校内高可用服务；Chart 不创建含示例密码的有状态服务。

发布前创建 `deep-geology-runtime` Secret，其中包含 `DATABASE_URL`、`REDIS_URL`、对象存储配置和 OIDC 配置。配置镜像仓库、域名和 TLS 后执行：

```powershell
helm lint infra/helm/deep-geology
helm upgrade --install deep-geology infra/helm/deep-geology --namespace deep-geology --create-namespace
```

先在预发布环境运行迁移并验证回滚。Ingress 会将 `/api` 路由到当前 Release 的 API Service，其他路径路由到前端 Service；浏览器继续通过相对路径访问 API。Worker 已部署为独立工作负载，GPU 模型服务、NetworkPolicy 和集群级可观测性资源仍由校内平台提供。禁止将 `.env`、OIDC 密钥、数据库密码或对象存储凭据提交到仓库。
