# interfaces for LLM adapter
# must have functions:
#   - chat completion -> returns object message: [ tool calls []: [function name, function argument],  content ]


from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from openai import OpenAI


@dataclass
class LLMMessage:
    role: str
    content: Optional[str]
    tool_calls: Optional[List[Any]] = None


class LLMClient(ABC):
    @abstractmethod
    def chat(
        self, messages: List[Dict[str, str]], tools: Any, tool_choice: Any
    ) -> LLMMessage:
        """Send a chat API call and return an LLMMessage."""
        pass


# OpenAI adapter
class OpenAIAdapter(LLMClient):
    def __init__(self, model: str, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def chat(self, messages: List[Dict[str, str]], tools: Any, tool_choice: Any):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )

        msg = response.choices[0].message

        return LLMMessage(
            role=msg.role,
            content=msg.content,
            tool_calls=msg.tool_calls,
        )
