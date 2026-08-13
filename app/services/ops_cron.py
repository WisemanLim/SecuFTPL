"""secuftpl — ops cron 배선 플랜 생성 (PRD F5·F2 §7.5·§7.9, E6).

스케줄(cron) 자체는 ops 가 담당 — 이 서비스는 `.env`의 크론 표현식으로 crontab 라인만
생성한다(model_download.download_plan·export_runtime.conversion_plan 과 동일 원칙:
**생성만, 설치·실행 없음**). 설치는 사용자가 `crontab -e` 로 직접 반영.
"""
from app.core.config import settings


def cron_plan(base_url: str = "http://127.0.0.1:8000") -> str:
    """야간 배치(F5)·HF 신규 모델 polling(F2) crontab 라인 — `crontab -e` 붙여넣기용."""
    base = base_url.rstrip("/")
    return (
        "# secuftpl ops cron — crontab -e 로 직접 추가(자동 설치 없음)\n"
        f"{settings.ft_trigger_schedule_cron} curl -sf -X POST {base}/api/v1/batch/run"
        " -H 'content-type: application/json' -d '{}'"
        " >> /var/log/secuftpl-batch.log 2>&1\n"
        f"{settings.hf_polling_cron} curl -sf -X POST {base}/api/v1/models/events/scan"
        " -H 'content-type: application/json' -d '{}'"
        " >> /var/log/secuftpl-hf-scan.log 2>&1"
    )
