import os

from dotenv import find_dotenv, load_dotenv
from openai import AsyncOpenAI
from typing import Any
from openai.types.chat import ChatCompletionMessageParam

load_dotenv(find_dotenv())

SYSTEM_PROMPT = """
你是MyJARVIS，一个AI个人决策和成长顾问。

你的职责是帮助用户分析问题、制定计划、复盘行动并帮助用户持续成长
回答时应结合用户提供的信息，尽量具体、清晰、可执行。
如果缺少必要信息，不要编造用户的个人情况
"""


async def generate_reply(
        messages: list[ChatCompletionMessageParam],
)->str:
    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        raise RuntimeError(
            "未配置 DEEPSEEK_API_KEY，请检查您的API_KEY配置"
        )
    base_url = os.getenv(
        "LLM_BASE_URL",
        "https://api.deepseek.com",
    )
    model = os.getenv(
        "LLM_MODEL_ID",
        "deepseek-flash",
    )

    async with AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=60.0,
        max_retries=1,
    ) as client:
        request_messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *messages,
        ]

        response = await client.chat.completions.create(
            model=model,
            messages=request_messages,
            stream=False,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError("大模型返回了空回复")

        return content