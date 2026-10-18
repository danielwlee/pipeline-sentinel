"""Central config. Override any model via env var; verify names with `ollama list`."""
import os

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.getenv("SENTINEL_LLM", "qwen3.8:27b-mlx")
EMBED_MODEL = os.getenv("SENTINEL_EMBED", "embeddinggemma-2:740m")
RERANK_MODEL = os.getenv("SENTINEL_RERANK", "pdurugyan/qwen3-reranker-0.6b-q8_0:latest")
# 32k is plenty for the agent; 128k costs lots of KV-cache memory and speed.
NUM_CTX = int(os.getenv("SENTINEL_NUM_CTX", "32768"))
INDEX_DIR = os.getenv("SENTINEL_INDEX_DIR", "data/index")
