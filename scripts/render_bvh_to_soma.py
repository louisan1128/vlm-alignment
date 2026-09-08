#!/usr/bin/env python3
"""Render a SeG-style BVH as a front/side SOMA mesh video.

The body uses direct local-rotation transfer. Finger rotations are mapped to
anatomically corresponding SOMA phalanges and calibrated for the two rigs'
different rest-bone directions. No IK is applied.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KIMODO = PROJECT_ROOT / "third_party" / "kimodo"
DEFAULT_BVH_MODULE = PROJECT_ROOT / "src" / "vlm_alignment_v2" / "bvh.py"

BODY_MAP = {
    "Hips": "Hips", "Chest": "Spine1", "Chest2": "Chest",
    "Neck": "Neck1", "Head": "Head",
    "LeftCollar": "LeftShoulder", "LeftShoulder": "LeftArm",
    "LeftElbow": "LeftForeArm", "LeftWrist": "LeftHand",
    "RightCollar": "RightShoulder", "RightShoulder": "RightArm",
    "RightElbow": "RightForeArm", "RightWrist": "RightHand",
    "LeftHip": "LeftLeg", "LeftKnee": "LeftShin",
    "LeftAnkle": "LeftFoot", "LeftToe": "LeftToeBase",
    "RightHip": "RightLeg", "RightKnee": "RightShin",
    "RightAnkle": "RightFoot", "RightToe": "RightToeBase",
}
DIGITS = (("0", "Thumb"), ("1", "Index"), ("2", "Middle"),
          ("3", "Ring"), ("4", "Pinky"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bvh", type=Path)
    parser.add_argument("output", type=Path, help="Output directory")
    parser.add_argument("--kimodo-root", type=Path, default=DEFAULT_KIMODO)
    parser.add_argument("--bvh-module", type=Path, default=DEFAULT_BVH_MODULE)
    parser.add_argument("--target-fps", type=float, default=30.0)
    parser.add_argument("--size", type=int, default=640, help="Pixels per view")
    parser.add_argument("--render-limit", type=int, help="Render first N frames (smoke tests)")
    parser.add_argument("--keep-frames", action="store_true")
    return parser.parse_args()


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("_standalone_soma_bvh", path.resolve())
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load BVH module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def source_local_rotations(module, motion) -> np.ndarray:
    rotations = np.broadcast_to(
        np.eye(3), (motion.frame_count, len(motion.joints), 3, 3)
    ).copy()
    for frame_index, frame in enumerate(motion.values):
        for joint_index, joint in enumerate(motion.joints):
            rotation = np.eye(3)
            for offset, channel in enumerate(joint.channels):
                if channel.lower().endswith("rotation"):
                    rotation = rotation @ module._axis_rotation(
                        channel[0].upper(), frame[joint.channel_start + offset]
                    )
            rotations[frame_index, joint_index] = rotation
    return rotations


def align_vectors(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Return a proper minimal rotation that maps source direction to target."""
    a = source / np.linalg.norm(source)
    b = target / np.linalg.norm(target)
    cosine = float(np.clip(a @ b, -1.0, 1.0))
    if cosine < -1.0 + 1e-8:
        axis = np.cross(a, np.eye(3)[np.argmin(np.abs(a))])
        axis /= np.linalg.norm(axis)
        return 2.0 * np.outer(axis, axis) - np.eye(3)
    vector = np.cross(a, b)
    cross = np.array(((0, -vector[2], vector[1]),
                      (vector[2], 0, -vector[0]),
                      (-vector[1], vector[0], 0)))
    return np.eye(3) + cross + cross @ cross / (1.0 + cosine)


def transfer_fingers(motion, source_local, skeleton, target_local):
    source_index = {joint.name: index for index, joint in enumerate(motion.joints)}
    neutral = skeleton.neutral_joints.cpu().numpy()
    result = target_local.copy()
    applied = {}
    for side in ("Left", "Right"):
        for digit, target_digit in DIGITS:
            source_names = [f"{side}Finger{digit}{suffix}" for suffix in ("", "1", "2")]
            source_chain = [source_index[name] for name in source_names]
            source_end = [
                index for index, joint in enumerate(motion.joints)
                if joint.parent == source_chain[-1] and joint.is_end_site
            ]
            if len(source_end) != 1:
                raise ValueError(f"Expected one fingertip for {source_names[-1]}")
            source_chain.append(source_end[0])

            # SOMA joint 1 is a metacarpal for non-thumb digits. SeG FingerN is
            # the MCP, so it maps to SOMA joint 2 rather than joint 1.
            suffixes = ("1", "2", "3", "End") if target_digit == "Thumb" else ("2", "3", "4", "End")
            target_chain = [
                skeleton.bone_index[f"{side}Hand{target_digit}{suffix}"]
                for suffix in suffixes
            ]
            if target_digit != "Thumb":
                result[:, skeleton.bone_index[f"{side}Hand{target_digit}1"]] = np.eye(3)

            previous_basis = np.eye(3)
            for source_joint, source_child, target_joint, target_child in zip(
                source_chain, source_chain[1:], target_chain, target_chain[1:]
            ):
                source_bone = motion.joints[source_child].offset
                target_bone = neutral[target_child] - neutral[target_joint]
                basis = align_vectors(target_bone, source_bone)
                result[:, target_joint] = (
                    previous_basis.T @ source_local[:, source_joint] @ basis
                )
                applied[motion.joints[source_joint].name] = skeleton.bone_order_names[target_joint]
                previous_basis = basis
    return result, applied


