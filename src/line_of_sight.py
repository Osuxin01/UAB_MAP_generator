from shapely.geometry import LineString, Point

from .barricade import Barricade


def line_between(a: tuple[float, float], b: tuple[float, float]) -> LineString:
    return LineString([a, b])


def is_blocked(a: tuple[float, float], b: tuple[float, float], barricades: list[Barricade], buffer: float = 0.02) -> bool:
    line = line_between(a, b).buffer(buffer, cap_style="flat")
    return any(line.intersects(barricade.polygon) for barricade in barricades)


def visible(a: tuple[float, float], b: tuple[float, float], barricades: list[Barricade]) -> bool:
    return not is_blocked(a, b, barricades)


def visible_ratio(points_a: list[tuple[float, float]], points_b: list[tuple[float, float]], barricades: list[Barricade]) -> float:
    total = 0
    open_count = 0
    for a in points_a:
        for b in points_b:
            total += 1
            if visible(a, b, barricades):
                open_count += 1
    return open_count / total if total else 0.0


def sample_area(x_values: list[float], y_values: list[float]) -> list[tuple[float, float]]:
    return [(x, y) for x in x_values for y in y_values]


def path_is_clear(start: tuple[float, float], end: tuple[float, float], barricades: list[Barricade], clearance: float = 0.22) -> bool:
    corridor = LineString([start, end]).buffer(clearance, cap_style="round")
    return not any(corridor.intersects(b.polygon) for b in barricades)


def point_blocked(point: tuple[float, float], barricades: list[Barricade], clearance: float = 0.2) -> bool:
    disk = Point(point).buffer(clearance)
    return any(disk.intersects(b.polygon) for b in barricades)
