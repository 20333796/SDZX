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

门户课程、仿真资源、地学数据和演示学习任务由版本库内的种子代码自动写入 PostgreSQL；全校导师公开资料保存在 `apps/web/src/config/mentorDirections.json`。这些内容就是可公开、可重复恢复的数据库基线，不需要提交本机数据库二进制文件。

GeoChat 首次部署后，先在工作台完成管理员初始化，再执行一次知识库导入。默认首个管理员的用户 ID 为 `1`；如果实际 ID 不同，在根目录 `.env` 中设置 `GEOCHAT_IMPORT_USER_ID`：

```powershell
docker compose --project-name deep-geology --project-directory . -f infra/compose/docker-compose.yml --profile tools run --rm --build knowledge-import
```

导入器读取 `services/yuxi/.env` 中部署时生成的 JWT 配置，从门户 API 汇总当前课程和仿真资源，并将导师、课程和官网链接写入 GeoChat 知识库。运行前必须启用 GeoChat 的 `knowledge` profile，并配置可用的 embedding 模型；提交成功后在任务中心确认“知识库文档处理”完成。重复执行会复用同名知识库并跳过已经存在的同名知识文档。

运行数据由多种存储共同组成：门户 PostgreSQL 与 MinIO 使用 Compose 命名卷，GeoChat 的 PostgreSQL、Milvus、MinIO、Neo4j 和工作区位于 `services/yuxi/docker/volumes/`。这些原始文件包含账号、密码散列、会话、令牌、用户上传文件和机器相关状态，禁止提交到 Git。

升级前先停止写入，并分别备份关系数据库和 GeoChat 状态目录：

```powershell
New-Item -ItemType Directory -Force .\backups | Out-Null
docker exec geochat-runtime-postgres-1 pg_dump -U postgres -d yuxi -Fc -f /tmp/yuxi.dump
docker cp geochat-runtime-postgres-1:/tmp/yuxi.dump .\backups\yuxi.dump
docker compose --project-name deep-geology -f infra/compose/docker-compose.yml exec postgres pg_dump -U geology_ai -d geology_ai -Fc -f /tmp/portal.dump
docker compose --project-name deep-geology -f infra/compose/docker-compose.yml cp postgres:/tmp/portal.dump .\backups\portal.dump
```

随后备份 `services/yuxi/docker/volumes/` 和门户 MinIO 命名卷。备份文件只应进入受控备份存储，不应提交到公开 GitHub。停止服务不要使用 `docker compose down -v`；Docker Desktop 的磁盘镜像建议放在数据盘。

## 健康检查与升级

启动后运行 `scripts/start-platform.ps1 -Health`，并确认门户、GeoChat API 和工作台均可访问。升级时先完成上述备份，再执行 `git pull --ff-only` 和 `scripts/start-platform.ps1 -Build`。Alembic 与 GeoChat storage-migrator 会在服务启动阶段应用结构迁移，不要手工修改已经应用的迁移文件。

## 故障处理

先运行 `-Status` 和 `-Health`，再用 `-Logs` 定位服务。端口被占用时释放 8080、8000、5050、9100、9101。镜像拉取超时可切换 `-ImageRegistryMirror`。登录出现“服务不可用”时检查 GeoChat API readiness；出现“账号或密码错误”时检查认证数据，不要反复重建数据库。
