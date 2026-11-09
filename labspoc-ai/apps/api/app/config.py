from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "LabSPOC AI API"
    app_version: str = "0.9.0"
    database_url: str = "sqlite:///./labspoc.db"
    upload_dir: str = "./uploads"
    max_upload_mb: int = 25
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    min_retrieval_score: int = 1
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    admin_api_key: str = ""
    admin_username: str = "admin"
    admin_password: str = ""
    jwt_secret: str = ""
    access_token_minutes: int = 120
    embedding_model: str = "gemini-embedding-001"
    semantic_retrieval_enabled: bool = True
    retrieval_top_k: int = 5
    retrieval_min_score: float = 0.18
    lab_name: str = "AI & ML Laboratory"
    institution_name: str = "Oriental Institute of Science & Technology, Bhopal"
    rate_limit_per_minute: int = 120
    trusted_proxies: str = "127.0.0.1,::1,localhost"
    environment: str = "development"

    # Production Storage Configuration (S3-compatible / MinIO / Cloudflare R2)
    storage_backend: str = "local"  # "local" or "s3"
    s3_endpoint_url: str = ""       # e.g., https://<account_id>.r2.cloudflarestorage.com
    s3_bucket_name: str = "labspoc-uploads"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_region: str = "us-east-1"
    s3_public_url: str = ""         # Optional CDN or public bucket endpoint prefix

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
