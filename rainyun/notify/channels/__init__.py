"""通知渠道实现（仅保留 Telegram）。"""
import logging

from rainyun.notify.state import push_config
from rainyun.utils.http import post_with_retry

logger = logging.getLogger(__name__)


def telegram_bot(title: str, content: str) -> None:
    """
    使用 telegram 机器人 推送消息。
    """
    if not push_config.get("TG_BOT_TOKEN") or not push_config.get("TG_USER_ID"):
        return
    logger.info("tg 服务启动")

    if push_config.get("TG_API_HOST"):
        url = f"{push_config.get('TG_API_HOST')}/bot{push_config.get('TG_BOT_TOKEN')}/sendMessage"
    else:
        url = f"https://api.telegram.org/bot{push_config.get('TG_BOT_TOKEN')}/sendMessage"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "chat_id": str(push_config.get("TG_USER_ID")),
        "text": f"{title}\n\n{content}",
        "disable_web_page_preview": "true",
    }
    proxies = None
    if push_config.get("TG_PROXY_HOST") and push_config.get("TG_PROXY_PORT"):
        if push_config.get("TG_PROXY_AUTH") is not None and "@" not in push_config.get(
            "TG_PROXY_HOST"
        ):
            push_config["TG_PROXY_HOST"] = (
                push_config.get("TG_PROXY_AUTH")
                + "@"
                + push_config.get("TG_PROXY_HOST")
            )
        proxy_str = "http://{}:{}".format(
            push_config.get("TG_PROXY_HOST"), push_config.get("TG_PROXY_PORT")
        )
        proxies = {"http": proxy_str, "https": proxy_str}
    try:
        response = post_with_retry(
            url=url, headers=headers, params=payload, proxies=proxies, timeout=15
        ).json()

        if response.get("ok"):
            logger.info("tg 推送成功！")
        else:
            logger.error(f"tg 推送失败！响应: {response}")
    except Exception as exc:
        logger.error(f"tg 推送异常: {exc}")
