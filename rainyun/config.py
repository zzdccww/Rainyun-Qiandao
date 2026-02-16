"""配置定义与解析。"""

import hashlib
import logging
import os
from dataclasses import dataclass, field, replace
from functools import lru_cache
from typing import Any, Mapping

logger = logging.getLogger(__name__)

# fmt: off
DEFAULT_PUSH_CONFIG = {
    'TG_BOT_TOKEN': '',                 # tg 机器人的 TG_BOT_TOKEN
    'TG_USER_ID': '',                   # tg 机器人的 TG_USER_ID
    'TG_API_HOST': '',                  # tg 代理 api
    'TG_PROXY_AUTH': '',                # tg 代理认证参数
    'TG_PROXY_HOST': '',                # tg 机器人的 TG_PROXY_HOST
    'TG_PROXY_PORT': '',                # tg 机器人的 TG_PROXY_PORT
}
# fmt: on


def _read_str(env: Mapping[str, str], name: str, default: str) -> str:
    value = env.get(name)
    if value is None or value == "":
        return default
    return value


def _read_int(env: Mapping[str, str], name: str, default: int) -> int:
    value = env.get(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning(f"Invalid config: {name} must be int, using default {default}")
        return default


def _read_float(env: Mapping[str, str], name: str, default: float) -> float:
    value = env.get(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        logger.warning(f"Invalid config: {name} must be number, using default {default}")
        return default


def _read_bool(env: Mapping[str, str], name: str, default: bool) -> bool:
    value = env.get(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in ("true", "1", "yes", "y", "on")


def _parse_int_list(value: str) -> tuple[list[int], bool]:
    if not value:
        return [], False
    results = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            results.append(int(item))
        except ValueError:
            logger.error("配置错误：RENEW_PRODUCT_IDS 格式无效，应为逗号分隔的数字，自动续费已禁用")
            return [], True
    return results, False


def _coerce_str_value(value: Any, default: str) -> str:
    if isinstance(value, str):
        return value
    return default


def _coerce_bool_value(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "y", "on")
    return default


def _coerce_int_value(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        return default
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
    return default


def _coerce_float_value(value: Any, default: float) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return default
    return default


def _coerce_dict_str_value(value: Any, default: dict[str, str]) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return default
    result: dict[str, str] = {}
    for key, item in value.items():
        if isinstance(key, str) and isinstance(item, str):
            result[key] = item
    return result


def _parse_int_list_from_any(value: Any) -> tuple[list[int], bool]:
    if value is None:
        return [], False
    if isinstance(value, list):
        results: list[int] = []
        for item in value:
            if isinstance(item, int):
                results.append(item)
            elif isinstance(item, str):
                stripped = item.strip()
                if not stripped:
                    continue
                if stripped.isdigit():
                    results.append(int(stripped))
                else:
                    return [], True
            else:
                return [], True
        return results, False
    if isinstance(value, str):
        return _parse_int_list(value)
    return [], True


@dataclass(frozen=True)
class Config:
    app_base_url: str
    api_base_url: str
    app_version: str
    cookie_file: str
    points_to_cny_rate: int
    captcha_retry_limit: int
    captcha_retry_unlimited: bool
    captcha_save_samples: bool
    captcha_icr_enabled: bool
    captcha_icr_rotate_range: int
    captcha_icr_threshold: float
    captcha_min_similarity: float
    captcha_icr_signin_only: bool
    request_timeout: int
    max_retries: int
    retry_delay: float
    download_timeout: int
    download_max_retries: int
    download_retry_delay: float
    chrome_low_memory: bool
    default_renew_cost_7_days: int
    timeout: int
    max_delay: int
    rainyun_user: str
    rainyun_pwd: str
    debug: bool
    linux_mode: bool
    rainyun_api_key: str
    auto_renew: bool
    renew_threshold_days: int
    renew_product_ids: list[int]
    renew_product_ids_parse_error: bool
    chrome_bin: str
    chromedriver_path: str
    skip_push_title: str
    push_config: dict[str, str] = field(default_factory=dict)
    notify_channels: list[dict[str, Any]] = field(default_factory=list)
    display_name: str = ""

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Config":
        if env is None:
            env = os.environ

        app_base_url = _read_str(env, "APP_BASE_URL", "https://app.rainyun.com").rstrip("/")
        api_base_url = _read_str(env, "API_BASE_URL", "https://api.v2.rainyun.com").rstrip("/")
        app_version = _read_str(env, "APP_VERSION", "3.0")
        cookie_file = _read_str(env, "COOKIE_FILE", "data/cookies/cookies.json")

        points_to_cny_rate = 2000
        captcha_retry_limit = 5
        captcha_retry_unlimited = False
        captcha_save_samples = False
        captcha_icr_enabled = _read_bool(env, "CAPTCHA_ICR_ENABLED", False)
        captcha_icr_rotate_range = _read_int(env, "CAPTCHA_ICR_ROTATE_RANGE", 45)
        captcha_icr_threshold = _read_float(env, "CAPTCHA_ICR_THRESHOLD", 0.35)
        captcha_min_similarity = _read_float(env, "CAPTCHA_MIN_SIMILARITY", 0.25)
        captcha_icr_signin_only = _read_bool(env, "CAPTCHA_ICR_SIGNIN_ONLY", True)

        request_timeout = 15
        max_retries = 3
        retry_delay = 2.0

        download_timeout = 10
        download_max_retries = 3
        download_retry_delay = 2.0

        chrome_low_memory = _read_bool(env, "CHROME_LOW_MEMORY", False)
        default_renew_cost_7_days = 2258

        timeout = 15
        max_delay = 90
        rainyun_user = ""
        rainyun_pwd = ""
        debug = False
        linux_mode = _read_bool(env, "LINUX_MODE", True)
        rainyun_api_key = ""

        auto_renew = True
        renew_threshold_days = 7
        renew_product_ids = []
        renew_product_ids_parse_error = False

        chrome_bin = _read_str(env, "CHROME_BIN", "")
        chromedriver_path = _read_str(env, "CHROMEDRIVER_PATH", "/usr/local/bin/chromedriver")
        skip_push_title = ""

        push_config = DEFAULT_PUSH_CONFIG.copy()

        return cls(
            app_base_url=app_base_url,
            api_base_url=api_base_url,
            app_version=app_version,
            cookie_file=cookie_file,
            points_to_cny_rate=points_to_cny_rate,
            captcha_retry_limit=captcha_retry_limit,
            captcha_retry_unlimited=captcha_retry_unlimited,
            captcha_save_samples=captcha_save_samples,
            captcha_icr_enabled=captcha_icr_enabled,
            captcha_icr_rotate_range=captcha_icr_rotate_range,
            captcha_icr_threshold=captcha_icr_threshold,
            captcha_min_similarity=captcha_min_similarity,
            captcha_icr_signin_only=captcha_icr_signin_only,
            request_timeout=request_timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            download_timeout=download_timeout,
            download_max_retries=download_max_retries,
            download_retry_delay=download_retry_delay,
            chrome_low_memory=chrome_low_memory,
            default_renew_cost_7_days=default_renew_cost_7_days,
            timeout=timeout,
            max_delay=max_delay,
            rainyun_user=rainyun_user,
            rainyun_pwd=rainyun_pwd,
            debug=debug,
            linux_mode=linux_mode,
            rainyun_api_key=rainyun_api_key,
            auto_renew=auto_renew,
            renew_threshold_days=renew_threshold_days,
            renew_product_ids=renew_product_ids,
            renew_product_ids_parse_error=renew_product_ids_parse_error,
            chrome_bin=chrome_bin,
            chromedriver_path=chromedriver_path,
            skip_push_title=skip_push_title,
            push_config=push_config,
            notify_channels=[],
            display_name="",
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "Config":
        payload = data if isinstance(data, Mapping) else {}
        base = cls.from_env({})

        app_base_url = _coerce_str_value(payload.get("app_base_url"), base.app_base_url).rstrip("/")
        api_base_url = _coerce_str_value(payload.get("api_base_url"), base.api_base_url).rstrip("/")
        app_version = _coerce_str_value(payload.get("app_version"), base.app_version)
        cookie_file = _coerce_str_value(payload.get("cookie_file"), base.cookie_file)

        points_to_cny_rate = _coerce_int_value(payload.get("points_to_cny_rate"), base.points_to_cny_rate)
        captcha_retry_limit = _coerce_int_value(payload.get("captcha_retry_limit"), base.captcha_retry_limit)
        captcha_retry_unlimited = _coerce_bool_value(
            payload.get("captcha_retry_unlimited"), base.captcha_retry_unlimited
        )
        captcha_save_samples = _coerce_bool_value(payload.get("captcha_save_samples"), base.captcha_save_samples)
        captcha_icr_enabled = _coerce_bool_value(payload.get("captcha_icr_enabled"), base.captcha_icr_enabled)
        captcha_icr_rotate_range = _coerce_int_value(
            payload.get("captcha_icr_rotate_range"), base.captcha_icr_rotate_range
        )
        captcha_icr_threshold = _coerce_float_value(
            payload.get("captcha_icr_threshold"), base.captcha_icr_threshold
        )
        captcha_min_similarity = _coerce_float_value(
            payload.get("captcha_min_similarity"), base.captcha_min_similarity
        )
        captcha_icr_signin_only = _coerce_bool_value(
            payload.get("captcha_icr_signin_only"), base.captcha_icr_signin_only
        )

        request_timeout = _coerce_int_value(payload.get("request_timeout"), base.request_timeout)
        max_retries = _coerce_int_value(payload.get("max_retries"), base.max_retries)
        retry_delay = _coerce_float_value(payload.get("retry_delay"), base.retry_delay)

        download_timeout = _coerce_int_value(payload.get("download_timeout"), base.download_timeout)
        download_max_retries = _coerce_int_value(payload.get("download_max_retries"), base.download_max_retries)
        download_retry_delay = _coerce_float_value(payload.get("download_retry_delay"), base.download_retry_delay)

        chrome_low_memory = _coerce_bool_value(payload.get("chrome_low_memory"), base.chrome_low_memory)
        default_renew_cost_7_days = _coerce_int_value(
            payload.get("default_renew_cost_7_days"), base.default_renew_cost_7_days
        )

        timeout = _coerce_int_value(payload.get("timeout"), base.timeout)
        max_delay = _coerce_int_value(payload.get("max_delay"), base.max_delay)
        rainyun_user = _coerce_str_value(payload.get("rainyun_user"), base.rainyun_user)
        rainyun_pwd = _coerce_str_value(payload.get("rainyun_pwd"), base.rainyun_pwd)
        debug = _coerce_bool_value(payload.get("debug"), base.debug)
        linux_mode = _coerce_bool_value(payload.get("linux_mode"), base.linux_mode)
        rainyun_api_key = _coerce_str_value(payload.get("rainyun_api_key"), base.rainyun_api_key)

        auto_renew = _coerce_bool_value(payload.get("auto_renew"), base.auto_renew)
        renew_threshold_days = _coerce_int_value(
            payload.get("renew_threshold_days"), base.renew_threshold_days
        )

        renew_product_ids_parse_error = False
        if "renew_product_ids" in payload:
            renew_product_ids, renew_product_ids_parse_error = _parse_int_list_from_any(
                payload.get("renew_product_ids")
            )
            if renew_product_ids_parse_error:
                renew_product_ids = base.renew_product_ids
        else:
            renew_product_ids = base.renew_product_ids

        chrome_bin = _coerce_str_value(payload.get("chrome_bin"), base.chrome_bin)
        chromedriver_path = _coerce_str_value(payload.get("chromedriver_path"), base.chromedriver_path)
        skip_push_title = _coerce_str_value(payload.get("skip_push_title"), base.skip_push_title)

        push_config = base.push_config.copy()
        notify_channels: list[dict[str, Any]] = []
        if "push_config" in payload:
            push_config.update(_coerce_dict_str_value(payload.get("push_config"), {}))
        raw_channels = payload.get("notify_channels")
        if isinstance(raw_channels, list):
            notify_channels = [dict(item) for item in raw_channels if isinstance(item, Mapping)]

        return cls(
            app_base_url=app_base_url,
            api_base_url=api_base_url,
            app_version=app_version,
            cookie_file=cookie_file,
            points_to_cny_rate=points_to_cny_rate,
            captcha_retry_limit=captcha_retry_limit,
            captcha_retry_unlimited=captcha_retry_unlimited,
            captcha_save_samples=captcha_save_samples,
            captcha_icr_enabled=captcha_icr_enabled,
            captcha_icr_rotate_range=captcha_icr_rotate_range,
            captcha_icr_threshold=captcha_icr_threshold,
            captcha_min_similarity=captcha_min_similarity,
            captcha_icr_signin_only=captcha_icr_signin_only,
            request_timeout=request_timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            download_timeout=download_timeout,
            download_max_retries=download_max_retries,
            download_retry_delay=download_retry_delay,
            chrome_low_memory=chrome_low_memory,
            default_renew_cost_7_days=default_renew_cost_7_days,
            timeout=timeout,
            max_delay=max_delay,
            rainyun_user=rainyun_user,
            rainyun_pwd=rainyun_pwd,
            debug=debug,
            linux_mode=linux_mode,
            rainyun_api_key=rainyun_api_key,
            auto_renew=auto_renew,
            renew_threshold_days=renew_threshold_days,
            renew_product_ids=renew_product_ids,
            renew_product_ids_parse_error=renew_product_ids_parse_error,
            chrome_bin=chrome_bin,
            chromedriver_path=chromedriver_path,
            skip_push_title=skip_push_title,
            push_config=push_config,
            notify_channels=notify_channels,
            display_name="",
        )

    @classmethod
    def from_account(cls, account: Any, settings: Any | None = None) -> "Config":
        base = cls.from_env(os.environ)
        auto_renew = base.auto_renew
        renew_threshold_days = base.renew_threshold_days
        timeout = base.timeout
        max_delay = base.max_delay
        debug = base.debug
        request_timeout = base.request_timeout
        max_retries = base.max_retries
        retry_delay = base.retry_delay
        download_timeout = base.download_timeout
        download_max_retries = base.download_max_retries
        download_retry_delay = base.download_retry_delay
        captcha_retry_limit = base.captcha_retry_limit
        captcha_retry_unlimited = base.captcha_retry_unlimited
        captcha_save_samples = base.captcha_save_samples
        captcha_icr_enabled = base.captcha_icr_enabled
        captcha_icr_rotate_range = base.captcha_icr_rotate_range
        captcha_icr_threshold = base.captcha_icr_threshold
        captcha_min_similarity = base.captcha_min_similarity
        captcha_icr_signin_only = base.captcha_icr_signin_only
        skip_push_title = base.skip_push_title
        push_config = DEFAULT_PUSH_CONFIG.copy()
        notify_channels: list[dict[str, Any]] = []

        if settings is not None:
            auto_renew = getattr(settings, "auto_renew", auto_renew)
            renew_threshold_days = getattr(settings, "renew_threshold_days", renew_threshold_days)
            timeout = getattr(settings, "timeout", timeout)
            max_delay = getattr(settings, "max_delay", max_delay)
            debug = getattr(settings, "debug", debug)
            request_timeout = getattr(settings, "request_timeout", request_timeout)
            max_retries = getattr(settings, "max_retries", max_retries)
            retry_delay = getattr(settings, "retry_delay", retry_delay)
            download_timeout = getattr(settings, "download_timeout", download_timeout)
            download_max_retries = getattr(settings, "download_max_retries", download_max_retries)
            download_retry_delay = getattr(settings, "download_retry_delay", download_retry_delay)
            captcha_retry_limit = getattr(settings, "captcha_retry_limit", captcha_retry_limit)
            captcha_retry_unlimited = getattr(
                settings, "captcha_retry_unlimited", captcha_retry_unlimited
            )
            captcha_save_samples = getattr(settings, "captcha_save_samples", captcha_save_samples)
            captcha_icr_enabled = getattr(settings, "captcha_icr_enabled", captcha_icr_enabled)
            captcha_icr_rotate_range = getattr(
                settings, "captcha_icr_rotate_range", captcha_icr_rotate_range
            )
            captcha_icr_threshold = getattr(settings, "captcha_icr_threshold", captcha_icr_threshold)
            captcha_min_similarity = getattr(settings, "captcha_min_similarity", captcha_min_similarity)
            captcha_icr_signin_only = getattr(
                settings, "captcha_icr_signin_only", captcha_icr_signin_only
            )
            skip_push_title = getattr(settings, "skip_push_title", skip_push_title)
            notify_config = getattr(settings, "notify_config", None)
            if isinstance(notify_config, Mapping):
                for key, value in notify_config.items():
                    if isinstance(key, str) and isinstance(value, str):
                        push_config[key] = value
            raw_channels = getattr(settings, "notify_channels", None)
            if isinstance(raw_channels, list):
                notify_channels = [dict(item) for item in raw_channels if isinstance(item, Mapping)]

        account_auto_renew = getattr(account, "auto_renew", True)
        auto_renew = bool(auto_renew) and bool(account_auto_renew)
        renew_product_ids = list(getattr(account, "renew_products", []))
        cookie_file = base.cookie_file
        cookie_dir = os.path.dirname(cookie_file)
        if not cookie_dir:
            cookie_dir = "."
        account_id = getattr(account, "id", "")
        account_key = str(account_id).strip() if account_id is not None else ""
        if not account_key:
            username = str(getattr(account, "username", "") or "").strip()
            name = str(getattr(account, "name", "") or "").strip()
            identity = username or name
            if identity:
                account_key = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:10]
            else:
                account_key = "default"
        cookie_file = os.path.join(cookie_dir, f"cookies_{account_key}.json")
        account_name = str(getattr(account, "name", "") or "").strip()
        account_username = str(getattr(account, "username", "") or "").strip()
        display_name = account_name or account_username or str(account_key)

        return replace(
            base,
            rainyun_user=getattr(account, "username", ""),
            rainyun_pwd=getattr(account, "password", ""),
            rainyun_api_key=getattr(account, "api_key", ""),
            cookie_file=cookie_file,
            auto_renew=auto_renew,
            renew_threshold_days=renew_threshold_days,
            renew_product_ids=renew_product_ids,
            renew_product_ids_parse_error=False,
            timeout=timeout,
            max_delay=max_delay,
            debug=debug,
            request_timeout=request_timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            download_timeout=download_timeout,
            download_max_retries=download_max_retries,
            download_retry_delay=download_retry_delay,
            captcha_retry_limit=captcha_retry_limit,
            captcha_retry_unlimited=captcha_retry_unlimited,
            captcha_save_samples=captcha_save_samples,
            captcha_icr_enabled=captcha_icr_enabled,
            captcha_icr_rotate_range=captcha_icr_rotate_range,
            captcha_icr_threshold=captcha_icr_threshold,
            captcha_min_similarity=captcha_min_similarity,
            captcha_icr_signin_only=captcha_icr_signin_only,
            skip_push_title=skip_push_title,
            push_config=push_config,
            notify_channels=notify_channels,
            display_name=display_name,
        )


@lru_cache(maxsize=1)
def get_default_config() -> Config:
    return Config.from_env()


_DEFAULT_CONFIG = get_default_config()

APP_BASE_URL = _DEFAULT_CONFIG.app_base_url
API_BASE_URL = _DEFAULT_CONFIG.api_base_url
APP_VERSION = _DEFAULT_CONFIG.app_version
COOKIE_FILE = _DEFAULT_CONFIG.cookie_file

POINTS_TO_CNY_RATE = _DEFAULT_CONFIG.points_to_cny_rate
CAPTCHA_RETRY_LIMIT = _DEFAULT_CONFIG.captcha_retry_limit
CAPTCHA_RETRY_UNLIMITED = _DEFAULT_CONFIG.captcha_retry_unlimited

REQUEST_TIMEOUT = _DEFAULT_CONFIG.request_timeout
MAX_RETRIES = _DEFAULT_CONFIG.max_retries
RETRY_DELAY = _DEFAULT_CONFIG.retry_delay

DOWNLOAD_TIMEOUT = _DEFAULT_CONFIG.download_timeout
DOWNLOAD_MAX_RETRIES = _DEFAULT_CONFIG.download_max_retries
DOWNLOAD_RETRY_DELAY = _DEFAULT_CONFIG.download_retry_delay

# Chrome 低内存模式（适用于 1核1G 小鸡）
CHROME_LOW_MEMORY = _DEFAULT_CONFIG.chrome_low_memory

DEFAULT_RENEW_COST_7_DAYS = _DEFAULT_CONFIG.default_renew_cost_7_days