def project(vertices: np.ndarray, view: str):
    if view == "front":
        horizontal, vertical, depth = vertices[:, 0], vertices[:, 1], vertices[:, 2]
    else:
        horizontal, vertical, depth = vertices[:, 2], vertices[:, 1], -vertices[:, 0]
    return np.column_stack((horizontal, vertical)), depth


def draw_mesh(vertices, faces, view, center, scale, size):
    points, depth = project(vertices, view)
    xy = np.empty_like(points)
    xy[:, 0] = (points[:, 0] - center[0]) * scale + size / 2
    xy[:, 1] = size - 30 - (points[:, 1] - center[1]) * scale
    xy = np.rint(xy).astype(np.int32)
    image = Image.new("RGB", (size, size), (247, 247, 247))
    draw = ImageDraw.Draw(image)

    triangles = vertices[faces]
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-8)
    light = np.asarray((0.25, 0.45, 0.86))
    intensity = 0.55 + 0.38 * np.abs(normals @ light)
    colors = np.clip(np.asarray((190, 145, 92))[None] * intensity[:, None], 45, 235).astype(np.uint8)
    for face_index in np.argsort(depth[faces].mean(axis=1)):
        polygon = xy[faces[face_index]]
        if np.any(polygon < -20) or np.any(polygon > size + 20):
            continue
        draw.polygon([tuple(map(int, point)) for point in polygon], fill=tuple(map(int, colors[face_index])))
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    draw.text((18, 10), view.upper(), fill=(35, 35, 35), font=font)
    return image


def main() -> None:
    args = parse_args()
    sys.path.insert(0, str(args.kimodo_root.resolve()))
    from kimodo.skeleton import SOMASkeleton77
    from kimodo.viz.soma_skin import SOMASkin

    module = load_module(args.bvh_module)
    motion = module.parse_bvh(args.bvh)
    source_positions, _ = module.forward_kinematics(motion)
    source_local = source_local_rotations(module, motion)
    step = max(1, int(round(motion.fps / args.target_fps)))
    frame_indices = np.arange(0, motion.frame_count, step, dtype=np.int64)
    if args.render_limit is not None:
        frame_indices = frame_indices[:args.render_limit]
    source_positions = source_positions[frame_indices]
    source_local = source_local[frame_indices]

    skeleton = SOMASkeleton77()
    skin = SOMASkin(skeleton)
    target_local = np.broadcast_to(
        np.eye(3, dtype=np.float32),
        (len(frame_indices), skeleton.nbjoints, 3, 3),
    ).copy()
    source_index = {joint.name: index for index, joint in enumerate(motion.joints)}
    applied = {}
    for source_name, target_name in BODY_MAP.items():
        if source_name in source_index and target_name in skeleton.bone_index:
            target_local[:, skeleton.bone_index[target_name]] = source_local[:, source_index[source_name]]
            applied[source_name] = target_name
    target_local, finger_map = transfer_fingers(motion, source_local, skeleton, target_local)
    applied.update(finger_map)

    source_root = source_positions[:, source_index["Hips"]]
    source_height = float(np.ptp(source_positions[0, :, 1]))
    target_y = skeleton.neutral_joints[:, 1]
    scale_to_soma = float((target_y.max() - target_y.min()).item()) / source_height
    root_positions = ((source_root - source_root[:1]) * scale_to_soma).astype(np.float32)
    root_positions[:, 1] -= float(target_y.min().item())
    with torch.no_grad():
        rotations, joints, _ = skeleton.fk(
            torch.from_numpy(target_local), torch.from_numpy(root_positions)
        )
        vertices = skin.skin(rotations, joints, rot_is_global=True).cpu().numpy()
    faces = skin.faces.cpu().numpy()

    args.output.mkdir(parents=True, exist_ok=True)
    frame_dir = args.output / "frames"
    frame_dir.mkdir(exist_ok=True)
    projected = {
        view: np.concatenate([project(frame, view)[0] for frame in vertices])
        for view in ("front", "side")
    }
    vertical_min = min(points[:, 1].min() for points in projected.values())
    vertical_max = max(points[:, 1].max() for points in projected.values())
    horizontal_extent = max(np.ptp(points[:, 0]) for points in projected.values())
    render_scale = (args.size - 70) / max(vertical_max - vertical_min, horizontal_extent, 1e-6)
    for frame_index, frame in enumerate(vertices):
        views = []
        for view in ("front", "side"):
            points = projected[view]
            center = np.asarray(((points[:, 0].min() + points[:, 0].max()) / 2, vertical_min))
            views.append(draw_mesh(frame, faces, view, center, render_scale, args.size))
        combined = Image.new("RGB", (args.size * 2, args.size), (247, 247, 247))
        combined.paste(views[0], (0, 0))
        combined.paste(views[1], (args.size, 0))
        combined.save(frame_dir / f"frame_{frame_index:05d}.png")

    video = args.output / "soma_front_side.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-framerate", f"{args.target_fps:g}",
        "-i", str(frame_dir / "frame_%05d.png"), "-c:v", "libx264",
        "-pix_fmt", "yuv420p", "-crf", "20", str(video),
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    metadata = {
        "source_bvh": str(args.bvh.resolve()),
        "video": str(video.resolve()),
        "source_fps": motion.fps,
        "target_fps": args.target_fps,
        "rendered_frames": len(frame_indices),
        "method": "Body local rotations plus anatomical, rest-bone-calibrated finger rotations; no IK",
        "mapping": applied,
    }
    (args.output / "render_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    if not args.keep_frames:
        for path in frame_dir.glob("frame_*.png"):
            path.unlink()
        frame_dir.rmdir()
    print(video)


if __name__ == "__main__":
    main()
