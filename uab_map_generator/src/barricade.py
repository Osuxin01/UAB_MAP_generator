from dataclasses import dataclass
from math import cos, sin, sqrt

from shapely.affinity import rotate, translate
from shapely.geometry import LineString, Polygon


SHAPES = ("triangle", "diamond", "trapezoid", "large_triangle")
UNIT_SIDE = 0.9


@dataclass(frozen=True)
class Barricade:
    shape: str
    x: float
    y: float
    angle: float
    polygon: Polygon

    @property
    def center(self) -> tuple[float, float]:
        return (self.x, self.y)


def regular_triangle(side: float) -> Polygon:
    height = side * sqrt(3.0) / 2.0
    points = [(-side / 2.0, -height / 3.0), (side / 2.0, -height / 3.0), (0.0, 2.0 * height / 3.0)]
    return Polygon(points)


def diamond(side: float) -> Polygon:
    height = side * sqrt(3.0) / 2.0
    return centered_polygon(
        Polygon(
            [
                (0.0, 0.0),
                (side, 0.0),
                (side * 1.5, height),
                (side * 0.5, height),
            ]
        )
    )


def trapezoid(short_side: float) -> Polygon:
    top = short_side
    bottom = short_side * 2.0
    height = short_side * sqrt(3.0) / 2.0
    return centered_polygon(
        Polygon(
            [
                (0.0, 0.0),
                (bottom, 0.0),
                ((bottom + top) / 2.0, height),
                ((bottom - top) / 2.0, height),
            ]
        )
    )


def shape_polygon(shape: str) -> Polygon:
    if shape == "triangle":
        return regular_triangle(UNIT_SIDE)
    if shape == "diamond":
        return diamond(UNIT_SIDE)
    if shape == "trapezoid":
        return trapezoid(UNIT_SIDE)
    if shape == "large_triangle":
        return regular_triangle(UNIT_SIDE * 2.0)
    raise ValueError(f"Unknown barricade shape: {shape}")


def create_barricade(shape: str, x: float, y: float, angle: float) -> Barricade:
    base = shape_polygon(shape)
    rotated = rotate(base, angle, origin=(0.0, 0.0), use_radians=False)
    placed = translate(rotated, xoff=x, yoff=y)
    return Barricade(shape=shape, x=x, y=y, angle=angle, polygon=placed)


def seam_lines_for_barricade(barricade: Barricade) -> list[LineString]:
    lines = local_seam_lines(barricade.shape)
    rotated = [rotate(line, barricade.angle, origin=(0.0, 0.0), use_radians=False) for line in lines]
    return [translate(line, xoff=barricade.x, yoff=barricade.y) for line in rotated]


def local_seam_lines(shape: str) -> list[LineString]:
    side = UNIT_SIDE
    height = side * sqrt(3.0) / 2.0
    if shape == "diamond":
        base = Polygon([(0.0, 0.0), (side, 0.0), (side * 1.5, height), (side * 0.5, height)])
        return center_lines([LineString([(side, 0.0), (side * 0.5, height)])], base)
    if shape == "trapezoid":
        base = Polygon([(0.0, 0.0), (side * 2.0, 0.0), (side * 1.5, height), (side * 0.5, height)])
        return center_lines(
            [
                LineString([(side, 0.0), (side * 0.5, height)]),
                LineString([(side, 0.0), (side * 1.5, height)]),
            ],
            base,
        )
    if shape == "large_triangle":
        h2 = side * 2.0 * sqrt(3.0) / 2.0
        return [
            LineString([(-side / 2.0, -h2 / 3.0 + height), (side / 2.0, -h2 / 3.0 + height)]),
            LineString([(0.0, -h2 / 3.0), (-side / 2.0, -h2 / 3.0 + height)]),
            LineString([(0.0, -h2 / 3.0), (side / 2.0, -h2 / 3.0 + height)]),
        ]
    return []


def centered_polygon(polygon: Polygon) -> Polygon:
    centroid = polygon.centroid
    return translate(polygon, xoff=-centroid.x, yoff=-centroid.y)


def center_lines(lines: list[LineString], polygon: Polygon) -> list[LineString]:
    centroid = polygon.centroid
    return [translate(line, xoff=-centroid.x, yoff=-centroid.y) for line in lines]


def random_angle(rng, shape: str | None = None) -> float:
    if shape == "diamond":
        return rng.choice([0, 30, 90, 120, 180, 210, 270, 300])
    return rng.choice([0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330])


def point_on_circle(cx: float, cy: float, radius: float, angle_rad: float) -> tuple[float, float]:
    return (cx + cos(angle_rad) * radius, cy + sin(angle_rad) * radius)
