# 深地智学部署指南

本文描述门户、GeoChat、数据库、缓存和对象存储的一体化 Docker 部署方式。服务器只需要 Docker Engine（或 Docker Desktop）和 Docker Compose，不需要单独安装 Node.js、Python 或启动 Vite/uvicorn。生产环境应把示例密码替换为随机值，并使用学校批准的镜像仓库和统一认证配置。

## 环境要求

- 服务器：Linux Docker Engine + Docker Compose v2；Windows：Docker Desktop + Docker Compose v2。Docker 数据目录可放在指定数据盘。
- Git、PowerShell 5.1+ 仅用于执行仓库脚本；服务器不需要 Python 或 Node.js。
- 至少 8 GB 可用内存。启用知识图谱和向量服务前应准备更多资源。

## 配置

```powershell
Copy-Item .env.example .env
notepad .env
```

必须修改 `POSTGRES_PASSWORD` 和 `MINIO_ROOT_PASSWORD`。首次执行统一启动脚本时，会自动从 `services/yuxi/.env.template` 创建 GeoChat 配置并生成本地安全密钥，不需要手工运行初始化脚本。`OLLAMA_BASE_URL`、`OLLAMA_MODEL` 用于局域网 Ollama；留空时不会启用模型调用。SiliconFlow 仅保留为空的兼容配置，不是必需项。OIDC 参数配置完成后，上传、收藏、测评和后台功能才会接入学校统一登录。`.env`、`services/yuxi/.env` 和任何密钥不得提交。

## 统一启动与运维

其他人从仓库下载后，复制根目录 `.env.example` 并填写两个本地密码，即可由同一个脚本完成构建、配置和启动：

```powershell
.\scripts\start-platform.ps1 -Build       # 构建并启动
.\scripts\start-platform.ps1 -Deploy      # 使用现有镜像重建并启动
.\scripts\start-platform.ps1 -Health      # 检查四个入口
.\scripts\start-platform.ps1 -Status      # 查看两个 Compose 项目
.\scripts\start-platform.ps1 -Logs        # 查看门户和 GeoChat 日志
.\scripts\start-platform.ps1 -Down        # 停止容器，保留数据卷
```

默认使用 `docker.m.daocloud.io` 镜像前缀；可传 `-ImageRegistryMirror ''` 使用 Docker Hub，或传入学校批准的镜像地址。核心入口为门户 `http://localhost:8080/`、GeoChat `http://localhost:8080/geochat/agent`、门户 API `http://localhost:8000/docs`。

Linux 服务器可直接执行同一套 Compose 配置：

```bash
docker compose --project-name geochat-runtime --project-directory services/yuxi up -d --build
docker compose --project-name deep-geology -f infra/compose/docker-compose.yml up -d --build
```

两套 Compose 都由同一份发布代码和同一套配置管理；服务器不要再单独运行 `npm run dev`、`uvicorn` 或 GeoChat 开发服务器。

更推荐使用仓库内的 Linux 统一脚本，它会检查 Docker daemon、创建 GeoChat 配置和生成安全密钥：

```bash
bash scripts/start-platform.sh
```

## 数据与备份

Compose 命名卷保存 PostgreSQL 和 MinIO 数据，GeoChat 的持久化目录位于 `services/yuxi/docker/volumes/`。停止服务不要使用 `docker compose down -v`。迁移或升级前导出 PostgreSQL，并备份该目录；Docker Desktop 的磁盘镜像也应位于 D 盘。

## 故障处理

先运行 `-Status` 和 `-Health`，再用 `-Logs` 定位服务。端口被占用时释放 8080、8000、5050、9100、9101。镜像拉取超时可切换 `-ImageRegistryMirror`。登录出现“服务不可用”时检查 GeoChat API readiness；出现“账号或密码错误”时检查认证数据，不要反复重建数据库。
