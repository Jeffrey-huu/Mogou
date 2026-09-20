from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


class ChatModel:
    """In-memory conversation state; it intentionally has no persistence."""

    def __init__(self) -> None:
        self.messages: list[ChatMessage] = []

    def add(self, role: str, content: str) -> ChatMessage:
        message = ChatMessage(role=role, content=content)
        self.messages.append(message)
        return message
