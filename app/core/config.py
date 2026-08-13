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
    ft_trigger_schedule_cron: str = "0 2 * * *"  # 야간 배치 크론 표현식 (schedule 모드, PRD §7.9)
    hf_polling_cron: str = "0 3 * * 1"  # 신규 모델 이벤트 polling 크론 표현식(F2, PRD §7.9)
    serving_stack: str = "ollama"  # ollama | vllm | tgi | llama.cpp | mlx (PRD §7.9)
    dataset_min_records: int = 500  # 튜닝 시작 게이트 — approved 미만이면 잡 제출 차단 (PRD §7.5)
    job_max_gpu: int = 1  # 잡당 GPU 개수 기본 상한 (F9, PRD §7.9·§7.12)
    job_max_vram_gb: int = 24  # 잡당 VRAM 기본 상한(GB) (F9)
    total_gpu_capacity: int = 2  # 시스템 전체 동시 학습 GPU 상한 — 초과 시 실제 큐잉(F9, §7.12)


settings = Settings()
