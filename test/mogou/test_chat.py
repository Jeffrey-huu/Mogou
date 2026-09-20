from mogou.models.chat import ChatModel
from mogou.services.chat import EchoChatService


def test_chat_model_preserves_roles_and_order() -> None:
    model = ChatModel()
    model.add("user", "你好")
    model.add("assistant", "Echo: 你好")
    assert [(item.role, item.content) for item in model.messages] == [
        ("user", "你好"),
        ("assistant", "Echo: 你好"),
    ]


def test_echo_service_is_deterministic() -> None:
    assert EchoChatService().reply("测试") == "Echo: 测试"
