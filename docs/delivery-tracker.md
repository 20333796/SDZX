# 深地智学交付追踪

## 已完成：阶段一，工程与首页

- [x] Vue 3 + TypeScript 前端与 FastAPI API 工程骨架。
- [x] “智赋深地”匿名问答首页与四组固定导航。
- [x] 参照目标站公开前端源码完成首页门户结构收敛：分组导航、匿名问答、流式加载状态、访问统计和模块化入口。未复制目标站私有接口、签名逻辑、课程内容或业务代码。
- [x] 匿名门户配置契约：`GET /api/v1/portal-config` 为导航和首屏状态提供服务端配置，本地回退保证 API 离线时首屏可用。
- [x] 外部课程统一目录、来源标注、新标签跳转与点击契约。
- [x] Docker Compose：前端、API、PostgreSQL/pgvector、Redis、MinIO。
- [x] Helm 路由：`/api` 由 Ingress 路由到当前 Release 的 API Service，其余路径路由到前端；Web 镜像使用 `npm ci` 保证锁文件可复现构建。
- [x] GitLab CI：前端构建、API 测试、依赖审计、SBOM 与容器镜像任务。
- [x] Alembic 资源目录与知识资料迁移；兼容早期本地 SQLite 开发库。
- [x] 运行、发布、外部资源与第三方依赖边界文档。

## 已完成：首个专业模块

- [x] 测井教学案例 API、连续候选段判识、解释依据与 API 测试。
- [x] GR、RT、NPHI 曲线展示和教学判识界面。

## 进行中：知源智汇与身份能力

- [x] OIDC/OAuth2 校内统一认证令牌校验与 RBAC 适配；待学校提供 Issuer、Audience 与 JWKS 参数后联调。
- [x] PostgreSQL 资源管理持久化与 Alembic 迁移。
- [x] 教材/课件 MinIO 上传元数据、解析 Worker、知识片段持久化与审核状态机；审核后的资料通过 Ollama 嵌入适配器由 Worker 写入向量，待学校配置嵌入服务后启用。
- [x] 已发布知识片段的检索、引用 SSE 契约与前端来源展示；已实现向量相似度与词法证据重排序，未配置嵌入服务时回退为词法检索；100 题评测集待课程组提供审核题目。
- [x] OpenLayers 公开地形底图与课程教学位置图层；GeoTIFF 导入待审核和坐标校验链路接入。
- [x] 课程知识图谱 API 与 ECharts 交互视图，展示课程、知识点和能力关系。

## 后续阶段：学习与实践扩展

- [x] 智能研学公开任务目录、OIDC 保护的学习依据提交、教师反馈和评分数据闭环；校内 OIDC 联调与学情诊断、导师图谱、成长画像待后续完成。
- [x] LAS/CSV 登录后上传与规则化教学判识；教师反馈和作业评分待课程工作流接入。
- [ ] GeoTIFF 审核导入与 Cesium 野外实训接入。
- [x] Kubernetes Helm Chart、API Prometheus 指标与运维边界文档；告警、备份恢复和 50 并发压测待校内环境验证。

## 验证记录

- 2026-09-17，平台研发组：`apps/web` 执行 `npm run build` 通过；桌面和 390px 移动端的 Playwright 快照验证了二级导航、资源筛选、移动端菜单和建设中锚点，控制台为 0 错误。
- 2026-09-17，平台研发组：`apps/api` 执行 `python -m pytest -q`，23 项测试通过；`python -m alembic upgrade head` 与 `python -m alembic check` 通过；`docker compose -f infra/compose/docker-compose.yml config --quiet` 通过。
- 2026-09-17，平台研发组：本地 API 的 `/readyz` 返回数据库可用状态，`/api/v1/knowledge-graph` 返回课程、知识点和能力关系。Helm 模板验证已写入 GitLab CI；本机未安装 Helm CLI，待 CI 执行该门禁。
- 2026-09-17，平台研发组：`apps/web` 再次执行 `npm run build` 通过。Playwright 在桌面端验证了导航下拉、模式切换和匿名问答，在 390px 宽度验证了移动菜单与首屏输入区；浏览器控制台为 0 错误。快照位于 `output/playwright/`。
- 2026-09-17，平台研发组：本地 API 重启后，`/api/v1/portal-config`、资源目录、知识图谱和测井教学接口的浏览器请求均返回 200；门户配置由 API 实际加载，控制台为 0 错误。
- 2026-09-17，平台研发组：使用临时占位环境变量执行 `docker compose -f infra/compose/docker-compose.yml config --quiet` 通过；前端构建、API 23 项测试和 Alembic 检查通过。Docker Desktop 引擎与 Helm CLI 在本机不可用，Helm lint、模板和 `/api` 路由断言由 GitLab CI 执行。
- 2026-09-17，平台研发组：学习任务服务全量 API 测试 26 项通过，新增迁移 `20260917_06` 已应用并通过 Alembic 检查。Playwright 确认 `/api/v1/learning/tasks` 返回 200，桌面和 390px 移动端任务目录可用，控制台为 0 错误。

每个勾选项必须附带可复现命令、测试证据和负责人，才能进入下一阶段。

具体责任角色、依赖关系和验收出口见 `docs/project-control.md`。
