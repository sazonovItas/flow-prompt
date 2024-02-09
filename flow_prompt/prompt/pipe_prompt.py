import logging
from copy import deepcopy
from dataclasses import dataclass

from flow_prompt import settings
from flow_prompt.ai_models.attempt_to_call import AttemptToCall
from flow_prompt.prompt.base_prompt import BasePrompt
from flow_prompt.prompt.chat import ChatsEntity
from flow_prompt.prompt.user_prompt import UserPrompt
from flow_prompt.settings import PIPE_PROMPTS

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class PipePrompt(BasePrompt):
    """
    PipePrompt is a class that represents a pipe of chats that will be used to generate a prompt.
    You can add chats with different priorities to the pipe thinking just about the order of chats.
    When you initialize a Prompt, chats will be sorted by priority and then by order of adding.
    """

    id: str
    max_tokens: int = None
    min_sample_tokens: int = settings.DEFAULT_SAMPLE_MIN_BUDGET
    max_sample_tokens: int = None

    def __post_init__(self):
        PIPE_PROMPTS[self.id] = self

    def get_max_tokens(self, ai_attempt: AttemptToCall) -> int:
        if self.max_tokens:
            return min(self.max_tokens, ai_attempt.model_max_tokens())
        return ai_attempt.model_max_tokens()

    def create_prompt(self, ai_attempt: AttemptToCall) -> UserPrompt:
        logger.debug(
            f"Creating prompt for {ai_attempt.ai_model} with {ai_attempt.attempt_number} attempt"
            f"Encoding {ai_attempt.tiktoken_encoding()}"
        )
        return UserPrompt(
            pipe=deepcopy(self.pipe),
            priorities=deepcopy(self.priorities),
            tiktoken_encoding=ai_attempt.tiktoken_encoding(),
            model_max_tokens=self.get_max_tokens(ai_attempt),
            min_sample_tokens=self.min_sample_tokens,
            max_sample_tokens=self.max_sample_tokens,
        )

    def dump(self) -> dict:
        return {
            "id": self.id,
            "max_tokens": self.max_tokens,
            "min_sample_tokens": self.min_sample_tokens,
            "max_sample_tokens": self.max_sample_tokens,
            "priorities": {
                priority: [chats_value.dump() for chats_value in chats_values]
                for priority, chats_values in self.priorities.items()
            },
            "pipe": self.pipe,
        }

    @classmethod
    def load(cls, data):
        priorities = {}
        for priority, chat_values in data["priorities"].items():
            priorities[int(priority)] = [
                ChatsEntity.load(chat_value) for chat_value in chat_values
            ]
        return cls(
            id=data["id"],
            max_tokens=data["max_tokens"],
            min_sample_tokens=data.get("min_sample_tokens"),
            max_sample_tokens=data.get("max_sample_tokens"),
            priorities=priorities,
            pipe=data["pipe"],
        )
