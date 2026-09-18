from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "深地智学 API"
    app_env: str = "development"
    api_cors_origins: str = "http://localhost:8080"
    database_url: str = "sqlite:///./var/geology_ai.db"
    redis_url: str = "redis://localhost:6379/0"
    object_storage_endpoint: str = "http://localhost:9000"
    object_storage_access_key: str | None = None
    object_storage_secret_key: str | None = None
    object_storage_bucket: str = "knowledge-documents"
    local_storage_dir: str = "./var/objects"
    upload_max_bytes: int = 52_428_800
    external_resource_allowed_hosts: str = (
        "wisdomh5.zhihuishu.com,higher.smartedu.cn,cup.yuketang.cn,"
        "5o2hyk4q.mh.chaoxing.com,vrlab.cup.edu.cn,www.xuetangx.com"
    )
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_jwks_url: str | None = None
    oidc_role_claim: str = "roles"
    geochat_auth_bridge_url: str | None = None
    anonymous_chat_requests_per_minute: int = 30
    worker_poll_seconds: int = 10
    worker_batch_size: int = 10
    ollama_base_url: str | None = None
    ollama_model: str | None = None
    llm_timeout_seconds: int = 45
    embedding_base_url: str | None = None
    embedding_model: str | None = None
    embedding_timeout_seconds: int = 30
    auto_create_schema: bool = True

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]

    @property
    def oidc_enabled(self) -> bool:
        return bool(self.oidc_issuer and self.oidc_audience)

    @property
    def geochat_auth_bridge_enabled(self) -> bool:
        return bool(self.geochat_auth_bridge_url)

    @property
    def allowed_resource_hosts(self) -> set[str]:
        return {host.strip().lower() for host in self.external_resource_allowed_hosts.split(",") if host.strip()}

    @property
    def llm_enabled(self) -> bool:
        return bool(self.ollama_base_url and self.ollama_model)

    @property
    def embedding_enabled(self) -> bool:
        return bool(self.embedding_base_url and self.embedding_model)


@lru_cache
def get_settings() -> Settings:
    return Settings()
