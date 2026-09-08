from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class Joint:
    name: str
    parent: int | None
    offset: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))
    channels: tuple[str, ...] = ()
    channel_start: int = 0
    is_end_site: bool = False


@dataclass(frozen=True)
class Motion:
    path: Path
    joints: tuple[Joint, ...]
    values: np.ndarray
    frame_time: float

    @property
    def frame_count(self) -> int:
        return int(self.values.shape[0])

    @property
    def fps(self) -> float:
        return 1.0 / self.frame_time

    @property
    def duration_seconds(self) -> float:
        return max(0, self.frame_count - 1) * self.frame_time


def parse_bvh(path: str | Path) -> Motion:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"BVH file does not exist: {source}")

    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    try:
        motion_line = next(i for i, line in enumerate(lines) if line.strip() == "MOTION")
    except StopIteration as error:
        raise ValueError(f"BVH contains no MOTION section: {source}") from error

    joints: list[Joint] = []
    stack: list[int] = []
    end_counts: dict[str, int] = {}
    channel_count = 0

    for raw in lines[:motion_line]:
        line = raw.strip()
        if not line or line in {"HIERARCHY", "{"}:
            continue
        if line.startswith(("ROOT ", "JOINT ")):
            name = line.split(maxsplit=1)[1].strip()
            joints.append(Joint(name=name, parent=stack[-1] if stack else None))
            stack.append(len(joints) - 1)
            continue
        if line == "End Site":
            if not stack:
                raise ValueError(f"End Site has no parent: {source}")
            parent_name = joints[stack[-1]].name
            end_counts[parent_name] = end_counts.get(parent_name, 0) + 1
            joints.append(
                Joint(
                    name=f"{parent_name}_EndSite{end_counts[parent_name]}",
                    parent=stack[-1],
                    is_end_site=True,
                )
            )
            stack.append(len(joints) - 1)
            continue
        if line.startswith("OFFSET "):
            if not stack:
                raise ValueError(f"OFFSET has no joint: {source}")
            joints[stack[-1]].offset = np.asarray(
                [float(value) for value in line.split()[1:4]], dtype=np.float64
            )
            continue
        if line.startswith("CHANNELS "):
            if not stack:
                raise ValueError(f"CHANNELS has no joint: {source}")
            parts = line.split()
            declared = int(parts[1])
            channels = tuple(parts[2 : 2 + declared])
            if len(channels) != declared:
                raise ValueError(f"Malformed channel declaration: {line}")
            joints[stack[-1]].channels = channels
            joints[stack[-1]].channel_start = channel_count
            channel_count += declared
            continue
        if line == "}":
            if not stack:
                raise ValueError(f"Unbalanced closing brace: {source}")
            stack.pop()

    if stack:
        raise ValueError(f"Unclosed BVH hierarchy: {source}")
    if not joints or joints[0].parent is not None:
        raise ValueError(f"Invalid BVH hierarchy: {source}")

    metadata = [line.strip() for line in lines[motion_line + 1 :] if line.strip()]
    if len(metadata) < 3:
        raise ValueError(f"Incomplete BVH MOTION section: {source}")
    frame_match = re.fullmatch(r"Frames:\s*(\d+)", metadata[0])
    time_match = re.fullmatch(r"Frame Time:\s*([0-9.eE+-]+)", metadata[1])
    if frame_match is None or time_match is None:
        raise ValueError(f"Malformed BVH MOTION metadata: {source}")

    frame_count = int(frame_match.group(1))
    frame_time = float(time_match.group(1))
    if frame_count <= 0 or frame_time <= 0:
        raise ValueError(f"Invalid frame count or frame time: {source}")
    flat = np.fromstring(" ".join(metadata[2:]), sep=" ", dtype=np.float64)
    expected = frame_count * channel_count
    if flat.size != expected:
        raise ValueError(f"Expected {expected} values, found {flat.size}: {source}")
    return Motion(source, tuple(joints), flat.reshape(frame_count, channel_count), frame_time)


def _axis_rotation(axis: str, degrees: float) -> np.ndarray:
    radians = math.radians(degrees)
    c, s = math.cos(radians), math.sin(radians)
    if axis == "X":
        return np.asarray(((1, 0, 0), (0, c, -s), (0, s, c)), dtype=np.float64)
    if axis == "Y":
        return np.asarray(((c, 0, s), (0, 1, 0), (-s, 0, c)), dtype=np.float64)
    if axis == "Z":
        return np.asarray(((c, -s, 0), (s, c, 0), (0, 0, 1)), dtype=np.float64)
    raise ValueError(f"Unsupported rotation axis: {axis}")


def forward_kinematics(motion: Motion) -> tuple[np.ndarray, np.ndarray]:
    """Return world positions `(F,J,3)` and rotations `(F,J,3,3)`."""

    frame_count, joint_count = motion.frame_count, len(motion.joints)
    positions = np.empty((frame_count, joint_count, 3), dtype=np.float64)
    rotations = np.empty((frame_count, joint_count, 3, 3), dtype=np.float64)
    world = np.empty((joint_count, 4, 4), dtype=np.float64)

    for frame_index, frame in enumerate(motion.values):
        for joint_index, joint in enumerate(motion.joints):
            translation = joint.offset.astype(np.float64, copy=True)
            rotation = np.eye(3, dtype=np.float64)
            for offset, channel in enumerate(joint.channels):
                value = frame[joint.channel_start + offset]
                lowered = channel.lower()
                axis = channel[0].upper()
                if lowered.endswith("position"):
                    translation["XYZ".index(axis)] += value
                elif lowered.endswith("rotation"):
                    rotation = rotation @ _axis_rotation(axis, value)
                else:
                    raise ValueError(f"Unsupported BVH channel: {channel}")

            local = np.eye(4, dtype=np.float64)
            local[:3, :3] = rotation
            local[:3, 3] = translation
            world[joint_index] = (
                local if joint.parent is None else world[joint.parent] @ local
            )
            positions[frame_index, joint_index] = world[joint_index, :3, 3]
            rotations[frame_index, joint_index] = world[joint_index, :3, :3]
    return positions, rotations
