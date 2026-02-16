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


def preprocess_black_mask(
    image: np.ndarray,
    *,
    threshold: int = 30,
    morph_kernel: int | tuple[int, int] = 2,
    iterations: int = 1,
) -> np.ndarray:
    if image is None or image.size == 0:
        return np.zeros((0, 0), dtype=np.uint8)
    if len(image.shape) == 2:
        mask = cv2.inRange(image, 0, threshold)
    else:
        mask = cv2.inRange(image, (0, 0, 0), (threshold, threshold, threshold))
    if morph_kernel:
        if isinstance(morph_kernel, int):
            kernel = np.ones((morph_kernel, morph_kernel), np.uint8)
        else:
            kernel = np.ones(morph_kernel, np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=max(1, int(iterations)))
    _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    return mask


def _rect_intersection_area(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> int:
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    if x2 <= x1 or y2 <= y1:
        return 0
    return (x2 - x1) * (y2 - y1)


def _rect_area(rect: tuple[int, int, int, int]) -> int:
    return max(0, rect[2] - rect[0]) * max(0, rect[3] - rect[1])


def _merge_rect(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def merge_rectangles(
    rects: list[tuple[int, int, int, int]], *, overlap_threshold: float = 0.0
) -> list[tuple[int, int, int, int]]:
    rects = list(rects)
    if not rects:
        return rects
    merged = True
    while merged:
        merged = False
        result: list[tuple[int, int, int, int]] = []
        while rects:
            current = rects.pop()
            i = 0
            while i < len(rects):
                other = rects[i]
                intersection = _rect_intersection_area(current, other)
                if intersection > 0:
                    min_area = min(_rect_area(current), _rect_area(other))
                    ratio = intersection / min_area if min_area else 0
                    if ratio >= overlap_threshold:
                        current = _merge_rect(current, other)
                        rects.pop(i)
                        merged = True
                        continue
                i += 1
            result.append(current)
        rects = result
    return rects


def _rect_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> int:
    dx = max(0, max(a[0] - b[2], b[0] - a[2]))
    dy = max(0, max(a[1] - b[3], b[1] - a[3]))
    return max(dx, dy)


def merge_close_rectangles(
    rects: list[tuple[int, int, int, int]], *, max_distance: int
) -> list[tuple[int, int, int, int]]:
    rects = list(rects)
    if not rects or max_distance <= 0:
        return rects
    merged = True
    while merged:
        merged = False
        result: list[tuple[int, int, int, int]] = []
        while rects:
            current = rects.pop()
            i = 0
            while i < len(rects):
                other = rects[i]
                if _rect_distance(current, other) <= max_distance:
                    current = _merge_rect(current, other)
                    rects.pop(i)
                    merged = True
                    continue
                i += 1
            result.append(current)
        rects = result
    return rects


def extract_black_regions(
    mask: np.ndarray,
    *,
    min_area: int = 100,
    merged: bool = True,
    merge_distance: int = 0,
) -> list[tuple[int, int, int, int]]:
    if mask is None or mask.size == 0:
        return []
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects: list[tuple[int, int, int, int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w <= 0 or h <= 0:
            continue
        if w * h < min_area:
            continue
        rects.append((x, y, x + w, y + h))
    if not rects or not merged:
        return rects
    rects = merge_rectangles(rects, overlap_threshold=0.0)
    if merge_distance > 0:
        rects = merge_close_rectangles(rects, max_distance=merge_distance)
    return rects


def rotate_image_and_bbox(image: np.ndarray, angle: float, scale: float = 1.0) -> np.ndarray:
    if image is None or image.size == 0:
        return np.zeros((0, 0), dtype=np.uint8)
    height, width = image.shape[:2]
    center = (width / 2, height / 2)
    matrix = cv2.getRotationMatrix2D(center, angle, scale)
    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])
    new_width = int((height * sin) + (width * cos))
    new_height = int((height * cos) + (width * sin))
    matrix[0, 2] += (new_width / 2) - center[0]
    matrix[1, 2] += (new_height / 2) - center[1]
    return cv2.warpAffine(image, matrix, (new_width, new_height), flags=cv2.INTER_NEAREST, borderValue=0)
