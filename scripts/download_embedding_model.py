from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from huggingface_hub import snapshot_download

from app.config import get_settings


def main() -> int:
    load_dotenv()
    settings = get_settings()
    target_dir = settings.local_embedding_cache_dir / settings.local_embedding_model.replace("/", "--")
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {settings.local_embedding_model} ...")
    print(f"Target: {target_dir}")
    snapshot_download(
        repo_id=settings.local_embedding_model,
        local_dir=target_dir,
        local_dir_use_symlinks=False,
    )
    print("Embedding model download complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
