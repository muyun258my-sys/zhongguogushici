from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.config import Settings
from app.prompts import SYSTEM_PROMPT
from app.rag.repository import (
    get_poem_by_id,
    list_titles_by_author,
    render_poem_context,
    search_by_tags,
    search_exact,
)
from app.rag.vectorstore import PoetryVectorStore


class PoetryAssistantService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.vector_store = PoetryVectorStore(settings)
        self.history: dict[str, list[dict[str, str]]] = defaultdict(list)

    def answer(self, question: str, session_id: str) -> dict[str, Any]:
        question_type = self._classify_question(question)
        contexts = self._collect_contexts(question, question_type)
        answer = self._generate_answer(question, question_type, session_id, contexts)
        self._append_history(session_id, "user", question)
        self._append_history(session_id, "assistant", answer)

        return {
            "answer": answer,
            "question_type": question_type,
            "used_llm": self.settings.llm_enabled,
            "sources": [
                {
                    "title": item["title"],
                    "author": item["author"],
                    "dynasty": item["dynasty"],
                    "source": item.get("source", "未知来源"),
                }
                for item in contexts
            ],
            "contexts": contexts,
        }

    def auto_ingest(self) -> bool:
        return self.vector_store.ingest(reset=False)

    def vector_store_ready(self) -> bool:
        return self.vector_store.is_ready()

    def _append_history(self, session_id: str, role: str, content: str) -> None:
        self.history[session_id].append({"role": role, "content": content})
        self.history[session_id] = self.history[session_id][-6:]

    def _render_history(self, session_id: str) -> str:
        messages = self.history.get(session_id, [])
        if not messages:
            return "暂无历史对话。"
        return "\n".join(f"{item['role']}: {item['content']}" for item in messages)

    def _classify_question(self, question: str) -> str:
        if self._extract_author_for_title_list(question):
            return "author_titles"
        if any(keyword in question for keyword in ["推荐", "类似", "还有哪些", "适合", "主题"]):
            return "recommend"
        if any(keyword in question for keyword in ["赏析", "解析", "怎么理解", "什么意思", "解释"]):
            return "analysis"
        if any(keyword in question for keyword in ["区别", "比较", "对比", "异同"]):
            return "compare"
        if any(keyword in question for keyword in ["谁写的", "作者", "朝代", "哪首", "出自"]):
            return "lookup"
        return "general"

    def _extract_author_for_title_list(self, question: str) -> str:
        patterns = [
            r"([\u4e00-\u9fff]{2,4})的(?:诗词|诗|词|作品)(?:有)?哪些",
            r"([\u4e00-\u9fff]{2,4})(?:写过|有哪些)(?:诗词|诗|词|作品)",
        ]
        for pattern in patterns:
            match = re.search(pattern, question)
            if match:
                return match.group(1)
        return ""

    def _collect_contexts(self, question: str, question_type: str) -> list[dict[str, Any]]:
        dedup: dict[str, dict[str, Any]] = {}

        for poem in search_exact(question):
            dedup[poem["id"]] = poem

        if question_type == "recommend":
            for poem in search_by_tags(question, limit=self.settings.top_k):
                dedup.setdefault(poem["id"], poem)

        for document in self.vector_store.similarity_search(question, limit=self.settings.top_k):
            poem_id = document.metadata.get("poem_id")
            if not poem_id:
                continue
            poem = get_poem_by_id(poem_id)
            if poem:
                dedup.setdefault(poem["id"], poem)

        return list(dedup.values())[: self.settings.top_k]

    def _generate_answer(
        self,
        question: str,
        question_type: str,
        session_id: str,
        contexts: list[dict[str, Any]],
    ) -> str:
        if question_type == "author_titles":
            return self._generate_author_titles_answer(question)
        if self.settings.llm_enabled:
            llm_answer = self._generate_with_llm(question, question_type, session_id, contexts)
            if llm_answer:
                return llm_answer
        return self._generate_fallback(question, question_type, contexts)

    def _generate_author_titles_answer(self, question: str) -> str:
        author = self._extract_author_for_title_list(question)
        titles = list_titles_by_author(author, limit=20)
        if not titles:
            return ""
        return "\n".join(f"《{title}》" for title in titles)

    def _generate_with_llm(
        self,
        question: str,
        question_type: str,
        session_id: str,
        contexts: list[dict[str, Any]],
    ) -> str:
        from langchain_openai import ChatOpenAI

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                (
                    "human",
                    "最近对话：\n{history}\n\n问题类型：{question_type}\n\n参考资料：\n{context}\n\n用户问题：{question}",
                ),
            ]
        )

        llm_kwargs = {
            "model": self.settings.llm_model_name,
            "temperature": 0.2,
            "api_key": self.settings.openai_api_key,
        }
        if self.settings.openai_base_url:
            llm_kwargs["base_url"] = self.settings.openai_base_url

        llm = ChatOpenAI(**llm_kwargs)
        chain = prompt | llm | StrOutputParser()
        context_text = "\n\n---\n\n".join(render_poem_context(item) for item in contexts) or "暂无命中资料。"
        try:
            return chain.invoke(
                {
                    "history": self._render_history(session_id),
                    "question_type": question_type,
                    "context": context_text,
                    "question": question,
                }
            )
        except Exception:
            return ""

    def _generate_fallback(
        self,
        question: str,
        question_type: str,
        contexts: list[dict[str, Any]],
    ) -> str:
        if not contexts:
            return "根据当前内置知识库，暂时没有检索到足够信息。你可以换一种问法，或者补充作品名、作者、主题关键词。"

        if question_type == "recommend":
            lines = ["可以先读下面这几首："]
            for poem in contexts[:3]:
                lines.append(
                    f"《{poem['title']}》- {poem['author']}（{poem['dynasty']}），主题标签：{'、'.join(poem.get('tags', []))}"
                )
            lines.append("如果你愿意，我还可以继续按思乡、月夜、送别、边塞这些细分主题继续推荐。")
            return "\n".join(lines)

        if question_type == "compare" and len(contexts) >= 2:
            first, second = contexts[0], contexts[1]
            return (
                f"可以先从风格上做一个简要对比：\n"
                f"《{first['title']}》侧重{first.get('appreciation', '情感表达')}；\n"
                f"《{second['title']}》则更突出{second.get('appreciation', '意境描写')}。\n"
                f"如果你想要更准确的对比，建议直接指定两位作者或两首作品。"
            )

        poem = contexts[0]
        return (
            f"结论：这个问题可以先参考《{poem['title']}》这首作品。\n"
            f"作者：{poem['author']}，朝代：{poem['dynasty']}。\n"
            f"正文：{poem['content']}\n"
            f"译文：{poem.get('translation', '暂无')}\n"
            f"赏析：{poem.get('appreciation', '暂无')}"
        )
