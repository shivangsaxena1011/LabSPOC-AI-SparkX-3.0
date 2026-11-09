from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "LabSPOC AI API"
    app_version: str = "0.7.1"
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
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
