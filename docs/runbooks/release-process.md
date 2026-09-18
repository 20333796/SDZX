# 发布过程

## 分支与审查

在 GitLab 创建 `main` 保护分支：禁止直接推送，要求至少一名代码所有者批准，并要求所有流水线任务通过。功能开发从短期分支发起合并请求；数据库迁移、身份权限、外部资源与部署配置必须由相应模块负责人复核。

## 流水线门禁

`.gitlab-ci.yml` 执行前端类型检查与构建、API 迁移与测试、Python 依赖审计、Node 高危依赖审计和 CycloneDX SBOM 生成。镜像任务只在项目容器仓库可用时运行，使用提交 SHA 作为不可变标签。

## 环境推进

开发环境使用 Docker Compose。预发布环境先运行 Helm 迁移 Hook，验证 OIDC、资源外链、文档上传和 Worker 解析，再由课程负责人抽样确认答案引用。生产发布使用相同镜像 SHA 和 Helm values；先确认 PostgreSQL 备份、MinIO 版本控制、Redis 健康和回滚镜像可用。发布前运行 `python scripts/check_external_resources.py`，报告写入 `output/external-resource-health.json`；待补链和需平台授权的资源保留状态，违规域名或不可达的已发布资源会使命令失败。部署后检查 Ingress 的 `/api` 路径指向当前 Release 的 API Service，并从公开域名请求 `/healthz`、`/readyz` 与 `/api/v1/portal-config`。

## 回滚

应用问题使用 `helm rollback` 回到上一个成功 Revision。数据库迁移采用向前兼容策略；不得在未演练恢复的情况下回滚生产数据。课程资料仅在审核状态变化后发布，错误资料通过新版本或拒绝状态处理，不删除审计记录。
