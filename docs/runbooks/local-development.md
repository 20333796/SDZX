# 本地开发与发布

## 本地开发

前端在 `apps/web` 运行 `npm install` 与 `npm run dev`；API 在 `apps/api` 使用 Python 3.12 运行 `uvicorn app.main:app --reload`。首次启动 API 前执行 `python -m alembic upgrade head`。完整依赖服务通过仓库根目录执行：

```powershell
Copy-Item .env.example .env
docker compose -f infra/compose/docker-compose.yml up --build
```

启动后检查 `http://localhost:8000/healthz` 与 `http://localhost:8000/readyz`，再访问 `http://localhost:8080`。`/healthz` 用于进程存活探针，`/readyz` 会确认数据库连接可用；Compose 与 Kubernetes 仅在就绪检查通过后将流量转给 API。Compose 启动 API 前会自动执行数据库迁移。首次部署必须替换 `.env` 中的数据库和 MinIO 默认密码。

## 身份与资料入库

匿名用户只能浏览资源并提交文本问答，问答按来源 IP 由 Redis 固定窗口限流。收藏、历史记录、资料上传、测井文件处理、能力测评和后台管理必须由校内 OIDC 访问令牌授权。部署前由学校统一认证团队提供 `OIDC_ISSUER`、`OIDC_AUDIENCE`、`OIDC_JWKS_URL` 及角色声明名称；教师和管理员角色才可调用资料上传、状态审核和资源维护接口。

课程资料按 `uploaded -> parsed -> reviewed -> indexed -> published` 进入知识库。文件实际写入 MinIO 的 `knowledge-documents` 存储桶，数据库只保存元数据、哈希、版本和审核痕迹。解析、向量化和 LlamaIndex 检索适配器在下一阶段接入，未发布资料不得进入问答引用范围。

设置 `OLLAMA_BASE_URL` 和 `OLLAMA_MODEL` 后，匿名问答会把已发布课程片段作为上下文调用校内 Ollama；模型不可用或未配置时，服务返回带来源的检索式学习引导。设置 `EMBEDDING_BASE_URL` 和 `EMBEDDING_MODEL` 后，Worker 会把教师审核资料写入向量，并在检索时与课程词法证据共同重排序。嵌入服务不可用时，检索自动回退为词法匹配且不发布失败的索引状态。模型不得对企业生产数据或勘探决策作结论。

## 发布门禁

发布前必须通过：前端 `npm run build`、API `pytest -q`、外链健康检查、镜像漏洞扫描及人工浏览器验证。生产发布使用不可变镜像标签；数据库迁移必须先在预发布环境演练。发生异常时回滚 Helm Release 和对应镜像标签，不回滚已审核的知识库内容版本。

## 运行边界

匿名访问仅允许文本问答和资源浏览。OIDC、资料上传、LAS/CSV 处理、用户画像和后台管理必须在校内统一认证完成后开放。外部课程始终以新标签方式跳转，平台不保存来源平台的用户凭据。
