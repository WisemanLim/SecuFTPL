"""secuftpl — 잡 리소스 모니터링 스냅샷 (F9, PRD §7.12).

GPU 정보는 pynvml 설치 + NVIDIA GPU 존재 시 실측, 그 외(미설치/GPU 없음)는
시뮬레이션 값(라벨 `simulated`)으로 대체 — 파이프라인이 GPU 없이도 동작하는
기존 학습 워커(app/services/trainer.py) 원칙과 동일.
"""
import hashlib

import psutil


def _gpu_snapshot(job_id: str, max_gpu: int, max_vram_gb: int) -> dict:
    try:
        import pynvml

        pynvml.nvmlInit()
        count = min(pynvml.nvmlDeviceGetCount(), max_gpu) or max_gpu
        devices = []
        for i in range(count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            devices.append({
                "index": i, "util_pct": util.gpu,
                "vram_used_gb": round(mem.used / (1024**3), 2),
                "vram_total_gb": round(mem.total / (1024**3), 2),
            })
        pynvml.nvmlShutdown()
        return {"mode": "real", "devices": devices}
    except Exception:  # noqa: BLE001 — pynvml 미설치·GPU 없음·드라이버 오류 모두 시뮬레이션으로
        seed = int(hashlib.sha256(job_id.encode()).hexdigest()[:8], 16)
        devices = [{
            "index": i, "util_pct": 40 + (seed + i * 17) % 55,
            "vram_used_gb": round(min(max_vram_gb, 4 + (seed + i * 11) % max(max_vram_gb, 1)), 2),
            "vram_total_gb": max_vram_gb,
        } for i in range(max(max_gpu, 1))]
        return {"mode": "simulated", "devices": devices}


def job_resource_snapshot(job_id: str, max_gpu: int, max_vram_gb: int) -> dict:
    """잡별 리소스 스냅샷 — CPU/메모리는 호스트 실측(psutil), GPU 는 real/simulated 자동 선택."""
    gpu = _gpu_snapshot(job_id, max_gpu, max_vram_gb)
    return {
        "job_id": job_id,
        "limits": {"max_gpu": max_gpu, "max_vram_gb": max_vram_gb},
        "cpu_pct": psutil.cpu_percent(interval=0.05),
        "mem_used_pct": psutil.virtual_memory().percent,
        "gpu_mode": gpu["mode"],
        "gpu_devices": gpu["devices"],
    }
