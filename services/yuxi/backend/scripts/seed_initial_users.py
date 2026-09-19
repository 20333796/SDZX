from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from sqlalchemy import func, select


APP_ROOT = Path(__file__).resolve().parents[1]
for import_path in (APP_ROOT, APP_ROOT / "package"):
    import_path_str = str(import_path)
    if import_path_str not in sys.path:
        sys.path.insert(0, import_path_str)

SUPERADMIN_UID = "zwj"
SUPERADMIN_NAME = "张文杰"
SUPERADMIN_PHONE_NUMBER = "15251638888"
SUPERADMIN_PASSWORD = "zwj12138"
DEFAULT_USER_PASSWORD = "yuxi123456"


class DepartmentSeed(TypedDict):
    name: str
    description: str
    prefix: str
    admin_count: int
    normal_count: int
    account_type: str


# 平台标准部门：管理员、教师、学生、访客（与 ensure_standard_departments 保持一致）
DEPARTMENTS: list[DepartmentSeed] = [
    {"name": "管理员", "description": "系统管理员所属部门", "prefix": "admin", "admin_count": 1, "normal_count": 0, "account_type": "student"},
    {"name": "教师", "description": "教师用户所属部门", "prefix": "teacher", "admin_count": 1, "normal_count": 3, "account_type": "teacher"},
    {"name": "学生", "description": "学生用户所属部门", "prefix": "student", "admin_count": 1, "normal_count": 5, "account_type": "student"},
    {"name": "访客", "description": "访客用户所属部门", "prefix": "visitor", "admin_count": 0, "normal_count": 2, "account_type": "visitor"},
]


class SeedError(Exception):
    pass


def load_project_env() -> None:
    load_dotenv(APP_ROOT / ".env", override=False)
    load_dotenv(APP_ROOT.parent / ".env", override=False)
    load_dotenv(Path.cwd() / ".env", override=False)


async def ensure_uninitialized(session) -> None:
    from yuxi.storage.postgres.models_business import User

    user_count = await session.scalar(select(func.count(User.id)))
    if user_count:
        raise SeedError(f"系统已初始化：users 表已有 {user_count} 个用户，脚本已退出。")

    superadmin_count = await session.scalar(select(func.count(User.id)).where(User.role == "superadmin"))
    if superadmin_count:
        raise SeedError("系统已初始化：已存在超级管理员，脚本已退出。")


async def seed_initial_users() -> None:
    from yuxi.utils.auth_utils import AuthUtils
    from yuxi.storage.postgres.manager import pg_manager
    from yuxi.storage.postgres.models_business import Department, User
    from yuxi.utils.datetime_utils import utc_now_naive

    try:
        pg_manager.initialize()
        await pg_manager.create_business_tables()
        await pg_manager.ensure_business_schema()

        async with pg_manager.get_async_session_context() as session:
            await ensure_uninitialized(session)

            departments: dict[str, Department] = {}
            for department_seed in DEPARTMENTS:
                department = Department(
                    name=department_seed["name"],
                    description=department_seed["description"],
                )
                session.add(department)
                departments[department_seed["prefix"]] = department

            await session.flush()

            users = [
                User(
                    username=SUPERADMIN_NAME,
                    uid=SUPERADMIN_UID,
                    phone_number=SUPERADMIN_PHONE_NUMBER,
                    password_hash=AuthUtils.hash_password(SUPERADMIN_PASSWORD),
                    role="superadmin",
                    department_id=departments["admin"].id,
                    last_login=utc_now_naive(),
                )
            ]

            for department_seed in DEPARTMENTS:
                department = departments[department_seed["prefix"]]
                for index in range(1, department_seed["admin_count"] + 1):
                    users.append(
                        User(
                            username=f"{department_seed['name']}管理员{index}",
                            uid=f"{department_seed['prefix']}_admin_{index}",
                            password_hash=AuthUtils.hash_password(DEFAULT_USER_PASSWORD),
                            role="admin",
                            account_type=department_seed["account_type"],
                            department_id=department.id,
                        )
                    )
                for index in range(1, department_seed["normal_count"] + 1):
                    users.append(
                        User(
                            username=f"{department_seed['name']}用户{index}",
                            uid=f"{department_seed['prefix']}_user_{index:02d}",
                            password_hash=AuthUtils.hash_password(DEFAULT_USER_PASSWORD),
                            role="user",
                            account_type=department_seed["account_type"],
                            department_id=department.id,
                        )
                    )

            session.add_all(users)
    finally:
        await pg_manager.close()


def main() -> int:
    load_project_env()
    try:
        asyncio.run(seed_initial_users())
    except SeedError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"初始化种子用户失败：{exc}", file=sys.stderr)
        return 1

    admin_total = sum(d["admin_count"] for d in DEPARTMENTS)
    normal_total = sum(d["normal_count"] for d in DEPARTMENTS)
    print(
        f"初始化完成：已创建超级管理员 {SUPERADMIN_NAME}（{SUPERADMIN_UID}）、"
        f"{len(DEPARTMENTS)} 个标准部门（{'/'.join(d['name'] for d in DEPARTMENTS)}）、"
        f"{admin_total} 个部门管理员和 {normal_total} 个普通用户。"
    )
    print("超级管理员密码：zwj12138")
    print("部门管理员和普通用户默认密码：yuxi123456")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
