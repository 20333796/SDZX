# 深地智学 代码审查报告

- 审查日期：2026-09-17
- 审查范围：`apps/api`（FastAPI）、`apps/web`（Vue 3）、`apps/worker`、`infra`、`packages/contracts`
- 代码规模：约 56 个 Python 文件、9 个 Vue 组件、7 个 TS 文件
- 方法：静态审查 + 关键路径实证验证（测井解析用例在本机实际执行）

## 总体评价

工程骨架质量高于一般原型：分层清晰（routers / services / modules 分离）、Pydantic 契约完整、OIDC 校验正确（限定 RS256/ES256、校验 issuer 与 audience、角色白名单过滤）、SSRF 有域名白名单与重定向拦截、外部资源链接带 `rel="noopener noreferrer"`、Alembic 迁移与 Helm/CI 配套齐全，`docs/delivery-tracker.md` 对未完成项标注诚实。

主要问题集中在**测井文件解析的实用性**、**流式输出实现**、以及**若干缺少纵深防御的位置**。以下按严重程度列出。

---

## 高：影响功能正确性 / 可用性

### 1. LAS/CSV 解析强制「恰好 4 列」，真实测井文件会被拒绝

位置：`apps/api/app/modules/well_log.py:152`（CSV）、`:161`（LAS）

```python
headers = {header: _canonical_curve_name(header) for header in reader.fieldnames}
if set(headers.values()) != {"depth", "gr", "rt", "nphi"}:
    raise ValueError("CSV must contain depth, GR, RT and NPHI curves")
```

未识别的列会映射为 `None`，进入 `set(headers.values())`，导致集合不相等。因此只要文件**多出任意一列**（真实测井数据常见的 SP、CAL、DTC、DEN…）就会被拒。

**实测验证**（本机执行）：

| 用例 | 结果 |
|---|---|
| 标准 4 列 CSV | 通过，4 points |
| 多一列 `sp` 的 CSV | 失败：`CSV must contain depth, GR, RT and NPHI curves` |
| 深度降序 CSV | 失败：`Depth must be in ascending order`（预期内） |
| `gr=300`（超出 0–250） | 失败，但提示为 `invalid numeric value` |

**建议**：改为子集校验（后续 `rows` 提取已经用 `if canonical` 过滤掉了 `None`，无需改动）：

```python
required = {"depth", "gr", "rt", "nphi"}
if not required.issubset(set(headers.values())):
    raise ValueError("CSV must contain depth, GR, RT and NPHI curves")
```

### 2. LAS 深度曲线假设第一条曲线即深度

位置：`apps/api/app/modules/well_log.py:164`

```python
for index in range(len(las[las.curves[0].mnemonic])):
```

隐含假设 `las.curves[0]` 是深度曲线。部分 LAS 文件首条曲线并非深度，会导致行数或取值错位。

**建议**：改用 lasio 的深度索引（`las.index` / `las.depth_mnemonic`）确定行数。此项本机无 `lasio`，**未实测**，需装依赖后回归验证。

### 3. SSE 流式输出按「单个字符」发送，且每字符休眠 12ms

位置：`apps/api/app/routers/chat.py:32-34`

```python
for token in reply:
    yield f"event: token\ndata: {json.dumps({'content': token}, ensure_ascii=False)}\n\n"
    await asyncio.sleep(0.012)
```

`reply` 是字符串，迭代得到的是**字符**而非 token。一段 500 字的回答会产生约 500 个 SSE 事件、耗时约 6 秒，且中文逐字渲染观感破碎。

**建议**：按 2–4 字或词粒度切片后发送，并显著缩短/移除固定 sleep。

---

## 中：健壮性 / 安全纵深防御

### 4. 限流仅覆盖 `/chat/stream`，其他匿名端点无保护

位置：`apps/api/app/rate_limit.py:22`

```python
if request.method != "POST" or request.url.path != "/api/v1/chat/stream":
```

`/api/v1/well-log/analyze`（匿名、单次最多 5000 点）与 `/api/v1/knowledge/search`（全表扫描式检索）均无频率限制。

**建议**：把限流扩展到其他匿名 POST 端点，或改用通用的每 IP 限流。

### 5. 限流键使用直连 IP，反向代理后失效

位置：`apps/api/app/rate_limit.py:24` — `request.client.host`

在 Nginx / Ingress 之后该值为代理地址，所有用户共享同一计数桶，限流形同虚设；同时也未处理 `X-Forwarded-For` 伪造。

**建议**：按部署拓扑取可信代理头，或配置 `ProxyHeadersMiddleware` 并限定可信跳数。

### 6. `/metrics` 端点无访问控制

位置：`apps/api/app/main.py:68`

Prometheus 指标含请求路径与延迟分布，当前对任何可达 API 的访问者开放。

**建议**：限制为集群内/内网访问，或用 Ingress/NetworkPolicy 隔离。

### 7. `LocalObjectStore.put` 缺少 `get` 那样的路径校验

位置：`apps/api/app/storage.py:24`

