from dataclasses import dataclass

from shapely.geometry import Point, Polygon


@dataclass(frozen=True)
class Field:
    width: float = 8.0
    height: float = 18.0
    grid_size: float = 0.5
    start_radius: float = 0.35

    @property
    def bounds(self) -> Polygon:
        return Polygon(
            [
                (0.0, 0.0),
                (self.width, 0.0),
                (self.width, self.height),
                (0.0, self.height),
            ]
        )

    @property
    def bottom_start(self) -> tuple[float, float]:
        return (self.width / 2.0, 0.5)

    @property
    def top_start(self) -> tuple[float, float]:
        return (self.width / 2.0, self.height - 0.5)

    @property
    def start_points(self) -> list[tuple[float, float]]:
        return [self.bottom_start, self.top_start]

    @property
    def start_zones(self) -> list[Point]:
        return [
            Point(self.bottom_start).buffer(self.start_radius),
            Point(self.top_start).buffer(self.start_radius),
        ]

    def contains_polygon(self, polygon: Polygon, margin: float = 0.05) -> bool:
        playable = self.bounds.buffer(-margin)
        return playable.contains(polygon)
