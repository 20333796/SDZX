# 校内 Ollama 默认模型

状态：implemented
类型：architecture
Owner：backend/package/yuxi/models/providers/

## 问题

深地智学需要在统一部署栈中使用校内局域网模型服务，并让 API 与 Worker 使用同一个可管理的默认模型配置。

## 决策

使用既有 `model_providers` 持久化配置创建 `local-ollama` OpenAI 兼容供应商，并将 `qwen3.8:latest` 设置为系统默认对话与快速响应模型。模型条目维护 262144 上下文与 `tools` 能力元数据；现有 Agent 工具编排继续负责实际工具授权和调用。SiliconFlow 不作为内置供应商或默认模型保留，运行数据库中的现有条目同步删除。

供应商地址、凭据和默认模型值由 PostgreSQL 与 Redis 模型缓存拥有，均通过既有供应商服务和系统配置服务更新。局域网供应商定义为内置模板，以支持空数据库的统一部署；凭据不写入代码、决策记录或镜像。

## 替代方案

- 在门户 API 单独配置模型：会形成与 GeoChat 不一致的运行时入口。
- 修改 Agent 代码固化模型地址：无法通过管理界面调整，也绕过既有供应商边界。
- 使用非 OpenAI 兼容适配器：当前局域网端点已提供兼容接口，没有额外收益。

## 后果

GeoChat 的模型管理页可以查看和维护供应商及模型元数据。局域网模型不可用时，模型连接与 Agent 运行会显式失败；不会静默切换到外部模型。

## 验证

在统一 Docker Compose 环境中，供应商缓存包含 `local-ollama:qwen3.8:latest`，系统默认配置指向该模型。通过 `test_model_status_by_spec` 实际调用局域网 OpenAI 兼容接口，返回“连接正常”；模型清单和强制工具调用请求均已得到有效响应。
