"""通知通道注册表。"""

from dataclasses import dataclass
from typing import Callable, Iterable

from rainyun.notify.channels import telegram_bot


@dataclass(frozen=True)
class FunctionNotifier:
    name: str
    enabled: Callable[[dict], bool]
    handler: Callable[[str, str], None]

    def is_enabled(self, config: dict) -> bool:
        return self.enabled(config)

    def send(self, title: str, content: str) -> None:
        self.handler(title, content)


class NotifierRegistry:
    def __init__(self) -> None:
        self._items: list[FunctionNotifier] = []

    def register(self, notifier: FunctionNotifier) -> None:
        self._items.append(notifier)

    def resolve(self, config: dict) -> list[FunctionNotifier]:
        return [notifier for notifier in self._items if notifier.is_enabled(config)]

    def all(self) -> Iterable[FunctionNotifier]:
        return list(self._items)


def build_default_registry() -> NotifierRegistry:
    registry = NotifierRegistry()
    registry.register(
        FunctionNotifier(
            "telegram_bot",
            lambda cfg: bool(cfg.get("TG_BOT_TOKEN") and cfg.get("TG_USER_ID")),
            telegram_bot,
        )
    )
    return registry


DEFAULT_REGISTRY = build_default_registry()
