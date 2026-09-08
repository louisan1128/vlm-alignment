from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .models import PairPaths, SampledFrame


VIEW_SIZE = 640
TARGET_BODY_HEIGHT = 512.0
TARGET_FOOT_Y = 592.0
G1_NEUTRAL_BODY_HEIGHT = 342.0
G1_CENTER_X = 320.0
G1_FOOT_Y = 632.0
G1_BACKGROUND = (79, 83, 89)


def video_info(path: Path) -> tuple[int, float, int, int]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {path}")
    try:
        return (
            int(capture.get(cv2.CAP_PROP_FRAME_COUNT)),
            float(capture.get(cv2.CAP_PROP_FPS)),
            int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
    finally:
        capture.release()


def read_frame(capture: cv2.VideoCapture, index: int) -> np.ndarray:
    capture.set(cv2.CAP_PROP_POS_FRAMES, int(index))
    ok, frame = capture.read()
    if not ok:
        raise RuntimeError(f"Could not read video frame {index}")
    return frame


def transform_view(
    view: np.ndarray,
    *,
    scale: float,
    center_x: float,
    foot_y: float,
    background: tuple[int, int, int],
) -> np.ndarray:
    matrix = np.float32(
        [[scale, 0, VIEW_SIZE / 2 - scale * center_x], [0, scale, TARGET_FOOT_Y - scale * foot_y]]
    )
    return cv2.warpAffine(
        view,
        matrix,
        (VIEW_SIZE, VIEW_SIZE),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=background,
    )


def soma_calibration(first_combined: np.ndarray) -> tuple[list[dict[str, float]], float]:
    if first_combined.shape[1] != VIEW_SIZE * 2:
        raise ValueError(f"Expected 1280 px SOMA composite, got {first_combined.shape[1]} px")
    values: list[dict[str, float]] = []
    for view in (first_combined[:, :VIEW_SIZE], first_combined[:, VIEW_SIZE:]):
        hsv = cv2.cvtColor(view, cv2.COLOR_BGR2HSV)
        ys, xs = np.where((hsv[:, :, 1] > 60) & (hsv[:, :, 2] > 30))
        if not len(xs):
            raise ValueError("Could not detect the SOMA silhouette for sequence calibration")
        values.append(
            {
                "center_x": float((xs.min() + xs.max()) / 2),
                "foot_y": float(ys.max()),
                "height": float(ys.max() - ys.min()),
            }
        )
    return values, TARGET_BODY_HEIGHT / max(item["height"] for item in values)


def normalize_soma(view: np.ndarray, calibration: dict[str, float], scale: float) -> np.ndarray:
    background = tuple(int(value) for value in view[-1, -1])
    cleaned = view.copy()
    cleaned[:32] = background
    return transform_view(
        cleaned,
        scale=scale,
        center_x=calibration["center_x"],
        foot_y=calibration["foot_y"],
        background=background,
    )


def normalize_g1(view: np.ndarray) -> np.ndarray:
    if view.shape[:2] != (720, 640):
        raise ValueError(f"Expected 640x720 G1 input, got {view.shape[1]}x{view.shape[0]}")
    return transform_view(
        view,
        scale=TARGET_BODY_HEIGHT / G1_NEUTRAL_BODY_HEIGHT,
        center_x=G1_CENTER_X,
        foot_y=G1_FOOT_Y,
        background=G1_BACKGROUND,
    )


def uniform_indices(start: int, end: int, count: int) -> np.ndarray:
    if count < 2:
        raise ValueError("sample count must be at least 2")
    if end < start:
        raise ValueError(f"Invalid action window: {start}..{end}")
    return np.rint(np.linspace(start, end, count)).astype(np.int64)


def action_window(pair: PairPaths, frame_count: int, embodiment: str) -> tuple[int, int]:
    metadata = json.loads(pair.action_phase.read_text(encoding="utf-8"))
    if embodiment == "g1":
        window = metadata["same_normalized_window_on_g1"]
        start, end = int(window["start_frame"]), int(window["end_frame"])
    elif embodiment == "soma":
        window = metadata["action_window_from_source_bvh"]
        start = int(round(float(window["start_phase"]) * (frame_count - 1)))
        end = int(round(float(window["end_phase"]) * (frame_count - 1)))
    else:
        raise ValueError(f"Unknown embodiment: {embodiment}")
    return max(0, start), min(frame_count - 1, end)


def save_composite(front: np.ndarray, side: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(
        str(path), np.concatenate((front, side), axis=1), [cv2.IMWRITE_JPEG_QUALITY, 94]
    ):
        raise RuntimeError(f"Could not write sampled frame: {path}")


def make_contact_sheet(frames: list[SampledFrame], path: Path) -> None:
    columns, cell_width, image_height, label_height = 3, 640, 320, 30
    rows = (len(frames) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_width, rows * (image_height + label_height)), "white")
    draw = ImageDraw.Draw(sheet)
    for offset, frame in enumerate(frames):
        with Image.open(frame.path) as source:
            image = source.convert("RGB")
            image.thumbnail((cell_width, image_height), Image.Resampling.LANCZOS)
        x = (offset % columns) * cell_width
        y = (offset // columns) * (image_height + label_height)
        sheet.paste(image, (x + (cell_width - image.width) // 2, y))
        draw.text(
            (x + 8, y + image_height + 6),
            f"{frame.order:02d}/{len(frames)} | action phase={frame.window_phase:.3f}",
            fill=(20, 20, 20),
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=92)


def sample_soma(video: Path, pair: PairPaths, count: int, output: Path) -> list[SampledFrame]:
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open SOMA video: {video}")
    try:
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        first = read_frame(capture, 0)
        calibrations, scale = soma_calibration(first)
        start, end = action_window(pair, frame_count, "soma")
        indices = uniform_indices(start, end, count)
        frames: list[SampledFrame] = []
        for order, index in enumerate(indices, start=1):
            frame = read_frame(capture, int(index))
            front = normalize_soma(frame[:, :VIEW_SIZE], calibrations[0], scale)
            side = normalize_soma(frame[:, VIEW_SIZE:], calibrations[1], scale)
            path = output / f"frame_{order:02d}_idx_{index:05d}.jpg"
            save_composite(front, side, path)
            frames.append(SampledFrame(order, int(index), (int(index) - start) / max(1, end - start), path))
    finally:
        capture.release()
    make_contact_sheet(frames, output / "contact_sheet.jpg")
    return frames


def sample_g1(pair: PairPaths, count: int, output: Path) -> list[SampledFrame]:
    front_capture = cv2.VideoCapture(str(pair.g1_front))
    side_capture = cv2.VideoCapture(str(pair.g1_side))
    if not front_capture.isOpened() or not side_capture.isOpened():
        raise RuntimeError(f"Could not open both G1 views for {pair.name}")
    try:
        front_count = int(front_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        side_count = int(side_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        usable_count = min(front_count, side_count)
        start, end = action_window(pair, usable_count, "g1")
        indices = uniform_indices(start, end, count)
        frames: list[SampledFrame] = []
        for order, index in enumerate(indices, start=1):
            front = normalize_g1(read_frame(front_capture, int(index)))
            side = normalize_g1(read_frame(side_capture, int(index)))
            path = output / f"frame_{order:02d}_idx_{index:05d}.jpg"
            save_composite(front, side, path)
            frames.append(SampledFrame(order, int(index), (int(index) - start) / max(1, end - start), path))
    finally:
        front_capture.release()
        side_capture.release()
    make_contact_sheet(frames, output / "contact_sheet.jpg")
    return frames
