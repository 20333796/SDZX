from __future__ import annotations

import json
import os
import re
from pathlib import Path

import jwt
import requests

ROOT = Path(__file__).resolve().parents[1]
GEOCHAT_API = os.getenv("GEOCHAT_API", "http://127.0.0.1:5050/api").rstrip("/")
PORTAL_API = os.getenv("PORTAL_API", "http://127.0.0.1:8000/api/v1").rstrip("/")


def token() -> str:
    import datetime

    token_secret = os.getenv("JWT_SECRET_KEY", "").strip()
    instance_id = os.getenv("YUXI_INSTANCE_ID", "").strip()
    if not token_secret or not instance_id:
        raise RuntimeError("JWT_SECRET_KEY 和 YUXI_INSTANCE_ID 未配置，请通过 services/yuxi/.env 运行导入器")
    now = datetime.datetime.now(datetime.timezone.utc)
    return jwt.encode(
        {
            "sub": os.getenv("GEOCHAT_IMPORT_USER_ID", "1"),
            "exp": now + datetime.timedelta(minutes=30),
            "iss": f"yuxi-know:{instance_id}",
            "aud": "yuxi-know-api",
        },
        token_secret,
        algorithm="HS256",
    )


def build_markdown() -> Path:
    data = json.loads((ROOT / "apps/web/src/config/mentorDirections.json").read_text(encoding="utf-8"))
    lines = [
        "# 中国石油大学（北京）导师、课程与仿真资源知识库",
        "",
        "数据来源：来自中国石油大学（北京）教师平台 faculty.cup.edu.cn 的公开教师主页，以及本校门户已配置的课程和仿真资源。导入时间：2026-09-18。",
        "",
        "## 导师信息",
    ]
    for teacher in data.get("teachers", []):
        directions = "；".join(x.strip() for x in teacher.get("directions", []) if x.strip())
        lines.extend([
            f"### {teacher.get('name', '')}",
            f"- 所属学院/单位：{teacher.get('facultyName', '')}",
            f"- 研究方向、简介：{directions or '官网未公开填写'}",
            f"- 官网教师主页：https://faculty.cup.edu.cn/{teacher.get('path', '')}/",
            "",
        ])

    # Keep the local portal directory in the same knowledge source. The portal
    # contains verified entries (including teachers not present in the scraped
    # faculty export), so merge by name without duplicating existing records.
    existing_names = {str(teacher.get("name", "")).strip() for teacher in data.get("teachers", [])}
    mentor_graph = (ROOT / "apps/web/src/config/mentorGraph.ts").read_text(encoding="utf-8")
    profile_base = {
        "地球物理学院": {
            "教授": "https://www.cup.edu.cn/geophysics/szdw/js/",
            "副教授": "https://www.cup.edu.cn/geophysics/szdw/fjs/",
            "讲师": "https://www.cup.edu.cn/geophysics/szdw/jshi/",
        },
        "地球科学学院": {
            "教授": "https://www.cup.edu.cn/geosci/szdw/jiaoshou/",
            "副教授": "https://www.cup.edu.cn/geosci/szdw/fujiaoshou/",
            "讲师": "https://www.cup.edu.cn/geosci/szdw/jiangshi/",
        },
    }
    for school, title, name, page in re.findall(
        r"\['([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'\]", mentor_graph
    ):
        if name in existing_names or school not in profile_base or title not in profile_base[school]:
            continue
        lines.extend([
            f"### {name}",
            f"- 所属学院/单位：{school}",
            f"- 职称：{title}",
            "- 研究方向、简介：门户教师目录已列示该教师，官网公开简介以教师主页为准。",
            f"- 官网教师主页：{profile_base[school][title]}{page}",
            "",
        ])
        existing_names.add(name)

    response = requests.get(f"{PORTAL_API}/external-resources", timeout=30)
    response.raise_for_status()
    lines.append("## 课程、虚拟仿真与教学资源")
    for resource in response.json():
        lines.extend([
            f"### {resource.get('title', '')}",
            f"- 类型：{resource.get('category') or '教学资源'}",
            f"- 提供方：{resource.get('provider') or '中国石油大学（北京）'}",
            f"- 说明：{resource.get('description') or ''}",
            f"- 访问地址：{resource.get('url') or '可从门户相应课程/仿真入口打开'}",
            "",
        ])
    out = Path(os.getenv("KNOWLEDGE_OUTPUT_DIR", ROOT / "output")) / "geochat-cup-knowledge.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> None:
    headers = {"Authorization": f"Bearer {token()}"}
    name = "中国石油大学（北京）导师与课程知识库"
    existing = requests.get(f"{GEOCHAT_API}/knowledge/databases", headers=headers, timeout=30)
    existing.raise_for_status()
    existing_payload = existing.json()
    databases = existing_payload if isinstance(existing_payload, list) else existing_payload.get("databases", [])
    kb = next((x for x in databases if x.get("name") == name), None)
    if not kb:
        response = requests.post(
            f"{GEOCHAT_API}/knowledge/databases",
            headers=headers,
            json={
                "database_name": name,
                "description": "中国石油大学（北京）全校教师、课程、虚拟仿真和教学资源，优先采用官网公开信息。",
                "kb_type": "milvus",
                "embedding_model_spec": "alibaba-cn:text-embedding-v4",
                "share_config": {"version": 2, "read_scope": {"access_level": "global", "department_ids": [], "user_uids": []}, "manage_scope": None},
            },
            timeout=60,
        )
        if not response.ok:
            raise RuntimeError(f"创建知识库失败 {response.status_code}: {response.text}")
        kb = response.json()
    kb_id = kb.get("kb_id") or kb.get("id")
    if not kb_id:
        raise RuntimeError(f"未取得知识库 ID: {kb}")
    document = build_markdown()
    exists = requests.get(
        f"{GEOCHAT_API}/knowledge/databases/{kb_id}/documents/exists",
        headers=headers,
        params={"filename": document.name},
        timeout=30,
    )
    exists.raise_for_status()
    if exists.json().get("exists"):
        print(json.dumps({"kb_id": kb_id, "file": document.name, "status": "already_exists"}, ensure_ascii=False, indent=2))
        return
    with document.open("rb") as fh:
        uploaded = requests.post(f"{GEOCHAT_API}/knowledge/files/upload", headers=headers, params={"kb_id": kb_id}, files={"file": (document.name, fh, "text/markdown")}, timeout=120)
    uploaded.raise_for_status()
    item = uploaded.json()
    params = {
        "content_type": "file",
        "auto_index": True,
        "content_hashes": {item["file_path"]: item["content_hash"]},
        "file_sizes": {item["file_path"]: item["size"]},
    }
    ingested = requests.post(
        f"{GEOCHAT_API}/knowledge/databases/{kb_id}/documents",
        headers=headers,
        json={"items": [item["file_path"]], "params": params},
        timeout=60,
    )
    ingested.raise_for_status()
    print(json.dumps({"kb_id": kb_id, "file": document.name, "upload": item, "ingest": ingested.json()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
