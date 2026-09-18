# 第三方依赖边界

当前应用前端使用 Vue、Vite、Vue Router、Pinia、OpenLayers 与 Lucide 图标；API 和 Worker 使用 FastAPI、SQLAlchemy、Alembic、MinIO Python SDK、PyJWT、python-multipart、pypdf、python-docx、python-pptx 和 lasio。每项依赖在引入前必须记录版本、许可证、来源、漏洞扫描结果和 SBOM 条目。

当前新增依赖的上游许可证为：MinIO Python SDK（Apache-2.0）、PyJWT（MIT）、python-multipart（Apache-2.0）、pypdf（BSD-3-Clause）、python-docx（MIT）、python-pptx（MIT）和 lasio（MIT）。在发布流水线中使用锁定依赖生成 SBOM，并运行镜像与依赖漏洞扫描；发现高危未豁免漏洞时阻断发布。

已批准作为候选依赖：CesiumJS（Apache-2.0）、OpenLayers（BSD-2-Clause）、geotiff.js（MIT）、lasio（MIT）、Welly（Apache-2.0）和 LlamaIndex（MIT）。

`segyio` 为 LGPL-3.0，须在二期前完成法务审查与依赖隔离。Dify 当前不作为本平台基础设施依赖。不得复制第三方课程内容、平台页面或品牌资产。
