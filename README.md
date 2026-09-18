# 深地智学

中国石油大学（北京）地质学科教育大模型平台。正式运行统一使用 Docker Compose 管理门户、GeoChat、API、Worker、PostgreSQL、Redis 和 MinIO。

平台面向地质学、石油地质、地球物理和测井教学，提供统一的学科资源入口与智能学习工作台。首页支持匿名进入问答入口；需要保存历史、上传资料、测评或管理资源时，再通过统一身份认证登录。

## 主要功能

- **学科门户**：地学问答入口、课程与外部资源目录、知识图谱、地学数据目录。
- **智能教学**：学情诊断、研学任务、课程推荐、教师反馈和成长记录。
- **实践教学**：测井 LAS/CSV 教学案例、曲线可视化、规则判识、工程案例和虚拟仿真入口。
- **GeoChat 工作台**：对话、知识库检索、文档引用、任务执行和工作区管理。
- **统一认证**：支持用户名、UID、手机号登录；注册时可选择学生或教师身份，系统权限由 RBAC 独立控制。

复杂三维仿真、导师图谱算法和生产级地震处理保留前端入口与 API 契约，按建设阶段接入真实服务，不伪装为已交付算法。

## 技术路线

门户前端采用 Vue 3、TypeScript、Vite、Pinia、Vue Router 和 ECharts；门户 API 采用 FastAPI、Pydantic、SQLAlchemy 和 Alembic；GeoChat 使用独立的前后端工作台和异步 Worker。知识服务按“文档上传—解析—审核—切分—向量化—检索—引用回答”链路运行，模型默认适配局域网 Ollama。

运行时使用 Nginx 统一入口，PostgreSQL 保存业务数据，pgvector 支持向量检索，Redis 用于缓存和任务队列，MinIO 保存文档与附件。生产环境可在此基础上接入 OIDC、Kubernetes、Prometheus、Grafana 和日志系统。

## 架构与目录

```text
apps/web       门户前端（Vue 3 + Vite）
apps/api       门户 API（FastAPI + Alembic）
apps/worker    门户资料解析 Worker
services/yuxi  GeoChat 前端、API、Worker 与运行时服务
infra/compose  门户 Compose 配置
scripts        Windows/Linux 统一启动脚本
docs           部署、迁移、架构和运维文档
```

## 快速部署

### Windows

安装 Docker Desktop、Git 和 PowerShell，并确认 Docker Desktop 已显示 Running。

```powershell
git clone https://github.com/20333796/SDZX.git
cd SDZX
Copy-Item .env.example .env
notepad .env
powershell -ExecutionPolicy Bypass -File scripts/start-platform.ps1 -Build
```

### Linux 服务器

安装 Docker Engine、Docker Compose v2、Git 和 OpenSSL。

```bash
git clone https://github.com/20333796/SDZX.git
cd SDZX
cp .env.example .env
$EDITOR .env
bash scripts/start-platform.sh
```

`.env` 至少需要设置 `POSTGRES_PASSWORD` 和 `MINIO_ROOT_PASSWORD`。首次启动会自动创建 GeoChat 配置并生成安全密钥，不需要安装 Node.js、Python、npm 或单独启动 uvicorn。

## 服务入口

| 服务 | 地址 |
| --- | --- |
| 深地智学门户 | `http://localhost:8080/` |
| GeoChat 工作台 | `http://localhost:8080/geochat/agent` |
| 门户 API 文档 | `http://localhost:8000/docs` |
| 门户 MinIO 控制台 | `http://localhost:9101` |

如需使用局域网 Ollama，在根目录 `.env` 设置 `OLLAMA_BASE_URL` 和 `OLLAMA_MODEL`。SiliconFlow 仅作为空的兼容配置保留，不是部署必需项。

## 运维命令

Windows 使用 `scripts/start-platform.ps1`：

```powershell
.\scripts\start-platform.ps1 -Health
.\scripts\start-platform.ps1 -Status
.\scripts\start-platform.ps1 -Logs
.\scripts\start-platform.ps1 -Deploy
.\scripts\start-platform.ps1 -Down
```

不要使用 `docker compose down -v`，否则会删除数据库和对象存储卷。生产升级前请备份 PostgreSQL 和 `services/yuxi/docker/volumes/`。

## 数据迁移与验证

门户 API 容器启动时自动执行 Alembic。GeoChat storage-migrator 当前执行业务 schema v7 → v8，新增 `users.account_type`，历史用户默认为学生身份。详见 [`docs/MIGRATION.md`](docs/MIGRATION.md) 和 [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)。

代码规范、测试命令和提交要求见 [`AGENTS.md`](AGENTS.md)。

## 安全说明

不要提交 `.env`、`services/yuxi/.env`、密钥、数据库文件、Docker 数据卷或构建产物。生产环境应替换示例密码、配置学校 OIDC，并通过受控镜像仓库发布镜像。
