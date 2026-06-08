import hashlib
import base64
import mimetypes
import re

import requests
from requests import HTTPError
from flask import current_app


class AIService:
    def __init__(self):
        self.base_url = current_app.config["AI_BASE_URL"]
        self.api_key = current_app.config["AI_API_KEY"]
        self.chat_base_url = current_app.config["CHAT_BASE_URL"]
        self.chat_api_key = current_app.config["CHAT_API_KEY"]
        self.chat_model = current_app.config["CHAT_MODEL"]
        self.chat_wire_api = current_app.config["CHAT_WIRE_API"]
        self.chat_reasoning_effort = current_app.config["CHAT_REASONING_EFFORT"]
        self.chat_disable_response_storage = current_app.config["CHAT_DISABLE_RESPONSE_STORAGE"]
        self.text_embedding_base_url = current_app.config["TEXT_EMBEDDING_BASE_URL"]
        self.text_embedding_api_key = current_app.config["TEXT_EMBEDDING_API_KEY"]
        self.embedding_model = current_app.config["EMBEDDING_MODEL"]
        self.multimodal_embedding_url = current_app.config["MULTIMODAL_EMBEDDING_URL"]
        self.multimodal_embedding_api_key = current_app.config["MULTIMODAL_EMBEDDING_API_KEY"]
        self.multimodal_embedding_model = current_app.config["MULTIMODAL_EMBEDDING_MODEL"]
        self.multimodal_embedding_dimension = current_app.config["MULTIMODAL_EMBEDDING_DIMENSION"]

    @property
    def enabled(self):
        return bool(self.chat_base_url and self.chat_api_key)

    @property
    def text_embedding_enabled(self):
        return bool(self.text_embedding_base_url and self.text_embedding_api_key)

    def summarize(self, text):
        text = text.strip()
        if not text:
            return ""
        if not self.enabled:
            return self._fallback_summary(text)

        prompt = (
            "请为以下学习资料生成一段不超过180字的中文摘要，突出核心知识点：\n\n"
            f"{text[:6000]}"
        )
        return self.chat(prompt)

    def extract_keywords(self, text, limit=8):
        if not text.strip():
            return []
        if not self.enabled:
            return self._fallback_keywords(text, limit)

        prompt = (
            f"请从以下学习资料中提取{limit}个中文关键词，只返回用逗号分隔的关键词：\n\n"
            f"{text[:5000]}"
        )
        raw = self.chat(prompt)
        keywords = re.split(r"[,，、\n]", raw)
        return [item.strip() for item in keywords if item.strip()][:limit]

    def answer(self, question, contexts, conversation=None):
        text_contexts = [item for item in contexts if item.get("type", "text") == "text"][:5]
        image_contexts = [item for item in contexts if item.get("type") == "image"][:3]
        context_text = "\n\n".join(
            f"[文本资料{i + 1}]\n{item['content'][:1200]}" for i, item in enumerate(text_contexts)
        )
        visual_text = "\n".join(
            (
                f"[视觉资料{i + 1}] {item.get('title', '')}"
                f" 第{item.get('page_number') or item.get('asset_index', 0) + 1}项："
                f"{item.get('caption', '')}"
            )
            for i, item in enumerate(image_contexts)
        )
        conversation_text = self._format_conversation(conversation or [])
        prompt = (
            "你是个人学习助手。请优先根据提供的学习资料回答用户问题。"
            "如果资料中没有相关内容，请明确说明“资料中未找到直接依据”，再给出通用解释。\n\n"
            f"{conversation_text}\n\n{context_text}\n\n{visual_text}\n\n用户问题：{question}"
        )
        if self.enabled:
            return self.chat(prompt)
        return self._fallback_answer(question, contexts)

    def chat(self, prompt):
        if not self.enabled:
            return self._fallback_summary(prompt)

        if self.chat_wire_api == "responses":
            return self._responses_chat(prompt)
        return self._chat_completions_chat(prompt)

    def _chat_completions_chat(self, prompt):
        url = f"{self.chat_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.chat_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.chat_model,
            "messages": [
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        self._raise_for_status(response)
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    def _responses_chat(self, prompt):
        url = f"{self.chat_base_url}/responses"
        headers = {
            "Authorization": f"Bearer {self.chat_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.chat_model,
            "instructions": self._system_prompt(),
            "input": prompt,
            "reasoning": {"effort": self.chat_reasoning_effort},
            "store": not self.chat_disable_response_storage,
        }
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        self._raise_for_status(response)
        data = response.json()
        return self._extract_responses_text(data)

    def _extract_responses_text(self, data):
        if data.get("output_text"):
            return data["output_text"].strip()
        parts = []
        for item in data.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    parts.append(content["text"])
        if parts:
            return "\n".join(parts).strip()
        raise ValueError("Responses API 未返回文本内容")

    def _system_prompt(self):
        return (
            "你是一个简洁、可靠的个人学习助手。"
            f"当前后端配置的问答模型名称是 {self.chat_model}。"
            "如果用户问你使用的模型，可以如实说明该配置名称，但不要声称知道供应商内部真实模型。"
        )

    def _format_conversation(self, conversation):
        if not conversation:
            return ""
        lines = ["[最近对话上下文]"]
        for item in conversation[-8:]:
            role = item.get("role")
            content = (item.get("content") or "").strip()
            if not content:
                continue
            label = "用户" if role == "user" else "助手"
            lines.append(f"{label}：{content[:800]}")
        return "\n".join(lines)

    def embed(self, text):
        if self.embedding_model == self.multimodal_embedding_model:
            return self.embed_multimodal_text(text)
        if self.text_embedding_enabled:
            url = f"{self.text_embedding_base_url}/embeddings"
            headers = {
                "Authorization": f"Bearer {self.text_embedding_api_key}",
                "Content-Type": "application/json",
            }
            payload = {"model": self.embedding_model, "input": text}
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            self._raise_for_status(response)
            data = response.json()
            return data["data"][0]["embedding"]
        return self._hash_embedding(text)

    @property
    def multimodal_enabled(self):
        return bool(
            current_app.config["MULTIMODAL_RAG_ENABLED"]
            and self.multimodal_embedding_url
            and self.multimodal_embedding_api_key
        )

    def embed_multimodal_text(self, text):
        if self.multimodal_enabled:
            return self._dashscope_multimodal_embed({"text": text})
        return self._hash_embedding(text, self.multimodal_embedding_dimension)

    def embed_multimodal_image(self, image_path):
        if self.multimodal_enabled:
            data_uri = self._image_to_data_uri(image_path)
            return self._dashscope_multimodal_embed({"image": data_uri})
        return self._hash_embedding(str(image_path), self.multimodal_embedding_dimension)

    def _dashscope_multimodal_embed(self, factor):
        headers = {
            "Authorization": f"Bearer {self.multimodal_embedding_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.multimodal_embedding_model,
            "input": {"contents": [factor]},
            "parameters": {"dimension": self.multimodal_embedding_dimension},
        }
        response = requests.post(
            self.multimodal_embedding_url,
            headers=headers,
            json=payload,
            timeout=90,
        )
        self._raise_for_status(response)
        data = response.json()
        embeddings = data.get("output", {}).get("embeddings") or data.get("embeddings") or []
        if not embeddings:
            raise ValueError("多模态 embedding 接口未返回向量")
        first = embeddings[0]
        return first.get("embedding") if isinstance(first, dict) else first

    def _image_to_data_uri(self, image_path):
        mime_type = mimetypes.guess_type(str(image_path))[0] or "image/png"
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _raise_for_status(self, response):
        try:
            response.raise_for_status()
        except HTTPError as exc:
            detail = response.text[:800].replace("\n", " ")
            raise ValueError(f"{response.status_code} {response.reason}: {detail}") from exc

    def _fallback_summary(self, text):
        cleaned = re.sub(r"\s+", " ", text).strip()
        return cleaned[:180] + ("..." if len(cleaned) > 180 else "")

    def _fallback_keywords(self, text, limit):
        words = re.findall(r"[\u4e00-\u9fa5]{2,}|[A-Za-z][A-Za-z0-9_+-]{2,}", text)
        stop_words = {"学习", "资料", "内容", "知识", "系统", "用户", "进行", "可以", "需要"}
        scores = {}
        for word in words:
            if word in stop_words:
                continue
            scores[word] = scores.get(word, 0) + 1
        return [item[0] for item in sorted(scores.items(), key=lambda pair: pair[1], reverse=True)[:limit]]

    def _fallback_answer(self, question, contexts):
        if not contexts:
            return "资料中未找到直接依据。请先上传并处理学习资料，或换一个更具体的问题。"
        snippets = "\n".join(f"- {item['content'][:160]}" for item in contexts[:3])
        return (
            "当前未配置 AI API，以下是根据检索到的资料片段整理的参考回答：\n"
            f"问题：{question}\n"
            f"相关资料：\n{snippets}"
        )

    def _hash_embedding(self, text, dimensions=64):
        values = []
        for index in range(dimensions):
            digest = hashlib.sha256(f"{index}:{text}".encode("utf-8")).digest()
            value = int.from_bytes(digest[:4], "big") / 2**32
            values.append(value * 2 - 1)
        return values
