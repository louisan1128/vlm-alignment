from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from vlm_alignment_v2.framing import action_window, uniform_indices
from vlm_alignment_v2.models import PairPaths


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STEERING = PROJECT_ROOT / "data" / "g1_pairs" / "0316_HANDS_STEERING-1"


class FramingTests(unittest.TestCase):
    def test_pair_is_portable_and_complete(self) -> None:
        pair = PairPaths.from_directory(STEERING)
        self.assertEqual(pair.name, "0316_HANDS_STEERING-1")
        self.assertTrue(pair.source_bvh.is_file())
        self.assertFalse(pair.source_bvh.is_symlink())

    def test_action_window_maps_to_rendered_source_and_g1(self) -> None:
        pair = PairPaths.from_directory(STEERING)
        self.assertEqual(action_window(pair, 119, "soma"), (4, 99))
        self.assertEqual(action_window(pair, 119, "g1"), (4, 99))

    def test_uniform_sampling_includes_window_boundaries(self) -> None:
        indices = uniform_indices(4, 99, 12)
        np.testing.assert_array_equal(
            indices,
            np.asarray([4, 13, 21, 30, 39, 47, 56, 64, 73, 82, 90, 99]),
        )


if __name__ == "__main__":
    unittest.main()