`get()` 有 `resolve()` + `root not in parents` 校验，`put()` 没有。当前 `object_key` 由 `uuid4` + 后缀白名单生成（`services/knowledge.py:57`），因此**暂不构成可利用漏洞**；但属于纵深防御缺失，一旦将来改用用户可控 key 即出现路径穿越。

**建议**：`put()` 复用与 `get()` 相同的校验。

### 8. 资料解析的事务边界：删除旧分片后异常仍提交

位置：`apps/api/app/services/ingestion.py:80-103`

`session.execute(delete(chunks))` 执行后，若后续写入新分片过程中抛出异常，会进入 `except` 并执行 `session.commit()`，可能留下「旧分片已删、新分片不全」的状态。

**建议**：异常分支先 `session.rollback()`，再用独立事务记录失败状态与重试次数。

### 9. LLM 调用异常被静默吞掉

位置：`apps/api/app/services/llm.py:38-39`

```python
except (httpx.HTTPError, ValueError, AttributeError):
    pass
```

Ollama 不可用时与「无资料需回退」返回同样的兜底文案，无法区分故障，也没有日志或埋点。

**建议**：记录 warning 日志并计入失败指标，便于运维发现 LLM 掉线。

### 10. 数值越界报错信息误导

位置：`apps/api/app/modules/well_log.py:141`

`GR=300`（超出 0–250）被统一包装成 `Well-log file contains an invalid numeric value`，用户会以为是数字格式错误，实际是量程越界。

**建议**：区分「无法解析为数字」与「超出合理量程」，后者提示具体曲线与允许范围。

---

## 低：一致性 / 可维护性

### 11. 前后端种子数据双份维护，已发生漂移

后端 `app/data.py` 有 **15** 条资源，前端 `apps/web/src/config/resources.ts` 的 fallback 只有 **14** 条，缺少 `froude-number-vr`。

**实测验证**（读取本地 `apps/api/var/geology_ai.db`）：

```
external_resources: 15   (active 14 / pending 1)
froude-number-vr 存在: 1
```

该条正是唯一的 `pending` 资源。因此 API 正常时首屏显示 15 条（含「资源链接待学院补充」），前端回退时只剩 14 条——同一页面在不同链路下内容不一致。

**建议**：前端 fallback 仅保留最小可用集，或由构建期从后端契约生成，避免手工同步。

### 12. Prometheus `path` 标签基数过高

位置：`apps/api/app/observability.py:26`

使用原始 `request.url.path` 作标签，含资源 ID 的路径（如 `/knowledge/documents/{id}/transitions`）会随时间不断产生新时间序列。

**建议**：改用路由模板（如 `request.scope["route"].path`）。

### 13. Helm Deployment 缺少 securityContext

`infra/helm/deep-geology/templates/api.yaml` 等未设置 `runAsNonRoot`、`readOnlyRootFilesystem`、`capabilities.drop`。

### 14. 门户统计未过滤资源状态

位置：`apps/api/app/routers/portal.py:57`

`resource_count` 统计全部资源，包含 `pending`（链接待补充）的条目。实测本地库为 15 条（active 14 + pending 1），首屏「课程资源 15+」把链接待补充的条目也计入，与用户在页面上实际可点击的 14 条不一致。

**建议**：统计口径与列表口径保持一致（例如只统计 `active`），或改为「已接入 / 待补充」双数字呈现。

### 15. 权限不一致（需确认是否有意为之）

`/api/v1/well-log/analyze` 匿名可调用，而 `/api/v1/well-log/analyze-file` 要求登录。若属有意设计（教学案例公开、文件上传受控），建议在文档中明确说明。

---

## 补充说明（非缺陷）

- `app/routers/knowledge_graph.py` 目前返回 7 节点 6 边的静态常量，属阶段性实现，与 `docs/delivery-tracker.md` 中「课程知识图谱 API 与交互视图」的描述一致。
- `AUTO_CREATE_SCHEMA` 默认 `True`（`config.py:35`），而 compose 与 Helm 均显式设为 `false`，生产路径正确；但本地默认仍会 `create_all`，与 Alembic 并存时需注意 schema 来源。

## 测试执行说明

`docs/delivery-tracker.md` 记录 2026-09-17 API 测试 26 项通过（`apps/api` 下 `python -m pytest -q`）。

本次审查**未能在本机复跑完整测试套件**：本机 Python 环境未安装 `requirements.txt` 依赖（redis / minio / PyJWT / lasio / prometheus-client / httpx / pydantic-settings 均缺失）。审查中尝试在临时目录用 Python 3.12 建立隔离环境安装依赖，但安装耗时过长且未成功，因此测试复跑中止。上述测试通过记录来自项目自身文档，**未经本次审查独立验证**。

已独立实测的部分：测井解析相关结论通过实际执行验证（见第 1 节表格，使用本机已有的 Python 3.11 + pydantic 环境直接调用 `app.modules.well_log`）。

建议后续在具备依赖的环境（或 CI）中执行 `cd apps/api && python -m pytest -q` 复核，并在修复第 1、3 项后补充对应回归用例。
