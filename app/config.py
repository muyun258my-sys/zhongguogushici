from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    app_name: str = "中国古诗词智能问答助手"
    data_file: Path = BASE_DIR / "data" / "poems.json"
    vector_store_dir: Path = BASE_DIR / "storage" / "chroma"
    top_k: int = 4
    auto_ingest_on_start: bool = False
    openai_api_key: str = ""
    openai_base_url: str = ""
    llm_model_name: str = "gpt-4o-mini"
    embedding_provider: str = "local"
    embedding_model_name: str = "text-embedding-3-small"
    local_embedding_model: str = "BAAI/bge-small-zh-v1.5"
    local_embedding_cache_dir: Path = BASE_DIR / "models" / "embedding"

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        top_k=int(os.getenv("TOP_K", "4")),
        auto_ingest_on_start=os.getenv("AUTO_INGEST_ON_START", "false").lower() == "true",
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "").strip(),
        llm_model_name=os.getenv("LLM_MODEL_NAME", "gpt-4o-mini").strip(),
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "local").strip().lower(),
        embedding_model_name=os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small").strip(),
        local_embedding_model=os.getenv("LOCAL_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5").strip(),
        local_embedding_cache_dir=Path(
            os.getenv("LOCAL_EMBEDDING_CACHE_DIR", str(BASE_DIR / "models" / "embedding"))
        ),
    )
