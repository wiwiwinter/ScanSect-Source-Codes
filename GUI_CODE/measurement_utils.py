import math


def distance_raw(point1, point2):
    return math.sqrt(sum((b - a) ** 2 for a, b in zip(point1, point2)))


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
