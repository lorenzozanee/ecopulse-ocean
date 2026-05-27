"""Multi-provider LLM client — Claude + OpenAI with factory pattern."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


class LLMClient(Protocol):
    def generate(self, prompt: str) -> str: ...


@dataclass(frozen=True)
class ClaudeClient:
    model: str = "claude-sonnet-4-6"
    temperature: float = 0.3
    max_tokens: int = 800

    def generate(self, prompt: str) -> str:
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError(
                "anthropic package required. Install with: pip install earthreport[llm]"
            )
        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        msg = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text


@dataclass(frozen=True)
class OpenAIClient:
    model: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int = 800

    def generate(self, prompt: str) -> str:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package required. Install with: pip install earthreport[llm]"
            )
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
        resp = client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content or ""


@dataclass(frozen=True)
class MockClient:
    """Deterministic placeholder text for testing and offline use."""

    def generate(self, prompt: str) -> str:
        if "碳汇效率" in prompt or "碳泵" in prompt:
            return (
                "该海域碳汇效率处于较高水平，微生物碳泵活性强，有机碳沉降通量显著高于全球均值。"
                "当前季节的浮游植物水华正在通过生物泵机制将大量有机碳输送至深层，"
                "对区域碳封存具有积极贡献。"
            )
        if "热浪" in prompt or "MHW" in prompt:
            return (
                "当前海表温度距平接近但尚未突破海洋热浪阈值。"
                "若增温趋势持续，未来7天内约有三分之一概率触发轻度热浪事件。"
                "建议持续监测珊瑚礁区域，关注温度异常对浮游植物群落结构的潜在影响。"
            )
        if "多样性" in prompt or "变异系数" in prompt:
            return (
                "叶绿素-a变异系数处于中等水平，表明浮游植物群落多样性正常。"
                "温跃层梯度稳定，深层营养盐供给规律，未检测到异常藻华信号。"
                "生态系统处于健康波动范围。"
            )
        if "传感器" in prompt or "RLC" in prompt or "信号" in prompt:
            return (
                "AI降噪模块成功将传感器本底噪声压缩至原有水平的五分之一。"
                "检测到清晰的昼夜振荡模式，与浮游植物光合-呼吸周期一致，"
                "叠加半日潮周期的浊度波动。信号质量已满足微生物代谢速率定量推断要求。"
            )
        return "数据正常，未检测到异常信号。"


def get_llm(provider: str = "mock") -> LLMClient:
    providers: dict[str, LLMClient] = {
        "claude": ClaudeClient(),
        "openai": OpenAIClient(),
        "mock": MockClient(),
    }
    if provider not in providers:
        raise ValueError(f"Unknown LLM provider: {provider}. Available: {list(providers)}")
    return providers[provider]
