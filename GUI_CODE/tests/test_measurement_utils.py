import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from measurement_utils import (
    angle_degrees,
    atomic_write_json_with_backup,
    distance_mm,
    distance_raw,
    format_distance_from_mm,
    load_json_with_backup,
    polyline_mm,
    polyline_raw,
    unit_multiplier_from_mm,
)
from managers import ArchiveManager, MeshManager


class TestMeasurementUtils(unittest.TestCase):
    def test_distance(self):
        p1 = [0.0, 0.0, 0.0]
        p2 = [3.0, 4.0, 0.0]
        self.assertAlmostEqual(distance_raw(p1, p2), 5.0, places=8)
        self.assertAlmostEqual(distance_mm(p1, p2, 2.0), 10.0, places=8)

    def test_polyline(self):
        points = [
            [0.0, 0.0, 0.0],
            [3.0, 4.0, 0.0],
            [3.0, 4.0, 12.0],
        ]
        self.assertAlmostEqual(polyline_raw(points), 17.0, places=8)
        self.assertAlmostEqual(polyline_mm(points, 0.5), 8.5, places=8)

    def test_angle(self):
        p1 = [1.0, 0.0, 0.0]
        vertex = [0.0, 0.0, 0.0]
        p3 = [0.0, 1.0, 0.0]
        self.assertAlmostEqual(angle_degrees(p1, vertex, p3), 90.0, places=8)

    def test_units(self):
        self.assertAlmostEqual(unit_multiplier_from_mm("mm"), 1.0)
        self.assertAlmostEqual(unit_multiplier_from_mm("cm"), 0.1)
        self.assertAlmostEqual(unit_multiplier_from_mm("um"), 1000.0)
        self.assertEqual(format_distance_from_mm(10.0, "cm", 2), "1.00 cm")

    def test_atomic_write_and_backup_recovery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = os.path.join(tmpdir, "measurements_index.json")
            first_data = [{"session_id": "abc12345", "distance": "5.00 mm"}]
            second_data = [{"session_id": "def67890", "distance": "12.50 mm"}]

            atomic_write_json_with_backup(index_path, first_data)
            self.assertEqual(load_json_with_backup(index_path), first_data)
            self.assertFalse(os.path.exists(f"{index_path}.tmp"))

            atomic_write_json_with_backup(index_path, second_data)
            self.assertEqual(load_json_with_backup(index_path), second_data)
            self.assertTrue(os.path.exists(f"{index_path}.bak"))

            with open(index_path, "w", encoding="utf-8") as f:
                f.write("{corrupted json")

            recovered = load_json_with_backup(index_path, default=[])
            self.assertEqual(recovered, first_data)

    def test_archive_and_mesh_managers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = ArchiveManager(tmpdir)
            archive.add_measurement({"description": "Wing length", "distance": "4.20 mm"})
            archive.add_screenshot({"description": "Dorsal view", "session_id": archive.measurements[0]["session_id"]})
            self.assertEqual(len(archive.measurements), 1)
            self.assertEqual(len(archive.find_linked_screenshots(archive.measurements[0]["session_id"])), 1)

            mesh_mgr = MeshManager()
            self.assertFalse(mesh_mgr.has_model)
            self.assertEqual(mesh_mgr.insect_name, "Unknown")


if __name__ == "__main__":
    unittest.main()
