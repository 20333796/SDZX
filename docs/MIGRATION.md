# 数据迁移指南

## 门户数据库

门户 API 容器启动时自动执行 Alembic：

```powershell
docker compose --project-name deep-geology --project-directory . -f infra/compose/docker-compose.yml run --rm api alembic upgrade head
```

生产迁移前先备份数据库，并在维护窗口执行。迁移状态可在 API 容器中查看：

```powershell
docker compose --project-name deep-geology -f infra/compose/docker-compose.yml exec api alembic current
```

## GeoChat 业务数据库

GeoChat 的 `storage-migrator` 在统一启动时自动运行。当前业务 schema 从 v7 升级到 v8，新增 `users.account_type`，默认值为 `student`；历史用户不会丢失，教师注册写入 `teacher`，但系统权限仍由独立 `role` 字段控制。知识 schema 当前为 v2。

查看迁移日志：

```powershell
docker compose --project-name geochat-runtime -f services/yuxi/docker-compose.yml logs storage-migrator
```

迁移失败时，容器不会记录新的版本号。保留原数据卷，修复配置后重新执行 `-Deploy`；不要删除 `services/yuxi/docker/volumes/`。

## 发布后验证

```powershell
.\scripts\start-platform.ps1 -Health -TimeoutSeconds 180
```

随后验证注册的学生/教师类型、用户名/手机号登录、重复注册提示、匿名首页和 GeoChat 网关。升级后运行 API 单元测试和前端构建，再开放外部访问。
