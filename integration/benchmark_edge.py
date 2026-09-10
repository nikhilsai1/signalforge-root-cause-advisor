"""Edge hardware benchmark: sends repeated real operator-style prompts to a
local Ollama instance and logs response time and tokens/sec, so the team can
report real offline-inference performance numbers in the demo.

Run: python integration/benchmark_edge.py
"""
import json
import os
import platform
import statistics
import time
from datetime import datetime, timezone

import ollama
import psutil

MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
RUNS_PER_PROMPT = 3

# Real operator-style questions matching the actual RAG use case, not generic
# filler prompts - these are representative of what the system answers live.
PROMPTS = [
    "Why did Motor_1 trip? What do I do right now?",
    "A VFD current high alarm fired but motor load was normal before the trip. What should I do?",
    "LINE1.MTR_01.OVERLOAD just fired and motor_load_pct was trending above 90%. What do I do right now?",
]

SYSTEM_PROMPT = (
    "You are an industrial operations assistant. Answer the operator's question "
    "using ONLY the SOP context provided below. Synthesize a single, confident, "
    "actionable answer from ALL relevant sections in the context."
)

RESULTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark_results.json")


def get_hardware_info() -> dict:
    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_cores_physical": psutil.cpu_count(logical=False),
        "cpu_cores_logical": psutil.cpu_count(logical=True),
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
    }


def run_once(prompt: str) -> dict:
    start = time.perf_counter()
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context: (benchmark run, no retrieval)\n\nOperator question: {prompt}"},
        ],
        options={"temperature": 0.1},
    )
    wall_time = time.perf_counter() - start

    eval_count = response.get("eval_count", 0)
    eval_duration_s = response.get("eval_duration", 0) / 1e9
    tokens_per_sec = eval_count / eval_duration_s if eval_duration_s > 0 else 0.0

    return {
        "prompt": prompt,
        "wall_time_s": round(wall_time, 3),
        "eval_count_tokens": eval_count,
        "eval_duration_s": round(eval_duration_s, 3),
        "tokens_per_sec": round(tokens_per_sec, 2),
        "prompt_eval_count_tokens": response.get("prompt_eval_count", 0),
    }


def main():
    hw = get_hardware_info()
    print("=== Edge Hardware Benchmark ===")
    print(f"Model: {MODEL}")
    print(f"Hardware: {hw['processor'] or hw['platform']}")
    print(f"CPU cores: {hw['cpu_cores_physical']} physical / {hw['cpu_cores_logical']} logical")
    print(f"RAM: {hw['ram_total_gb']} GB")
    print()

    all_runs = []
    for prompt in PROMPTS:
        print(f"Prompt: {prompt!r}")
        for i in range(RUNS_PER_PROMPT):
            result = run_once(prompt)
            all_runs.append(result)
            print(
                f"  run {i + 1}/{RUNS_PER_PROMPT}: "
                f"{result['tokens_per_sec']} tok/s, "
                f"{result['wall_time_s']}s wall time, "
                f"{result['eval_count_tokens']} tokens generated"
            )
        print()

    tps_values = [r["tokens_per_sec"] for r in all_runs if r["tokens_per_sec"] > 0]
    wall_times = [r["wall_time_s"] for r in all_runs]

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "hardware": hw,
        "runs": all_runs,
        "summary": {
            "tokens_per_sec_mean": round(statistics.mean(tps_values), 2),
            "tokens_per_sec_median": round(statistics.median(tps_values), 2),
            "tokens_per_sec_min": round(min(tps_values), 2),
            "tokens_per_sec_max": round(max(tps_values), 2),
            "wall_time_s_mean": round(statistics.mean(wall_times), 2),
        },
    }

    print("=== Summary ===")
    for k, v in summary["summary"].items():
        print(f"{k}: {v}")

    with open(RESULTS_FILE, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nFull results written to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
