from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from app.config import get_settings
from app.rag.vectorstore import PoetryVectorStore


def main() -> None:
    load_dotenv()
    settings = get_settings()
    store = PoetryVectorStore(settings)
    success = store.ingest(reset=True)
    if success:
        print(f"向量库已完成重建：{settings.vector_store_dir}")
    else:
        print("未检测到可用的 LLM/Embedding 配置，向量入库已跳过。请先在 .env 中填写 OPENAI_API_KEY。")


if __name__ == "__main__":
    main()
