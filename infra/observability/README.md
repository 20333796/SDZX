# 可观测性

API 暴露内部 `/metrics` 端点，输出 Prometheus 格式的请求总数和请求耗时直方图。Helm API Pod 已包含抓取注解；校内 Prometheus 根据集群策略发现这些 Pod 或通过 ServiceMonitor 抓取。

Grafana 仪表板应至少覆盖 API 错误率、P95 请求耗时、匿名问答限流次数、Worker 解析失败和 PostgreSQL/Redis/MinIO 健康。Loki 收集容器标准输出，Sentry 在学校提供 DSN 后接入 API 与前端异常，不把资料正文、OIDC 令牌或测井文件内容发送到外部。

生产告警阈值由运维负责人在预发布压测后确定；发布前必须演练 API 回滚、数据库恢复和 MinIO 对象版本恢复。
