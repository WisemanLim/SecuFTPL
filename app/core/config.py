"""secuftpl — settings (env-driven)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    app_name: str = "secuftpl"
    env: str = "local"
    database_url: str = "sqlite:///./local.db"
    redis_url: str = ""
    hf_similarity_criteria: str = "family,param_size,license"  # PRD §7.9
    satisfaction_scale: str = "binary"  # binary | likert5 (PRD §7.9)
    ft_trigger_mode: str = "schedule"  # schedule | record_count | token_count (PRD §7.9)
    ft_trigger_record_threshold: int = 500
    ft_trigger_token_threshold: int = 1_000_000
    serving_stack: str = "ollama"  # ollama | vllm | tgi (PRD §7.9)


settings = Settings()
