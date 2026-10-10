# Copyright (c) 2026 Luiz Otávio Miranda
"""Portable layout normalization for old and new tmux servers."""

import json
import unittest

from tmux.scripts.lazy import normalize_layout


class LayoutTests(unittest.TestCase):
  def test_legacy_layouts_are_unchanged(self):
    for layout in ("", "c27f,123x36,0,0,2", "b263,80x24,0,0,6"):
      self.assertEqual(normalize_layout(layout), layout)

  def test_json_leaf_uses_legacy_checksum_and_pane_id(self):
    layout = {
      "V": 2,
      "L": {"t": "p", "w": 123, "h": 36, "x": 0, "y": 0, "a": True, "i": 1, "I": "%2"},
    }
    self.assertEqual(normalize_layout(json.dumps(layout)), "c27f,123x36,0,0,2")

  def test_nested_splits_preserve_geometry_and_order(self):
    layout = {
      "V": 2,
      "L": {
        "t": "h",
        "w": 120,
        "h": 40,
        "x": 0,
        "y": 0,
        "c": [
          {
            "t": "v",
            "w": 60,
            "h": 40,
            "x": 0,
            "y": 0,
            "c": [
              {"t": "p", "w": 60, "h": 20, "x": 0, "y": 0, "I": "%0"},
              {"t": "p", "w": 60, "h": 19, "x": 0, "y": 21, "I": "%2"},
            ],
          },
          {"t": "p", "w": 59, "h": 40, "x": 61, "y": 0, "I": "%1"},
        ],
      },
    }
    self.assertEqual(
      normalize_layout(json.dumps(layout)).split(",", 1)[1],
      "120x40,0,0{60x40,0,0[60x20,0,0,0,60x19,0,21,2],59x40,61,0,1}",
    )

  def test_invalid_or_nonportable_layouts_fail_closed(self):
    leaf = {"t": "p", "w": 80, "h": 24, "x": 0, "y": 0, "I": "%6"}
    for layout in (
      None,
      "invalid",
      "{",
      "[]",
      '{"V":3}',
      json.dumps({"V": 2, "L": leaf, "F": [leaf]}),
      json.dumps({"V": 2, "L": {**leaf, "w": -1}}),
      json.dumps({"V": 2, "L": {**leaf, "I": "bad"}}),
      json.dumps({"V": 2, "L": {**leaf, "t": "h", "c": []}}),
    ):
      with self.subTest(layout=layout), self.assertRaises(ValueError):
        normalize_layout(layout)
