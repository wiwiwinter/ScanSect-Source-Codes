import json
import math
import os
import shutil


def distance_raw(point1, point2):
    return math.dist(point1, point2)


def distance_mm(point1, point2, scale_to_mm=1.0):
    return distance_raw(point1, point2) * float(scale_to_mm)


def polyline_raw(points):
    if points is None or len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(points)):
        total += distance_raw(points[i - 1], points[i])
    return total


def polyline_mm(points, scale_to_mm=1.0):
    return polyline_raw(points) * float(scale_to_mm)


def angle_degrees(point1, vertex_point, point3):
    v1 = [a - b for a, b in zip(point1, vertex_point)]
    v2 = [a - b for a, b in zip(point3, vertex_point)]
    n1 = math.sqrt(sum(c * c for c in v1))
    n2 = math.sqrt(sum(c * c for c in v2))
    if n1 <= 1e-12 or n2 <= 1e-12:
        return 0.0

    dot = sum(a * b for a, b in zip(v1, v2))
    cos_theta = max(-1.0, min(1.0, dot / (n1 * n2)))
    return math.degrees(math.acos(cos_theta))


def unit_multiplier_from_mm(unit_name):
    multipliers = {
        "um": 1000.0,
        "mm": 1.0,
        "cm": 0.1,
        "m": 0.001,
    }
    return multipliers.get((unit_name or "mm").lower(), 1.0)


def format_distance_from_mm(value_mm, unit_name="mm", decimals=2):
    converted = float(value_mm) * unit_multiplier_from_mm(unit_name)
    return f"{converted:.{decimals}f} {unit_name}"


def atomic_write_json_with_backup(file_path, data):
    """Write JSON atomically and keep a .bak snapshot of the previous file."""
    directory = os.path.dirname(file_path) or "."
    os.makedirs(directory, exist_ok=True)
    temp_path = f"{file_path}.tmp"
    backup_path = f"{file_path}.bak"

    try:
        if os.path.exists(file_path):
            shutil.copy2(file_path, backup_path)

        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        os.replace(temp_path, file_path)
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        raise


def load_json_with_backup(file_path, default=None):
    """Load JSON from file_path, falling back to file_path.bak if corrupted."""
    if default is None:
        default = []
    for candidate in (file_path, f"{file_path}.bak"):
        if os.path.exists(candidate):
            try:
                with open(candidate, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                continue
    return default
