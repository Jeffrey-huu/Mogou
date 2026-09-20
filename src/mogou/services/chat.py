from typing import Protocol


class ChatService(Protocol):
    def reply(self, message: str) -> str:
        """Return an assistant response for a user message."""


class EchoChatService:
    """Deterministic local placeholder for a future Agent implementation."""

    def reply(self, message: str) -> str:
        return f"Echo: {message}"
