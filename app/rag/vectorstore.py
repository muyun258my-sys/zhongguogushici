from __future__ import annotations

import shutil
from pathlib import Path

from langchain_core.documents import Document

from app.config import Settings
from app.rag.repository import list_poems, render_poem_context


class PoetryVectorStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _build_embeddings(self):
        if not self.settings.llm_enabled:
            return None

        from langchain_openai import OpenAIEmbeddings

        kwargs = {
            "model": self.settings.embedding_model_name,
            "api_key": self.settings.openai_api_key,
        }
        if self.settings.openai_base_url:
            kwargs["base_url"] = self.settings.openai_base_url
        return OpenAIEmbeddings(**kwargs)

    def _build_documents(self) -> list[Document]:
        documents: list[Document] = []
        for poem in list_poems():
            documents.append(
                Document(
                    page_content=render_poem_context(poem),
                    metadata={
                        "poem_id": poem["id"],
                        "title": poem["title"],
                        "author": poem["author"],
                        "dynasty": poem["dynasty"],
                        "source": poem.get("source", "未知来源"),
                    },
                )
            )
        return documents

    def ingest(self, reset: bool = False) -> bool:
        embeddings = self._build_embeddings()
        if embeddings is None:
            return False

        store_dir = Path(self.settings.vector_store_dir)
        if reset and store_dir.exists():
            shutil.rmtree(store_dir)
        store_dir.mkdir(parents=True, exist_ok=True)

        from langchain_chroma import Chroma

        documents = self._build_documents()
        Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=str(store_dir),
        )
        return True

    def similarity_search(self, query: str, limit: int | None = None) -> list[Document]:
        try:
            embeddings = self._build_embeddings()
            if embeddings is None:
                return []

            store_dir = Path(self.settings.vector_store_dir)
            if not store_dir.exists():
                return []

            from langchain_chroma import Chroma

            vector_store = Chroma(
                persist_directory=str(store_dir),
                embedding_function=embeddings,
            )
            return vector_store.similarity_search(query, k=limit or self.settings.top_k)
        except Exception:
            return []

    def is_ready(self) -> bool:
        return Path(self.settings.vector_store_dir).exists()
