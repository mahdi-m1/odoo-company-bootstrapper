"""مزودو الذكاء الاصطناعي: Claude CLI / Anthropic / OpenAI / Ollama"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """أنت خبير في نظام أودو (Odoo ERP). مهمتك تحويل بيانات الشركة إلى خطة تنفيذ دقيقة عبر XML-RPC.
الشركة في البحرين (BHD, BH). قد يوجد نظام ساعات ومهن ديناميكية.

أعد الرد **فقط** بصيغة JSON صحيحة (بدون markdown):

{
  "summary": "ملخص عربي",
  "estimated_records": عدد,
  "steps": [
    {
      "order": 1,
      "action": "create",
      "model": "res.company",
      "description": "وصف عربي",
      "data": { }
    }
  ]
}

ترتيب مقترح: res.company → فروع → hr.department → hr.job (من المهن) → hr.employee → project.project → product.template
استخدم حقول أودو القياسية فقط. لا نص خارج JSON.
"""


class AIProvider(ABC):
    @abstractmethod
    def generate_plan(self, payload: dict) -> dict:
        pass


class ClaudeCLIProvider(AIProvider):
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.model = model
        if not shutil.which("claude"):
            raise RuntimeError(
                "أمر 'claude' غير موجود. ثبّت Claude CLI:\n"
                "  npm install -g @anthropic-ai/claude-code\n"
                "أو AI_PROVIDER=anthropic مع ANTHROPIC_API_KEY"
            )

    def generate_plan(self, payload: dict) -> dict:
        user_content = (
            "قم بإنشاء خطة تنفيذ لأودو بناءً على البيانات التالية:\n\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
        )
        prompt = f"{SYSTEM_PROMPT}\n\n{user_content}"
        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=180,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Claude CLI فشل: {result.stderr}")
            return self._extract_json(result.stdout.strip())
        except subprocess.TimeoutExpired:
            raise RuntimeError("انتهت مهلة Claude CLI")

    @staticmethod
    def _extract_json(text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            text = "\n".join(lines)
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("لم يتم العثور على JSON في الرد")
        return json.loads(text[start:end])


class AnthropicAPIProvider(AIProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY غير موجود")

    def generate_plan(self, payload: dict) -> dict:
        user_content = (
            "قم بإنشاء خطة تنفيذ لأودو:\n\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
        )
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 8192,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_content}],
                },
            )
            resp.raise_for_status()
            text = resp.json()["content"][0]["text"]
            return ClaudeCLIProvider._extract_json(text)


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY غير موجود")

    def generate_plan(self, payload: dict) -> dict:
        user_content = (
            "قم بإنشاء خطة تنفيذ لأودو:\n\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
        )
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    "temperature": 0.2,
                },
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"]
            return ClaudeCLIProvider._extract_json(text)


class OllamaProvider(AIProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate_plan(self, payload: dict) -> dict:
        user_content = (
            "قم بإنشاء خطة تنفيذ لأودو:\n\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
        )
        with httpx.Client(timeout=180) as client:
            resp = client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    "stream": False,
                    "format": "json",
                },
            )
            resp.raise_for_status()
            return json.loads(resp.json()["message"]["content"])


def get_ai_provider(provider: str = "claude") -> AIProvider:
    provider = provider.lower().strip()
    if provider in ("claude", "claude-cli"):
        return ClaudeCLIProvider()
    if provider in ("anthropic", "claude-api"):
        return AnthropicAPIProvider()
    if provider == "openai":
        return OpenAIProvider()
    if provider == "ollama":
        return OllamaProvider(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        )
    raise ValueError(f"مزود غير مدعوم: {provider}. الخيارات: claude | anthropic | openai | ollama")
