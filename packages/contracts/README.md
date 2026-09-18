# API 契约

前后端契约由 FastAPI OpenAPI 文档生成：运行 `python scripts/export_openapi.py` 会更新版本化快照 `openapi.json`。前端可据此生成类型，避免复制接口定义；接口或响应模型变更时，必须同步更新快照和测试。
