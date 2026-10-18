"""M0 sanity check: are models pulled, and how fast is the LLM at 32k context?"""
import json
import sys
import time
import urllib.request

sys.path.insert(0, "src")
from sentinel import config  # noqa: E402


def call(path, payload=None):
    req = urllib.request.Request(
        config.OLLAMA_HOST + path,
        data=json.dumps(payload).encode() if payload else None,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def main():
    try:
        have = {m["name"] for m in call("/api/tags")["models"]}
    except Exception as e:
        sys.exit(f"Ollama not reachable at {config.OLLAMA_HOST}: {e}")
    ok = True
    for label, name in [("LLM", config.LLM_MODEL), ("embed", config.EMBED_MODEL),
                        ("rerank", config.RERANK_MODEL)]:
        found = name in have or f"{name}:latest" in have
        ok &= found
        print(f"[{'ok' if found else 'MISSING'}] {label}: {name}")
    if not ok:
        print("\nAvailable:", *sorted(have), sep="\n  ")
        sys.exit("Fix names (env vars SENTINEL_LLM / SENTINEL_EMBED / SENTINEL_RERANK).")
    t = time.time()
    r = call("/api/chat", {"model": config.LLM_MODEL, "stream": False,
             "messages": [{"role": "user", "content": "Reply with the word: ready"}],
             "options": {"num_ctx": config.NUM_CTX}})
    print(f"LLM reply in {time.time()-t:.1f}s: {r['message']['content'][:80]!r}")
    e = call("/api/embed", {"model": config.EMBED_MODEL, "input": "select 1"})
    print(f"Embedding dim: {len(e['embeddings'][0])}")


if __name__ == "__main__":
    main()
