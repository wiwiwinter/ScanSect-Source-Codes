import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from measurement_utils import (
    distance_raw,
    distance_mm,
    polyline_raw,
    polyline_mm,
    angle_degrees,
    format_distance_from_mm,
    unit_multiplier_from_mm,
)


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


if __name__ == "__main__":
    unittest.main()
