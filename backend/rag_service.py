import logging
import json
import time
from typing import List

from langchain_core.documents import Document
from vector_store import VectorStoreManager
from llm_utils import stream_openrouter_completion

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, index_name: str = "docs-wiki-index", namespace: str = "default_docs"):
        self.vector_store = VectorStoreManager(index_name=index_name)
        self.namespace = namespace

    async def retrieve_documents(self, query: str, top_k: int = 4) -> List[Document]:
        return await self.vector_store.amax_marginal_relevance_search(
            query=query,
            namespace=self.namespace,
            top_k=top_k
        )

    def _build_prompt(self, query: str, context: str) -> str:
        return f"""
        You are a helpful documentation bot. Use the following context to answer the user's question.
        If you don't know the answer, state that you don't know, and do not make up an answer.

        Context:
        {context}

        Question: {query}
        """

    async def stream_chat_response(
        self, query: str, model: str, retrieved_documents: List[Document]
    ):
        context_texts = [doc.page_content for doc in retrieved_documents]
        source_urls = list(set([doc.metadata.get("source", "Unknown Source") for doc in retrieved_documents]))
        context = "\n\n".join(context_texts)

        prompt = self._build_prompt(query, context)

        yield json.dumps({"sources": source_urls}) + "\n"

        async for chunk in stream_openrouter_completion(
            model=model,
            prompt=prompt,
            temperature=0.7,
            max_tokens=1000
        ):
            try:
                chunk_str = chunk.decode('utf-8')
                for line in chunk_str.splitlines():
                    if line.startswith("data:"):
                        data = line[len("data:"):].strip()
                        if data == "[DONE]":
                            continue
                        json_data = json.loads(data)
                        if "choices" in json_data and len(json_data["choices"]) > 0:
                            delta = json_data["choices"][0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yield json.dumps({"answer_chunk": content}) + "\n"
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from chunk: {chunk_str}")
                continue
            except Exception as e:
                logger.error(f"Error processing stream chunk: {e}")
                raise
