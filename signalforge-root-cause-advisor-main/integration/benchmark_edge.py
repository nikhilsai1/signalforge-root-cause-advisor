import time
import requests

PROMPT = "The motor tripped on VFD overload with high bearing temperature. State immediate operator action in 2 sentences."
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "llama3.2:3b"

print(f"[*] Starting Edge Benchmark on {MODEL_NAME}...")

latencies = []
tokens_per_sec = []

try:
    for i in range(3):
        start = time.perf_counter()
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL_NAME,
            "prompt": PROMPT,
            "stream": False
        }, timeout=60).json()
        total_time = time.perf_counter() - start
        
        eval_count = resp.get("eval_count", 0)
        eval_duration_sec = resp.get("eval_duration", 1) / 1e9
        tps = eval_count / eval_duration_sec if eval_duration_sec > 0 else 0
        
        latencies.append(total_time)
        tokens_per_sec.append(tps)
        print(f"Run {i+1}: {total_time:.2f}s total | {tps:.2f} tokens/sec")

    print("\n--- BENCHMARK RESULTS FOR SLIDES/DEMO ---")
    print(f"Model: {MODEL_NAME}")
    print(f"Avg Latency: {sum(latencies)/len(latencies):.2f} seconds")
    print(f"Throughput: {sum(tokens_per_sec)/len(tokens_per_sec):.1f} tokens/sec (Fully Offline)")
except Exception as e:
    print(f"[!] Benchmark error: {e}")
    print("[!] Make sure Ollama is running (`ollama serve`) and the model is downloaded (`ollama pull llama3.2:3b`).")
