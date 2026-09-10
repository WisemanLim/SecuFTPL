"""secuftpl — 다중 런타임 배포·풀모델 export (PRD F11·§7.14, E11).

어댑터 merge(→ 풀모델 safetensors) + 런타임별 변환 명령 플랜(GGUF/MLX) 생성.
변환 명령은 model_download의 download_plan 과 동일 원칙 — **생성만, 실행 없음**
(네트워크/빌드 도구 설치는 사용자 승인 후 별도). peft/transformers 설치 시 실 merge,
미설치 시 시뮬레이션 매니페스트(학습 워커의 real/simulate 원칙과 동일).
"""
import json
from pathlib import Path

GGUF_QUANT_PRESET = "q4_k_m"  # PRD §7.9 GGUF_QUANT_PRESET 기본값
EXPORT_TARGETS = ("gguf", "mlx")


def _merge_available() -> bool:
    try:
        import peft  # noqa: F401
        import torch  # noqa: F401
        import transformers  # noqa: F401
        return True
    except ImportError:
        return False


def merge_full_model(job_id: str, base_model: str, adapter_dir: Path, out_dir: Path) -> dict:
    """어댑터 merge → 풀모델 저장. real(peft merge_and_unload) 또는 simulate(매니페스트만)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    if _merge_available():
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        base = AutoModelForCausalLM.from_pretrained(base_model)
        merged = PeftModel.from_pretrained(base, str(adapter_dir)).merge_and_unload()
        merged.save_pretrained(str(out_dir))
        AutoTokenizer.from_pretrained(base_model).save_pretrained(str(out_dir))
        mode = "real"
    else:
        (out_dir / "model.safetensors.manifest.json").write_text(json.dumps({
            "note": "simulated merge — 실 merge 는 peft/transformers 설치 환경에서 자동 전환",
            "base_model": base_model, "adapter_dir": str(adapter_dir),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        mode = "simulated"
    manifest = {"job_id": job_id, "base_model": base_model, "mode": mode,
                "adapter_dir": str(adapter_dir), "full_model_dir": str(out_dir)}
    (out_dir / "export_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def _mlx_available() -> bool:
    try:
        import mlx_lm  # noqa: F401
        return True
    except ImportError:
        return False


def convert_to_mlx(full_model_dir: Path, mlx_out_dir: Path, quantize: bool = True) -> dict:
    """실 MLX 변환 실행(mlx-lm 설치 시, Apple Silicon 전용) — §7.14 실행 단계.
    `full_model_dir`는 실 HF 형식(config.json+safetensors) 이어야 함 — 시뮬레이션
    매니페스트만 있으면 mlx_lm 이 FileNotFoundError 로 실패(호출측이 422 안내).
    미설치 시 ValueError — `conversion_plan`(명령 텍스트) 로 폴백 안내."""
    if not _mlx_available():
        raise ValueError(
            "mlx-lm 미설치 — 'uv sync --extra mlx' 후 재시도(Apple Silicon 필요), "
            "또는 export-plan 명령을 직접 실행")
    from mlx_lm import convert

    # mlx_lm.convert 는 mlx_path 가 이미 존재하면 실패(중복 저장 방지) — 미리 생성하지 않는다.
    convert(hf_path=str(full_model_dir), mlx_path=str(mlx_out_dir), quantize=quantize)
    return {"mlx_path": str(mlx_out_dir), "quantize": quantize}


def mlx_lora_train_plan(job_id: str, model_id: str, dataset_version: str) -> dict:
    """mlx-lm LoRA 실학습 명령 플랜 (PRD F19, Apple Silicon) — 생성만, 실행 없음.
    데이터: `secuftpl dataset export --format canonical` 산출 JSONL 을 mlx chat 포맷 디렉터리로 변환해 사용."""
    safe = job_id.replace("/", "_")
    data_dir = f"./exports/{safe}-mlx-data"
    command = " ".join([
        "python -m mlx_lm.lora",
        f"--model {model_id}",
        "--train",
        f"--data {data_dir}",
        f"--adapter-path ./adapters/{safe}-mlx",
        "--batch-size 1 --num-layers 8 --iters 600",
    ])
    return {
        "job_id": job_id,
        "backend": "mlx-lm",
        "available": _mlx_available(),
        "data_dir": data_dir,
        "command": command,
        "notes": [
            "데이터 준비: dataset export(canonical JSONL) → {train,valid}.jsonl 로 분할해 data_dir 에 배치",
            "mlx-lm 미설치 시 'uv sync --extra mlx' (Apple Silicon 전용)",
            "실행은 worker/수동 — 이 엔드포인트는 명령 생성만 (export-plan 과 동일 원칙)",
        ],
    }


def conversion_plan(job_id: str, full_model_dir: Path, target: str) -> str:
    """GGUF(Ollama/llama.cpp)·MLX 변환 명령 플랜 — 생성만, 실행 없음(PRD §7.14)."""
    safe = job_id.replace("/", "__")
    if target == "gguf":
        return (
            f"# secuftpl export plan — {job_id} → GGUF (Ollama/llama.cpp)\n"
            f"python convert_hf_to_gguf.py {full_model_dir} --outfile ./exports/{safe}.gguf"
            f" --outtype {GGUF_QUANT_PRESET}\n"
            f"# Ollama 등록: ollama create {safe} -f Modelfile"
            f"  (Modelfile 1행: FROM ./exports/{safe}.gguf)\n"
            f"# llama.cpp 직접 서빙: ./llama-server -m ./exports/{safe}.gguf"
        )
    if target == "mlx":
        return (
            f"# secuftpl export plan — {job_id} → MLX (Apple Silicon)\n"
            f"python -m mlx_lm.convert --hf-path {full_model_dir} --mlx-path ./exports/{safe}-mlx -q"
        )
    raise ValueError(f"unsupported export target: {target} (지원: {', '.join(EXPORT_TARGETS)})")
