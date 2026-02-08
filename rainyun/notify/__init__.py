"""通知入口与发送编排。"""

import logging
import re
import threading

from rainyun.notify.registry import DEFAULT_REGISTRY
from rainyun.notify.state import (
    configure,
    ensure_loaded,
    get_channels,
    get_skip_title,
    push_config,
    use_temp_config,
)

logger = logging.getLogger(__name__)


def _compose_content(base_content: str, _config: dict) -> str:
    return base_content


def _dispatch(title: str, content: str, config: dict, warn_on_empty: bool = True) -> None:
    with use_temp_config(config, ignore_default_config=True):
        notifiers = DEFAULT_REGISTRY.resolve(push_config)
        if not notifiers:
            if warn_on_empty:
                logger.warning("无有效推送渠道，请检查通知变量是否正确")
            return

        def safe_run(notifier) -> None:
            try:
                notifier.send(title, content)
            except Exception as e:
                logger.error(f"{notifier.name} 线程执行崩溃: {e}")

        threads = [
            threading.Thread(target=safe_run, args=(notifier,), name=notifier.name)
            for notifier in notifiers
        ]
        [thread.start() for thread in threads]
        [thread.join() for thread in threads]


def send(title: str, content: str, ignore_default_config: bool = False, **kwargs) -> None:
    ensure_loaded()

    if not content:
        logger.warning(f"{title} 推送内容为空！")
        return

    skip_title = get_skip_title()
    if skip_title and title in re.split("\n", skip_title):
        logger.info(f"{title} 在SKIP_PUSH_TITLE环境变量内，跳过推送！")
        return

    base_config = {} if ignore_default_config else push_config.copy()
    if kwargs:
        base_config.update(kwargs)

    if ignore_default_config or kwargs:
        _dispatch(title, _compose_content(content, base_config), base_config)
        return

    channels = get_channels()
    if channels:
        used_keys: set[str] = set()
        for channel in channels:
            if not isinstance(channel, dict):
                continue
            if channel.get("enabled") is False:
                continue
            channel_config = channel.get("config")
            if not isinstance(channel_config, dict):
                channel_config = {}
            config = {k: v for k, v in channel_config.items() if isinstance(k, str)}
            if not config:
                name = channel.get("name") or channel.get("type") or "未知渠道"
                logger.warning("通知渠道配置无效: %s", name)
                continue
            used_keys.update(config.keys())
            if not DEFAULT_REGISTRY.resolve(config):
                name = channel.get("name") or channel.get("type") or "未知渠道"
                logger.warning("通知渠道配置无效: %s", name)
                continue
            _dispatch(title, _compose_content(content, config), config, warn_on_empty=False)
        extra_config = {k: v for k, v in push_config.items() if k not in used_keys}
        if extra_config:
            _dispatch(title, _compose_content(content, extra_config), extra_config, warn_on_empty=False)
        return

    _dispatch(title, _compose_content(content, base_config), base_config)


__all__ = ["configure", "send"]
