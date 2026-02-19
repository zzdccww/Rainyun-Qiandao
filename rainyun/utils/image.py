"""Image helper utilities."""

import cv2
import numpy as np


def decode_image_bytes(image_bytes: bytes, label: str) -> np.ndarray:
    if not image_bytes:
        raise ValueError(f"{label} 数据为空，无法解码")
    buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"{label} 解码失败")
    return image


def encode_image_bytes(image: np.ndarray, label: str) -> bytes:
    if image is None or image.size == 0:
        raise ValueError(f"{label} 为空，无法编码")
    success, encoded = cv2.imencode(".jpg", image)
    if not success:
        raise ValueError(f"{label} 编码失败")
    return encoded.tobytes()


def split_sprite_image(sprite: np.ndarray) -> list[np.ndarray]:
    if sprite is None or sprite.size == 0:
        raise ValueError("验证码小图为空，无法切分")
    width = sprite.shape[1]
    if width < 3:
        raise ValueError("验证码小图宽度异常，无法切分")
    step = width // 3
    if step == 0:
        raise ValueError("验证码小图切分宽度为 0")
    return [
        sprite[:, 0:step],
        sprite[:, step:step * 2],
        sprite[:, step * 2:width],
    ]


def normalize_gray(image: np.ndarray) -> np.ndarray:
    if image is None:
        return image
    if len(image.shape) == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
