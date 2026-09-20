from typing import Protocol

from mogou.models.chat import ChatModel
from mogou.services.chat import ChatService


class ChatView(Protocol):
    def chat_input_text(self) -> str: ...
    def clear_chat_input(self) -> None: ...
    def append_chat_message(self, role: str, content: str) -> None: ...


class ChatController:
    def __init__(self, model: ChatModel, service: ChatService, view: ChatView) -> None:
        self.model = model
        self.service = service
        self.view = view

    def send_message(self) -> bool:
        content = self.view.chat_input_text().strip()
        if not content:
            return False
        self.model.add("user", content)
        self.view.append_chat_message("user", content)
        self.view.clear_chat_input()
        response = self.service.reply(content)
        self.model.add("assistant", response)
        self.view.append_chat_message("assistant", response)
        return True
