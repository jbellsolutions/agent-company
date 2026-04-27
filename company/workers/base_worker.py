from __future__ import annotations

import os
from abc import ABC, abstractmethod

from openai import OpenAI

DEEPSEEK = "deepseek/deepseek-v4-flash"


class BaseWorker(ABC):
    """
    DeepSeek-powered worker via OpenRouter. Executes specific tasks.
    ~10x cheaper than Opus/Sonnet for high-volume execution.
    """

    name: str = "base_worker"

    def __init__(self, company_id: int) -> None:
        self.company_id = company_id
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
        )

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    def _call(self, user_message: str, max_tokens: int = 2048) -> str:
        response = self.client.chat.completions.create(
            model=DEEPSEEK,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content or ""

    @abstractmethod
    def run(self, task: str) -> str: ...
